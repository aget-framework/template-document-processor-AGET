# Document Processor API Specification v1.0

**Version:** 1.0
**Date:** 2025-10-26
**Status:** Draft for Review
**Purpose:** Formal API contracts for all document processing modules

---

## 1. Design Principles

### 1.1 Naming Conventions

**General Rules:**
- Method names use `snake_case`
- Class names use `PascalCase`
- Constants and enums use `UPPER_CASE` or `PascalCase` (for Enum)
- Private methods prefix with `_`

**Parameter Naming Standards:**
- Size parameters: Use `_bytes` suffix (e.g., `max_bytes`, `size_bytes`)
  - ❌ `max_size_mb`, `size` (ambiguous units)
  - ✅ `max_bytes`, `size_bytes` (explicit units)
- Format parameters: Use `_extensions` or `_mimetypes` suffix
  - ❌ `allowed_formats` (ambiguous - extensions or MIME types?)
  - ✅ `allowed_extensions`, `allowed_mimetypes` (explicit)
- Collection parameters: Use plural nouns (e.g., `documents`, `filters`, `publishers`)
- ID parameters: Use `_id` suffix (e.g., `document_id`, `version_id`, `batch_id`)

**Return Type Conventions:**
- Status methods: Return typed objects (e.g., `ValidationResult`, `PublishResult`, not `bool` or `Dict`)
- Mutation methods: Return the mutated object or operation result
- Query methods: Return typed data structures (dataclasses preferred over dicts)

### 1.2 Method Signature Patterns

**Initialization:**
```python
def __init__(self, required_config: str, optional_param: Optional[Type] = None)
```
- Required configuration first
- Optional parameters with defaults
- Use `Optional[Type]` for nullable parameters

**Processing Methods:**
```python
def process_X(
    self,
    primary_input: Type,
    metadata: Optional[Dict] = None
) -> ResultType:
```
- Primary input first
- `metadata` parameter last if needed
- Return typed result objects

**Validation Methods:**
```python
def validate(self, target: Type) -> ValidationResult:
```
- Return `ValidationResult` with `is_valid: bool` and `errors: List[str]`
- Never return raw `bool` (loses error information)

### 1.3 Data Structure Standards

**Result Objects:**
All operation results should be dataclasses with:
- `success: bool` - Whether operation succeeded
- Context-specific data fields
- `error_message: Optional[str]` - Error details if failed

**Progress Objects:**
All progress tracking should include:
- `total: int` - Total items to process
- `completed: int` - Items completed
- `failed: int` - Items failed
- `progress_percent: float` - Calculated percentage

**Version Objects:**
All versioning should include:
- `version_id: str` - Unique identifier
- `timestamp: str` - ISO format timestamp
- `content_hash: str` - Hash for integrity verification

---

## 2. Module API Specifications

### 2.1 Ingestion Modules

#### 2.1.1 QueueManager (`src/ingestion/queue_manager.py`)

**Purpose:** Manage document processing queues with state transitions

**Initialization:**
```python
def __init__(self, queue_file: str = '.aget/queue_state.json')
```

**Core Methods:**
```python
def add_candidate(
    self,
    document_id: str,
    path: str,
    size_bytes: int,
    metadata: Optional[Dict] = None
) -> DocumentQueueItem
```
- Adds document to candidate queue
- Returns queue item with state `QueueState.CANDIDATE`

```python
def mark_pending(self, document_id: str) -> DocumentQueueItem
```
- Transitions document to pending state
- Returns updated queue item

```python
def mark_processed(
    self,
    document_id: str,
    result: Optional[Dict] = None  # ✅ ADDED: Result parameter for processed state
) -> DocumentQueueItem
```
- Transitions document to processed state
- Stores processing result
- Returns updated queue item

```python
def mark_failed(
    self,
    document_id: str,
    error_message: str  # ✅ ADDED: Error message required
) -> DocumentQueueItem
```
- Transitions document to failed state
- Records error for debugging
- Returns updated queue item

**Data Structures:**
```python
@dataclass
class DocumentQueueItem:
    document_id: str
    path: str
    state: QueueState  # Not "status" - use "state" for consistency
    size_bytes: int    # Not "size" - explicit units
    added_timestamp: float
    processed_timestamp: Optional[float] = None
    result: Optional[Dict] = None  # ✅ ADDED
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None

class QueueState(Enum):
    CANDIDATE = "candidate"
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"
```

**Design Decisions:**
- ✅ Use `state` not `status` (queue items have states, not statuses)
- ✅ `mark_processed()` takes optional `result` parameter
- ✅ `mark_failed()` requires `error_message` (failure always has reason)

---

#### 2.1.2 DocumentValidator (`src/ingestion/validator.py`)

**Purpose:** Validate documents before processing

**Initialization:**
```python
def __init__(self, rules: Optional[List[ValidationRule]] = None)
```

**Core Methods:**
```python
def add_rule(self, rule: ValidationRule) -> None
```

```python
def validate(self, document_path: str) -> ValidationResult
```

**Validation Rules:**
```python
class FileSizeValidator(ValidationRule):
    def __init__(
        self,
        max_bytes: int,  # ✅ Explicit units
        warn_bytes: Optional[int] = None
    )
```

```python
class FileFormatValidator(ValidationRule):
    def __init__(
        self,
        allowed_extensions: List[str],  # ✅ CHANGED from allowed_formats
        allowed_mimetypes: Optional[List[str]] = None
    )
```

**Data Structures:**
```python
@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]
```

**Design Decisions:**
- ✅ Changed `allowed_formats` → `allowed_extensions` (explicit meaning)
- ✅ Added `allowed_mimetypes` for dual validation
- ✅ Return `ValidationResult` object, not bare `bool`

---

#### 2.1.3 BatchProcessor (`src/ingestion/batch_processor.py`)

**Purpose:** Process multiple documents with progress tracking

**Initialization:**
```python
def __init__(
    self,
    batch_id: str,
    dry_run: bool = False,
    stop_on_failure: bool = False
)
```

**Core Methods:**
```python
def process_batch(
    self,
    documents: List[str],
    processor_func: Callable[[str], Dict],
    on_progress: Optional[Callable[[BatchProgress], None]] = None
) -> BatchProgress
```

**Data Structures:**
```python
@dataclass
class BatchProgress:
    batch_id: str
    total: int
    completed: int  # ✅ CONSISTENT naming across all progress objects
    failed: int
    errors: List[Dict]

    @property
    def progress_percent(self) -> float:
        return (self.completed / self.total * 100) if self.total > 0 else 0.0
```

**Design Decisions:**
- ✅ Use `completed` not `succeeded` or `processed` (consistency)
- ✅ `progress_percent` is computed property (not stored)
- ✅ `batch_id` required (enables tracking multiple concurrent batches)

---

### 2.2 Processing Modules

#### 2.2.1 LLM Provider (`src/processing/llm_provider.py`)

**Purpose:** Abstract LLM provider interfaces

**Factory Pattern:**
```python
class LLMProviderFactory:
    @staticmethod
    def create(
        provider: LLMProvider,  # Enum
        api_key: Optional[str] = None,
        **kwargs
    ) -> BaseLLMProvider
```

**Provider Implementation:**
```python
class BaseLLMProvider:
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.config = kwargs  # Store all config for introspection

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key, **kwargs)
        self.model = kwargs.get('model', 'gpt-4o')  # ✅ ADDED: Direct model attribute

    def call(self, request: LLMRequest) -> LLMResponse:
        # ✅ CHANGED: Accept LLMRequest object, not string
```

**Data Structures:**
```python
@dataclass
class LLMRequest:
    prompt: str
    model: Optional[str] = None  # Override provider default
    temperature: float = 0.0
    max_tokens: int = 1000
    metadata: Optional[Dict] = None

@dataclass
class LLMResponse:
    content: str
    model: str
    usage: Dict[str, int]  # {input_tokens, output_tokens}
    latency_ms: float
    cost_usd: float
```

**Design Decisions:**
- ✅ Providers store `model` as direct attribute (not buried in config)
- ✅ `call()` takes `LLMRequest` object (structured, extensible)
- ✅ Return `LLMResponse` with usage and cost (observability)

---

#### 2.2.2 ModelRouter (`src/processing/model_router.py`)

**Purpose:** Route documents to appropriate models

**Initialization:**
```python
def __init__(
    self,
    primary_strategy: BaseRouter,
    fallback_chain: Optional[List[str]] = None,
    max_cost_per_doc: float = 0.5
)
```

**Router Implementations:**
```python
class StaticRouter(BaseRouter):
    def __init__(
        self,
        default_model: str,  # ✅ ADDED: Required default model
        default_provider: str,  # ✅ ADDED: Required default provider
        routing_rules: Optional[Dict] = None
    )
```

**Core Methods:**
```python
def route(
    self,
    document: str,
    metadata: Optional[Dict] = None
) -> RoutingDecision
```

**Data Structures:**
```python
@dataclass
class RoutingDecision:
    model: str
    provider: str
    estimated_cost: float
    reasoning: str  # Why this model was selected
```

**Design Decisions:**
- ✅ `StaticRouter` requires `default_model` and `default_provider` (fail-fast)
- ✅ `RoutingDecision` includes `reasoning` (explainability)
- ✅ Routing is deterministic given same input (reproducibility)

---

#### 2.2.3 SchemaValidator (`src/processing/schema_validator.py`)

**Purpose:** Validate LLM outputs against schemas

**Initialization:**
```python
def __init__(
    self,
    schema: Schema,
    strict_mode: bool = True
)
```

**Schema Definition:**
```python
class Schema:
    def __init__(self, fields: Optional[Dict[str, SchemaField]] = None):
        self.fields = fields or {}

    def add_field(
        self,
        name: str,
        field_type: FieldType,  # ✅ ADDED: Enum for type safety
        required: bool = False,
        description: Optional[str] = None
    ) -> None
```

**Field Types:**
```python
class FieldType(Enum):  # ✅ ADDED: Type enum for consistency
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
```

**Core Methods:**
```python
def validate(self, data: Dict[str, Any]) -> ValidationResult
```

**Design Decisions:**
- ✅ Added `FieldType` enum (was missing, caused smoke test failure)
- ✅ `Schema.add_field()` method for fluent API (was missing)
- ✅ Validate returns `ValidationResult` with detailed errors

---

#### 2.2.4 RetryHandler (`src/processing/retry_handler.py`)

**Purpose:** Handle retries with exponential backoff

**Configuration:**
```python
@dataclass
class RetryConfig:
    max_attempts: int = 3  # ✅ ADDED: Individual fields instead of object
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
```

**Initialization:**
```python
def __init__(self, config: Optional[RetryConfig] = None):
    self.config = config or RetryConfig()
```

**Core Methods:**
```python
def retry(
    self,
    func: Callable,
    error_classifier: Optional[Callable[[Exception], bool]] = None
) -> RetryResult
```

**Data Structures:**
```python
@dataclass
class RetryResult:
    success: bool
    result: Any
    attempts: int
    total_delay: float
    error_message: Optional[str] = None
```

**Design Decisions:**
- ✅ `RetryConfig` is dataclass with individual fields (not nested dict)
- ✅ Optional `error_classifier` function (classify retryable vs non-retryable)
- ✅ Return `RetryResult` with attempt count and timing (observability)

---

#### 2.2.5 CacheManager (`src/processing/cache_manager.py`)

**Purpose:** Cache LLM responses for idempotence

**Initialization:**
```python
def __init__(
    self,
    cache_dir: str = '.aget/cache',
    ttl_seconds: Optional[int] = None
)
```

**Core Methods:**
```python
def get_cache_key(
    self,
    prompt: str,
    model: str,
    temperature: float = 0.0,
    max_tokens: int = 1000,
    seed: Optional[int] = None
) -> str
```
- Returns SHA-256 hash of deterministic cache key

```python
def set(
    self,
    prompt: str,
    model: str,
    response: str,
    temperature: float = 0.0,
    max_tokens: int = 1000,
    seed: Optional[int] = None,
    metadata: Optional[Dict] = None
) -> str
```
- Stores response with cache key
- Returns cache key

```python
def get(
    self,
    prompt: str,  # ✅ CHANGED: Accept prompt+model, not cache_key
    model: str,
    temperature: float = 0.0,
    max_tokens: int = 1000,
    seed: Optional[int] = None
) -> Optional[str]
```
- Retrieves cached response
- Returns None if cache miss

**Design Decisions:**
- ✅ `get()` takes `prompt` + `model` parameters (not pre-computed cache_key)
  - Rationale: Consistent API with `set()`, user doesn't need to compute key
- ✅ Cache key includes all parameters affecting output (temperature, max_tokens, seed)
- ✅ SHA-256 for cache keys (collision-resistant, deterministic)

---

### 2.3 Output Modules

#### 2.3.1 Publisher (`src/output/publisher.py`)

**Purpose:** Publish processed documents to destinations

**Initialization:**
```python
def __init__(self, publishers: Optional[List[BasePublisher]] = None)
```

**Destination Implementations:**
```python
class FilesystemPublisher(BasePublisher):
    def __init__(
        self,
        output_dir: str,
        format: str = 'json'
    )
```

**Core Methods:**
```python
def publish(
    self,
    document_id: str,
    content: Any,
    metadata: Optional[Dict] = None
) -> List[PublishResult]
```
- Returns result for each registered publisher

**Data Structures:**
```python
@dataclass
class PublishResult:
    destination: str
    success: bool
    location: Optional[str] = None  # Where published
    error_message: Optional[str] = None
```

**Design Decisions:**
- ✅ Multi-destination support (list of publishers)
- ✅ `publish()` returns list of results (one per destination)
- ✅ `PublishResult` includes `location` (for verification)

---

#### 2.3.2 VersionManager (`src/output/version_manager.py`)

**Purpose:** Track document versions with content hashing

**Initialization:**
```python
def __init__(self, versions_dir: str = '.aget/versions')
```

**Core Methods:**
```python
def create_version(
    self,
    document_id: str,
    content: Any,
    processing_metadata: Dict,
    parent_version_id: Optional[str] = None
) -> DocumentVersion
```

**Data Structures:**
```python
@dataclass
class DocumentVersion:
    version_id: str
    document_id: str
    number: int  # ✅ ADDED: Sequential version number
    content: Any
    timestamp: str
    processing_metadata: Dict
    content_hash: str
    parent_version_id: Optional[str] = None
```

**Design Decisions:**
- ✅ Added `number` field (sequential version number for humans)
- ✅ `content_hash` for integrity verification
- ✅ `parent_version_id` for version graph (rollback path)

---

#### 2.3.3 RollbackManager (`src/output/rollback_manager.py`)

**Purpose:** Rollback documents to previous versions

**Initialization:**
```python
def __init__(
    self,
    version_manager: VersionManager,
    publisher: Publisher
)
```

**Core Methods:**
```python
def rollback_document(
    self,
    document_id: str,
    target_version_id: Optional[str] = None,
    reason: RollbackReason = RollbackReason.USER_REQUESTED,
    dry_run: bool = False
) -> RollbackRecord
```

**Data Structures:**
```python
class RollbackReason(Enum):
    USER_REQUESTED = "user_requested"
    VALIDATION_FAILED = "validation_failed"
    PROCESSING_ERROR = "processing_error"

@dataclass
class RollbackRecord:
    document_id: str
    from_version_id: str
    to_version_id: str
    reason: RollbackReason
    timestamp: str
    success: bool
    error_message: Optional[str] = None
```

**Design Decisions:**
- ✅ Rollback creates new version (doesn't delete current)
- ✅ `RollbackReason` enum for categorization
- ✅ `dry_run` mode for preview (doesn't commit)

---

### 2.4 Security Modules

#### 2.4.1 InputSanitizer (`src/security/input_sanitizer.py`)

**Purpose:** Prevent prompt injection attacks

**Core Methods:**
```python
def wrap_with_delimiters(
    self,
    user_content: str,
    delimiter: str = 'USER_CONTENT'
) -> str
```

**Prompt Builder:**
```python
class PromptBuilder:
    def build_extraction_prompt(
        self,
        document: str,
        extraction_schema: Dict  # ✅ ADDED: Required schema parameter
    ) -> str

    def build_classification_prompt(
        self,
        document: str,
        categories: List[str]  # ✅ ADDED: Required categories parameter
    ) -> str

    def build_summarization_prompt(
        self,
        document: str,
        max_length: Optional[int] = None
    ) -> str
```

**Design Decisions:**
- ✅ `build_extraction_prompt()` requires `extraction_schema` (was missing)
- ✅ `build_classification_prompt()` requires `categories` (was missing)
- ✅ All methods return sanitized prompts with delimiter wrapping

---

#### 2.4.2 ContentFilter (`src/security/content_filter.py`)

**Purpose:** Filter sensitive content from outputs

**Initialization:**
```python
class ContentFilterPipeline:
    def __init__(self, filters: Optional[List[BaseContentFilter]] = None)
```

**Core Methods:**
```python
def scan_and_redact(
    self,
    text: str
) -> Tuple[str, List[FilterMatch]]
```
- Returns (redacted_text, matches)
- Preserves original text structure

**Filter Implementations:**
```python
class PIIFilter(BaseContentFilter):
    def __init__(
        self,
        patterns: Optional[Dict[str, str]] = None,  # ✅ Custom patterns
        redaction_format: str = "[REDACTED:{type}]"
    )
```

**Design Decisions:**
- ✅ Pipeline pattern for composable filters
- ✅ Returns both redacted text and match details (auditability)
- ✅ Configurable redaction format

---

#### 2.4.3 ResourceLimiter (`src/security/resource_limiter.py`)

**Purpose:** Enforce resource consumption limits

**Initialization:**
```python
def __init__(
    self,
    max_tokens: Optional[int] = None,
    max_time_seconds: Optional[float] = None,
    max_api_calls: Optional[int] = None,
    max_cost_usd: Optional[float] = None
)
```

**Core Methods:**
```python
def check_token_limit(self, token_count: int) -> None
def check_time_limit(self, elapsed_seconds: float) -> None
def check_api_call_limit(self, call_count: int) -> None
def check_cost_limit(self, cost_usd: float) -> None
```
- Raise `ResourceLimitExceeded` if limit exceeded
- All checks are fail-fast

**Design Decisions:**
- ✅ Individual check methods (not combined)
- ✅ Raise exceptions (fail-fast, not silent)
- ✅ All limits optional (flexibility)

---

### 2.5 Pipeline Modules

#### 2.5.1 PipelineRunner (`src/pipeline/pipeline_runner.py`)

**Purpose:** Orchestrate multi-stage processing pipelines

**Initialization:**
```python
def __init__(self)
```

**Core Methods:**
```python
def add_stage(
    self,
    name: str,
    processor: Callable,
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL,
    depends_on: Optional[List[str]] = None
) -> 'PipelineRunner'
```
- Returns self for fluent API

```python
def run(
    self,
    input_data: Any,
    mode: ExecutionMode = ExecutionMode.SEQUENTIAL
) -> Dict[str, StageResult]
```
- Returns results keyed by stage name

**Data Structures:**
```python
class ExecutionMode(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    MIXED = "mixed"

@dataclass
class StageResult:
    stage_name: str
    success: bool
    output: Any
    error_message: Optional[str] = None
    duration_seconds: float
```

**Design Decisions:**
- ✅ Fluent API for stage addition (method chaining)
- ✅ `depends_on` for stage dependencies
- ✅ `StageResult` includes timing (observability)

---

## 3. Cross-Cutting Patterns

### 3.1 Error Handling

**Standard Exception Hierarchy:**
```python
class DocumentProcessorError(Exception):
    """Base exception for all document processor errors"""

class ValidationError(DocumentProcessorError):
    """Validation failures"""

class ProcessingError(DocumentProcessorError):
    """Processing failures"""

class ResourceLimitExceeded(DocumentProcessorError):
    """Resource limit violations"""
```

**Error Return Pattern:**
All result objects should include optional `error_message`:
```python
@dataclass
class SomeResult:
    success: bool
    # ... other fields
    error_message: Optional[str] = None
```

### 3.2 Metadata Convention

All processing methods should accept optional `metadata: Optional[Dict] = None`:
- Enables passing context through pipeline
- Never required (always optional)
- Always last parameter (convention)

### 3.3 Progress Tracking

All progress objects must include:
```python
@dataclass
class Progress:
    total: int
    completed: int  # Consistent naming
    failed: int

    @property
    def progress_percent(self) -> float:
        return (self.completed / self.total * 100) if self.total > 0 else 0.0
```

### 3.4 Timestamps

All timestamps use ISO 8601 format:
```python
from datetime import datetime
timestamp = datetime.utcnow().isoformat() + 'Z'
```

---

## 4. Migration Impact

### 4.1 Breaking Changes

**Gate 2A Modules:**

1. **QueueManager**
   - ✅ ADD: `mark_processed()` takes optional `result` parameter
   - ✅ ADD: `mark_failed()` requires `error_message` parameter
   - ✅ CHANGE: `DocumentQueueItem.state` (was `status`)

2. **DocumentValidator**
   - ✅ CHANGE: `FileFormatValidator.__init__()` parameter `allowed_extensions` (was `allowed_formats`)

3. **BatchProcessor**
   - ✅ CHANGE: `BatchProgress.completed` (was implementation-specific)

4. **LLMProvider**
   - ✅ ADD: `BaseLLMProvider.model` attribute
   - ✅ CHANGE: `call()` takes `LLMRequest` object (was string)

5. **ModelRouter**
   - ✅ CHANGE: `StaticRouter.__init__()` requires `default_model` and `default_provider`

6. **SchemaValidator**
   - ✅ ADD: `FieldType` enum
   - ✅ ADD: `Schema.add_field()` method

7. **RetryHandler**
   - ✅ CHANGE: `RetryConfig` is dataclass with individual fields

8. **CacheManager**
   - ✅ CHANGE: `get()` takes `prompt` and `model` (not cache_key)

**Gate 2B Modules:**

9. **VersionManager**
   - ✅ ADD: `DocumentVersion.number` field

10. **InputSanitizer**
    - ✅ CHANGE: `PromptBuilder.build_extraction_prompt()` requires `extraction_schema`
    - ✅ CHANGE: `PromptBuilder.build_classification_prompt()` requires `categories`

**Gate 2C Modules:**
- ✅ No breaking changes (all tests passed)

### 4.2 Smoke Test Impact

**Expected after refactoring:**
- Gate 2A: 0/8 → 8/8 passing (100%)
- Gate 2B: 3/7 → 7/7 passing (100%)
- Gate 2C: 5/5 → 5/5 passing (100%)
- **Total: 8/20 → 20/20 passing (100%)**

---

## 5. Implementation Checklist

**For each module being refactored:**

- [ ] Update method signatures per specification
- [ ] Add missing fields to data structures
- [ ] Update type hints to match specification
- [ ] Ensure consistent parameter naming
- [ ] Add/update docstrings with new signatures
- [ ] Update any internal calls to modified methods
- [ ] Verify module still imports correctly

**After all refactoring:**

- [ ] Run smoke tests: `python3 tests/smoke_test.py`
- [ ] Verify 95%+ pass rate
- [ ] Update module documentation
- [ ] Update examples in README

---

## 6. Rationale

**Why these specifications?**

1. **Consistency:** Similar operations use similar signatures across modules
2. **Explicitness:** Parameter names indicate units and types (e.g., `size_bytes`)
3. **Observability:** Result objects include timing, costs, and reasoning
4. **Extensibility:** Optional `metadata` parameters enable future enhancement
5. **Type Safety:** Enums for categorical values, dataclasses for structured data
6. **Debuggability:** All failures include error messages and context

**Based on:**
- L208 patterns (lines 230-250, 260-300, etc.)
- Industry best practices (PEP 8, typing conventions)
- Template usability (users will instantiate and customize)

---

**End of API Specification v1.0**
