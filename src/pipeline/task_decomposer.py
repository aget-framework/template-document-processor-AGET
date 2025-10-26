"""Task Decomposition for Large Documents

Breaks complex documents into hierarchical subtasks for:
- Parallel processing
- Better resource management
- Error isolation
- Progress tracking

Based on L208 lines 649-798 (Task Decomposition Patterns)
"""

from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import hashlib


class ChunkingStrategy(Enum):
    """Document chunking strategies"""
    FIXED_SIZE = "fixed_size"           # Split by character/word/token count
    SEMANTIC = "semantic"               # Split by logical boundaries (paragraphs, sections)
    CONTEXT_AWARE = "context_aware"     # Split with overlap for context preservation


@dataclass
class DocumentTask:
    """Represents a task in the processing hierarchy

    Based on L208 lines 668-687 (Hierarchical Task Model)
    """
    task_id: str
    document_id: str
    content: Any
    parent_task_id: Optional[str] = None
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Optional[Any] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None

    @property
    def is_leaf(self) -> bool:
        """Check if this is a leaf task (no children)

        Returns:
            True if leaf task
        """
        return self.metadata and self.metadata.get('is_leaf', True)


class TaskDecomposer:
    """Decomposes large documents into manageable subtasks

    Supports three chunking strategies (based on L208 lines 730-772):
    1. Fixed-Size: Split by count (simple, may break mid-concept)
    2. Semantic: Split by logical boundaries (preserves meaning)
    3. Context-Aware: Split with overlap (maintains context at boundaries)

    Design Decision: Parent/child hierarchy enables recursive decomposition.
    Tasks can spawn children which may spawn their own children.

    Based on L208 lines 649-798 (Task Decomposition Patterns)
    """

    def __init__(
        self,
        chunking_strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC,
        chunk_size: int = 2000,
        overlap: int = 200
    ):
        """Initialize task decomposer

        Args:
            chunking_strategy: Strategy for splitting documents
            chunk_size: Target chunk size (tokens, words, or characters)
            overlap: Overlap size for context-aware chunking
        """
        self.chunking_strategy = chunking_strategy
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.tasks: Dict[str, DocumentTask] = {}

    def decompose(
        self,
        document_id: str,
        content: str,
        threshold: Optional[int] = None
    ) -> List[DocumentTask]:
        """Decompose document into subtasks if needed

        Based on L208 lines 1088-1096 (Decision Framework)

        Args:
            document_id: Document identifier
            content: Document content
            threshold: Size threshold for decomposition (uses chunk_size if None)

        Returns:
            List of tasks (single task if no decomposition needed)
        """
        threshold = threshold or self.chunk_size
        content_size = len(content.split())  # Word count

        if content_size <= threshold:
            # No decomposition needed
            task = self._create_task(document_id, content, is_leaf=True)
            return [task]

        # Decompose based on strategy
        if self.chunking_strategy == ChunkingStrategy.FIXED_SIZE:
            chunks = self._fixed_size_chunking(content)
        elif self.chunking_strategy == ChunkingStrategy.SEMANTIC:
            chunks = self._semantic_chunking(content)
        else:  # CONTEXT_AWARE
            chunks = self._context_aware_chunking(content)

        # Create parent task
        parent_task = self._create_task(
            document_id,
            content,
            is_leaf=False,
            metadata={'total_chunks': len(chunks)}
        )

        # Create child tasks
        child_tasks = []
        for i, chunk in enumerate(chunks):
            child_task = self._create_task(
                f"{document_id}_chunk_{i}",
                chunk,
                parent_task_id=parent_task.task_id,
                is_leaf=True,
                metadata={'chunk_index': i, 'total_chunks': len(chunks)}
            )
            child_tasks.append(child_task)

        return [parent_task] + child_tasks

    def aggregate_results(
        self,
        parent_task_id: str,
        child_results: List[Any],
        aggregation_strategy: str = "concatenate"
    ) -> Any:
        """Aggregate child task results into parent result

        Based on L208 lines 805-808 (Result Aggregation)

        Args:
            parent_task_id: Parent task identifier
            child_results: List of results from child tasks
            aggregation_strategy: How to combine results
                                 (concatenate, voting, weighted_average)

        Returns:
            Aggregated result
        """
        if aggregation_strategy == "concatenate":
            # Simple concatenation
            return " ".join(str(r) for r in child_results)

        elif aggregation_strategy == "voting":
            # Majority vote (for classification tasks)
            from collections import Counter
            votes = Counter(child_results)
            return votes.most_common(1)[0][0] if votes else None

        elif aggregation_strategy == "weighted_average":
            # Weighted average (for numeric results)
            if not child_results:
                return 0.0
            return sum(child_results) / len(child_results)

        else:
            # Default: return list of results
            return child_results

    def _create_task(
        self,
        document_id: str,
        content: Any,
        parent_task_id: Optional[str] = None,
        is_leaf: bool = True,
        metadata: Optional[Dict] = None
    ) -> DocumentTask:
        """Create a document task

        Args:
            document_id: Document identifier
            content: Task content
            parent_task_id: Parent task ID if this is a child
            is_leaf: Whether this is a leaf task
            metadata: Additional metadata

        Returns:
            Created DocumentTask
        """
        task_id = self._generate_task_id(document_id, parent_task_id)

        metadata = metadata or {}
        metadata['is_leaf'] = is_leaf

        task = DocumentTask(
            task_id=task_id,
            document_id=document_id,
            content=content,
            parent_task_id=parent_task_id,
            metadata=metadata
        )

        self.tasks[task_id] = task
        return task

    def _generate_task_id(self, document_id: str, parent_id: Optional[str]) -> str:
        """Generate unique task ID

        Args:
            document_id: Document identifier
            parent_id: Parent task ID if applicable

        Returns:
            Unique task ID
        """
        unique_str = f"{document_id}_{parent_id or 'root'}_{len(self.tasks)}"
        hash_suffix = hashlib.sha256(unique_str.encode()).hexdigest()[:8]
        return f"task_{hash_suffix}"

    def _fixed_size_chunking(self, content: str) -> List[str]:
        """Split content by fixed size

        Based on L208 lines 730-734 (Fixed-Size Chunking)

        Args:
            content: Content to chunk

        Returns:
            List of chunks
        """
        words = content.split()
        chunks = []

        for i in range(0, len(words), self.chunk_size):
            chunk = " ".join(words[i:i + self.chunk_size])
            chunks.append(chunk)

        return chunks

    def _semantic_chunking(self, content: str) -> List[str]:
        """Split content by semantic boundaries

        Based on L208 lines 736-739 (Semantic Chunking)

        Args:
            content: Content to chunk

        Returns:
            List of chunks
        """
        # Split by paragraphs (double newline)
        paragraphs = content.split('\n\n')

        chunks = []
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para.split())

            if current_size + para_size > self.chunk_size and current_chunk:
                # Start new chunk
                chunks.append("\n\n".join(current_chunk))
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size

        # Add remaining chunk
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks

    def _context_aware_chunking(self, content: str) -> List[str]:
        """Split content with overlap for context preservation

        Based on L208 lines 741-772 (Context-Aware Chunking)

        Args:
            content: Content to chunk

        Returns:
            List of chunks with overlap
        """
        words = content.split()
        chunks = []

        for i in range(0, len(words), self.chunk_size - self.overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk = " ".join(chunk_words)
            chunks.append(chunk)

            # Stop if we've covered all content
            if i + self.chunk_size >= len(words):
                break

        return chunks


class RecursiveTaskProcessor:
    """Processes tasks recursively with automatic decomposition

    Based on L208 lines 774-798 (Recursive Task Hierarchies)
    """

    def __init__(
        self,
        decomposer: TaskDecomposer,
        processor_func: Callable,
        max_depth: int = 3
    ):
        """Initialize recursive processor

        Args:
            decomposer: TaskDecomposer instance
            processor_func: Function to process leaf tasks
            max_depth: Maximum recursion depth
        """
        self.decomposer = decomposer
        self.processor_func = processor_func
        self.max_depth = max_depth

    def process(
        self,
        document_id: str,
        content: str,
        depth: int = 0
    ) -> Any:
        """Process document recursively

        Pattern from L208 lines 780-789:
        ```
        if is_leaf():
            return process_directly()
        else:
            children = decompose()
            child_results = [child.process() for child in children]
            return aggregate(child_results)
        ```

        Args:
            document_id: Document identifier
            content: Document content
            depth: Current recursion depth

        Returns:
            Processed result
        """
        # Base case: max depth reached or content small enough
        if depth >= self.max_depth or len(content.split()) <= self.decomposer.chunk_size:
            return self.processor_func(content)

        # Recursive case: decompose and recurse
        tasks = self.decomposer.decompose(document_id, content)

        if len(tasks) == 1:
            # No decomposition occurred, process directly
            return self.processor_func(content)

        # Process child tasks recursively
        parent_task = tasks[0]
        child_tasks = tasks[1:]

        child_results = []
        for child_task in child_tasks:
            result = self.process(
                child_task.task_id,
                child_task.content,
                depth + 1
            )
            child_results.append(result)

        # Aggregate results
        return self.decomposer.aggregate_results(
            parent_task.task_id,
            child_results
        )
