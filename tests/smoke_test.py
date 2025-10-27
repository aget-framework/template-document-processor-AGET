"""Smoke Tests for Document Processor Modules

Validates basic functionality of all 20 implemented modules:
- Gate 2A: Core pipeline infrastructure (8 modules)
- Gate 2B: Output & security modules (7 modules)
- Gate 2C: Orchestration & Wikitext (5 modules)

Tests verify:
- Module imports succeed
- Main classes instantiate
- Basic operations complete without exceptions
- No obvious integration issues
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tempfile
from datetime import datetime


def test_gate_2a_ingestion_queue_manager():
    """Test queue_manager.py: Basic queue operations"""
    from ingestion.queue_manager import QueueManager, DocumentQueueItem, QueueState

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        queue_file = f.name

    qm = QueueManager(queue_file=queue_file)

    # Add candidate (correct API: document_id, path, size_bytes)
    item = qm.add_candidate("test_doc.pdf", "/path/to/test_doc.pdf", 1024)
    assert item.document_id == "test_doc.pdf"
    assert item.state == QueueState.CANDIDATE

    # Mark pending
    qm.mark_pending("test_doc.pdf")
    assert qm.items["test_doc.pdf"].state == QueueState.PENDING

    # Mark processed
    qm.mark_processed("test_doc.pdf", {"extracted": "data"})
    assert qm.items["test_doc.pdf"].state == QueueState.PROCESSED

    print("✅ queue_manager.py: Basic operations successful")


def test_gate_2a_ingestion_validator():
    """Test validator.py: Document validation"""
    from ingestion.validator import DocumentValidator, FileSizeValidator, FileFormatValidator

    # Create validator with empty rules list (no defaults)
    validator = DocumentValidator(rules=[])
    # Correct API: max_bytes (not max_size_mb)
    validator.add_rule(FileSizeValidator(max_bytes=10 * 1024 * 1024))  # 10 MB
    # Correct API: allowed_extensions (not allowed_formats)
    validator.add_rule(FileFormatValidator(allowed_extensions=['.pdf', '.docx']))

    # Validator instantiates successfully with 2 rules
    assert len(validator.rules) == 2

    print("✅ validator.py: Validator creation successful")


def test_gate_2a_ingestion_batch_processor():
    """Test batch_processor.py: Batch processing"""
    from ingestion.batch_processor import BatchProcessor

    # Correct API: batch_id required
    processor = BatchProcessor(batch_id="test_batch_001")

    # Simple processing function
    def mock_processor(doc):
        return {"doc": doc, "processed": True}

    # Process batch
    docs = ["doc1", "doc2", "doc3"]
    progress = processor.process_batch(docs, mock_processor)

    assert progress.total == 3
    assert progress.completed == 3
    assert progress.failed == 0

    print("✅ batch_processor.py: Batch processing successful")


def test_gate_2a_processing_llm_provider():
    """Test llm_provider.py: LLM provider factory"""
    from processing.llm_provider import LLMProviderFactory, LLMProvider, LLMRequest

    # Create OpenAI provider (stubbed)
    provider = LLMProviderFactory.create(
        LLMProvider.OPENAI,
        api_key="test_key",
        model="gpt-4"
    )

    assert provider is not None
    # Provider has direct model attribute per API spec
    assert provider.model == "gpt-4"

    # Test stubbed completion with LLMRequest
    request = LLMRequest(prompt="Test prompt", model="gpt-4")
    response = provider.call(request)
    assert response is not None
    assert response.model == "gpt-4"

    print("✅ llm_provider.py: Provider instantiation successful")


def test_gate_2a_processing_model_router():
    """Test model_router.py: Routing decisions"""
    from processing.model_router import ModelRouter, StaticRouter

    # Correct API: StaticRouter requires default_model and default_provider
    static_router = StaticRouter(default_model="gpt-4", default_provider="openai")
    router = ModelRouter(primary_strategy=static_router)

    # Test routing decision
    decision = router.route("Sample document content")
    assert decision.model is not None
    assert decision.provider is not None

    print("✅ model_router.py: Routing successful")


def test_gate_2a_processing_schema_validator():
    """Test schema_validator.py: Output validation"""
    from processing.schema_validator import SchemaValidator, Schema, FieldType

    # Correct API: Schema is a class, not dict
    schema = Schema()
    schema.add_field("title", FieldType.STRING, required=True)
    schema.add_field("content", FieldType.STRING, required=False)

    validator = SchemaValidator(schema)

    # Valid output
    result = validator.validate({"title": "Test", "content": "Sample"})
    assert result.is_valid

    print("✅ schema_validator.py: Validation successful")


def test_gate_2a_processing_retry_handler():
    """Test retry_handler.py: Retry logic"""
    from processing.retry_handler import RetryHandler, RetryConfig

    # Correct API: Takes RetryConfig object
    config = RetryConfig(max_attempts=3, base_delay=0.1)
    handler = RetryHandler(config)

    # Test successful retry
    call_count = [0]
    def mock_func():
        call_count[0] += 1
        if call_count[0] < 2:
            raise Exception("Temporary failure")
        return "success"

    result = handler.retry(mock_func)
    assert result.success
    assert result.result == "success"
    assert result.attempts == 2

    print("✅ retry_handler.py: Retry logic successful")


def test_gate_2a_processing_cache_manager():
    """Test cache_manager.py: Caching and checkpointing"""
    from processing.cache_manager import CacheManager, CheckpointManager

    with tempfile.TemporaryDirectory() as tmpdir:
        cache = CacheManager(cache_dir=tmpdir)

        # Test cache key generation
        key = cache.get_cache_key("prompt", "model")
        assert len(key) == 64  # SHA-256 hex digest

        # Test cache operations (parameter-based API: pass prompt, model directly)
        cache.set("prompt text", "gpt-4", "response text")
        cached = cache.get("prompt text", "gpt-4")  # Parameter-based, not cache_key-based
        assert cached is not None
        assert cached == "response text"

        # Test checkpoint manager
        checkpoint_file = f"{tmpdir}/processing.json"
        checkpoint_mgr = CheckpointManager(checkpoint_file=checkpoint_file)
        checkpoint_mgr.mark_complete("doc1")
        assert checkpoint_mgr.is_complete("doc1")
        assert checkpoint_mgr.get_completed_count() == 1

        print("✅ cache_manager.py: Caching and checkpointing successful")


def test_gate_2b_output_publisher():
    """Test publisher.py: Publishing to destinations"""
    from output.publisher import Publisher, FilesystemPublisher

    with tempfile.TemporaryDirectory() as tmpdir:
        fs_publisher = FilesystemPublisher(output_dir=tmpdir)
        # Correct API: Pass list of publishers to __init__
        publisher = Publisher(publishers=[fs_publisher])

        # Test publication
        results = publisher.publish("doc1", "content", {"timestamp": "2025-10-26"})
        assert len(results) == 1
        assert results[0].success

        print("✅ publisher.py: Publishing successful")


def test_gate_2b_output_version_manager():
    """Test version_manager.py: Version tracking"""
    from output.version_manager import VersionManager

    with tempfile.TemporaryDirectory() as tmpdir:
        vm = VersionManager(versions_dir=tmpdir)

        # Create version
        version = vm.create_version(
            "doc1",
            "content v1",
            {"model": "gpt-4"},
            "Initial version"
        )

        # Version object uses 'number', not 'version_number'
        assert version.number == 1
        assert version.document_id == "doc1"

        print("✅ version_manager.py: Version tracking successful")


def test_gate_2b_output_rollback_manager():
    """Test rollback_manager.py: Rollback operations"""
    from output.rollback_manager import RollbackManager, RollbackReason
    from output.version_manager import VersionManager
    from output.publisher import Publisher

    with tempfile.TemporaryDirectory() as tmpdir:
        vm = VersionManager(versions_dir=tmpdir)
        pub = Publisher()  # Empty publisher for testing
        # Correct API: Requires both version_manager and publisher
        rm = RollbackManager(version_manager=vm, publisher=pub)

        # Create versions
        v1 = vm.create_version("doc1", "content v1", {}, "v1")
        v2 = vm.create_version("doc1", "content v2", {}, "v2")

        # Test rollback (dry_run=True to avoid re-publishing in test)
        rollback = rm.rollback_document(
            "doc1",
            target_version_id=v1.version_id,
            reason=RollbackReason.USER_REQUESTED,  # Use enum, not string
            dry_run=True
        )
        assert rollback.success

        print("✅ rollback_manager.py: Rollback successful")


def test_gate_2b_security_input_sanitizer():
    """Test input_sanitizer.py: Prompt injection prevention"""
    from security.input_sanitizer import InputSanitizer, PromptBuilder

    sanitizer = InputSanitizer()

    # Test delimiter wrapping
    wrapped = sanitizer.wrap_with_delimiters("User content here")
    assert "<USER_CONTENT>" in wrapped
    assert "</USER_CONTENT>" in wrapped

    # Test prompt builder (uses template methods, not add_system)
    builder = PromptBuilder()
    prompt = builder.build_extraction_prompt("Extract data from this document")

    assert prompt is not None

    print("✅ input_sanitizer.py: Sanitization successful")


def test_gate_2b_security_content_filter():
    """Test content_filter.py: Content filtering"""
    from security.content_filter import PIIFilter, CredentialFilter, ContentFilterPipeline

    pipeline = ContentFilterPipeline()
    pipeline.add_filter(PIIFilter())
    pipeline.add_filter(CredentialFilter())

    # Test PII detection
    text = "My email is test@example.com and SSN is 123-45-6789"
    filtered, matches = pipeline.scan_and_redact(text)

    assert len(matches) > 0
    assert "[REDACTED:" in filtered

    print("✅ content_filter.py: Filtering successful")


def test_gate_2b_security_resource_limiter():
    """Test resource_limiter.py: Resource limiting"""
    from security.resource_limiter import ResourceLimiter, ResourceLimitExceeded

    limiter = ResourceLimiter(
        max_tokens=1000,
        max_time_seconds=10,
        max_api_calls=5,
        max_cost_usd=1.0
    )

    # Test token limit check (should pass)
    limiter.check_token_limit(500)

    # Test exceeded limit
    try:
        limiter.check_token_limit(2000)
        assert False, "Should have raised ResourceLimitExceeded"
    except ResourceLimitExceeded:
        pass

    print("✅ resource_limiter.py: Resource limiting successful")


def test_gate_2b_pipeline_pipeline_runner():
    """Test pipeline_runner.py: Pipeline execution"""
    from pipeline.pipeline_runner import PipelineRunner, ExecutionMode

    runner = PipelineRunner()

    # Add simple stages (API: add_stage takes name and processor)
    def stage1(data):
        return {"stage1": True, **data}

    def stage2(data):
        return {"stage2": True, **data}

    runner.add_stage(
        name="stage1",
        processor=stage1
    )

    runner.add_stage(
        name="stage2",
        processor=stage2
    )

    # Run pipeline
    results = runner.run({"input": "data"}, mode=ExecutionMode.SEQUENTIAL)

    assert results["stage1"].success
    assert results["stage2"].success

    print("✅ pipeline_runner.py: Pipeline execution successful")


def test_gate_2c_pipeline_task_decomposer():
    """Test task_decomposer.py: Task decomposition"""
    from pipeline.task_decomposer import TaskDecomposer, ChunkingStrategy

    decomposer = TaskDecomposer(
        chunking_strategy=ChunkingStrategy.SEMANTIC,
        chunk_size=100
    )

    # Small document (no decomposition)
    small_doc = "Short content"
    tasks = decomposer.decompose("doc1", small_doc)
    assert len(tasks) == 1

    # Large document (should decompose)
    large_doc = " ".join(["word"] * 200)
    tasks = decomposer.decompose("doc2", large_doc)
    assert len(tasks) > 1  # Parent + children

    print("✅ task_decomposer.py: Task decomposition successful")


def test_gate_2c_pipeline_status_tracker():
    """Test status_tracker.py: Progress tracking"""
    from pipeline.status_tracker import StatusTracker, TaskStatus

    tracker = StatusTracker()

    # Create and track task
    task = tracker.create_task("task1", total_items=10)
    assert task.status == TaskStatus.PENDING

    tracker.start_task("task1")
    assert tracker.get_task_status("task1").status == TaskStatus.IN_PROGRESS

    tracker.update_progress("task1", items_completed=5)
    assert tracker.get_task_status("task1").progress_percent == 50.0

    tracker.complete_task("task1")
    assert tracker.get_task_status("task1").status == TaskStatus.COMPLETED

    print("✅ status_tracker.py: Status tracking successful")


def test_gate_2c_pipeline_metrics_collector():
    """Test metrics_collector.py: Metrics collection"""
    from pipeline.metrics_collector import MetricsCollector

    collector = MetricsCollector(monthly_budget=300.0)

    # Record metrics
    collector.record_extraction(success=True)
    collector.record_validation(passed=True)
    collector.record_llm_call(
        input_tokens=100,
        output_tokens=50,
        cost_usd=0.01,
        latency_ms=500
    )

    # Get summary
    summary = collector.get_summary()
    assert summary['accuracy']['total_processed'] == 1
    assert summary['cost']['total_spent'] == 0.01

    print("✅ metrics_collector.py: Metrics collection successful")


def test_gate_2c_wikitext_parser():
    """Test wikitext_parser.py: Wikitext parsing"""
    from wikitext.wikitext_parser import WikitextParser, GMRKBParser

    parser = WikitextParser()

    sample_wikitext = """
== Section 1 ==
This is content with [[Internal Link]] and [http://example.com External].

{{Template|param1=value1}}

[[Category:Test]]
"""

    result = parser.parse(sample_wikitext)

    assert len(result['sections']) > 0
    assert len(result['links']) > 0
    assert len(result['templates']) > 0
    assert len(result['categories']) > 0

    # Test GM-RKB parser
    gmrkb_parser = GMRKBParser()
    entity = gmrkb_parser.parse_research_entity(sample_wikitext)
    assert 'type' in entity

    print("✅ wikitext_parser.py: Wikitext parsing successful")


def test_gate_2c_mediawiki_integration():
    """Test mediawiki_integration.py: MediaWiki API client"""
    from wikitext.mediawiki_integration import MediaWikiAPI, GMRKBClient

    # Test base API client (stubbed)
    api = MediaWikiAPI(api_url="https://wiki.example.com/api.php")
    page = api.get_page("Test Page")

    assert page is not None
    assert page.title == "Test Page"

    # Test GM-RKB client
    gmrkb = GMRKBClient(api_url="https://wiki.example.com/api.php")
    entity = gmrkb.get_research_entity("Test Entity")

    assert entity is not None

    print("✅ mediawiki_integration.py: MediaWiki integration successful")


def run_all_tests():
    """Run all smoke tests"""
    tests = [
        # Gate 2A (8 modules)
        ("queue_manager", test_gate_2a_ingestion_queue_manager),
        ("validator", test_gate_2a_ingestion_validator),
        ("batch_processor", test_gate_2a_ingestion_batch_processor),
        ("llm_provider", test_gate_2a_processing_llm_provider),
        ("model_router", test_gate_2a_processing_model_router),
        ("schema_validator", test_gate_2a_processing_schema_validator),
        ("retry_handler", test_gate_2a_processing_retry_handler),
        ("cache_manager", test_gate_2a_processing_cache_manager),

        # Gate 2B (7 modules)
        ("publisher", test_gate_2b_output_publisher),
        ("version_manager", test_gate_2b_output_version_manager),
        ("rollback_manager", test_gate_2b_output_rollback_manager),
        ("input_sanitizer", test_gate_2b_security_input_sanitizer),
        ("content_filter", test_gate_2b_security_content_filter),
        ("resource_limiter", test_gate_2b_security_resource_limiter),
        ("pipeline_runner", test_gate_2b_pipeline_pipeline_runner),

        # Gate 2C (5 modules)
        ("task_decomposer", test_gate_2c_pipeline_task_decomposer),
        ("status_tracker", test_gate_2c_pipeline_status_tracker),
        ("metrics_collector", test_gate_2c_pipeline_metrics_collector),
        ("wikitext_parser", test_gate_2c_wikitext_parser),
        ("mediawiki_integration", test_gate_2c_mediawiki_integration),
    ]

    print("=" * 70)
    print("Gate 2.5: Smoke Testing - 20 Modules")
    print("=" * 70)
    print()

    passed = 0
    failed = 0
    errors = []

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            failed += 1
            errors.append((name, str(e)))
            print(f"❌ {name}: FAILED - {e}")

    print()
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed (out of {len(tests)} total)")
    print("=" * 70)

    if errors:
        print()
        print("Failed Tests:")
        for name, error in errors:
            print(f"  - {name}: {error}")

    return passed, failed, errors


if __name__ == "__main__":
    passed, failed, errors = run_all_tests()
    sys.exit(0 if failed == 0 else 1)
