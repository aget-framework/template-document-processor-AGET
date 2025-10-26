"""Pipeline Orchestration

Coordinates document processing through sequential, parallel, or mixed execution patterns.

Based on L208 lines 689-726 (Orchestration Patterns)
"""

from typing import List, Dict, Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum
import time


class ExecutionMode(Enum):
    """Pipeline execution modes"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    MIXED = "mixed"


@dataclass
class PipelineStage:
    """Represents a stage in the processing pipeline"""
    name: str
    processor: Callable
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    depends_on: Optional[List[str]] = None


@dataclass
class StageResult:
    """Result of executing a pipeline stage"""
    stage_name: str
    success: bool
    result_data: Any = None
    error_message: Optional[str] = None
    execution_time: float = 0.0


class PipelineRunner:
    """Orchestrates multi-stage document processing pipelines

    Supports three execution patterns (based on L208 lines 691-706):
    1. Sequential: Tasks complete in order (Task1 → Task2 → Task3)
    2. Parallel: Tasks run concurrently (spawn all → wait all → aggregate)
    3. Mixed: Hybrid orchestration (parallel → sequential → parallel)

    Design Decision: Synchronous execution for template simplicity.
    Production should use asyncio for true parallelism.

    Based on L208 lines 689-726 (Orchestration Patterns)
    """

    def __init__(self):
        """Initialize pipeline runner"""
        self.stages: List[PipelineStage] = []

    def add_stage(
        self,
        name: str,
        processor: Callable,
        execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL,
        depends_on: Optional[List[str]] = None
    ) -> 'PipelineRunner':
        """Add a stage to the pipeline

        Args:
            name: Stage name
            processor: Function that processes data (input → output)
            execution_mode: How to execute this stage
            depends_on: List of stage names this depends on (for mixed mode)

        Returns:
            Self for method chaining
        """
        stage = PipelineStage(
            name=name,
            processor=processor,
            execution_mode=execution_mode,
            depends_on=depends_on or []
        )
        self.stages.append(stage)
        return self

    def run(
        self,
        input_data: Any,
        mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    ) -> Dict[str, StageResult]:
        """Run the pipeline

        Args:
            input_data: Input data for first stage
            mode: Global execution mode (can be overridden per stage)

        Returns:
            Dictionary mapping stage names to results
        """
        results = {}

        if mode == ExecutionMode.SEQUENTIAL:
            results = self._run_sequential(input_data)
        elif mode == ExecutionMode.PARALLEL:
            results = self._run_parallel(input_data)
        elif mode == ExecutionMode.MIXED:
            results = self._run_mixed(input_data)

        return results

    def _run_sequential(self, input_data: Any) -> Dict[str, StageResult]:
        """Run stages sequentially

        Pattern: Task1.complete() → Task2.start() → Task2.complete() → Task3.start()

        Based on L208 lines 691-694 (Sequential Execution)

        Args:
            input_data: Initial input

        Returns:
            Dictionary of stage results
        """
        results = {}
        current_data = input_data

        for stage in self.stages:
            start_time = time.time()

            try:
                # Execute stage
                result_data = stage.processor(current_data)

                result = StageResult(
                    stage_name=stage.name,
                    success=True,
                    result_data=result_data,
                    execution_time=time.time() - start_time
                )

                # Pass output to next stage
                current_data = result_data

            except Exception as e:
                result = StageResult(
                    stage_name=stage.name,
                    success=False,
                    error_message=str(e),
                    execution_time=time.time() - start_time
                )

                # Stop on failure in sequential mode
                break

            results[stage.name] = result

        return results

    def _run_parallel(self, input_data: Any) -> Dict[str, StageResult]:
        """Run stages in parallel

        Pattern: spawn([Task1, Task2, Task3]) → wait_all() → aggregate()

        Based on L208 lines 696-699 (Parallel Execution)

        Design Decision: Simulated parallelism for template.
        Production should use concurrent.futures or asyncio.

        Args:
            input_data: Input data for all stages

        Returns:
            Dictionary of stage results
        """
        results = {}

        # In real parallel execution, these would run concurrently
        # For template, we simulate by running all with same input
        for stage in self.stages:
            start_time = time.time()

            try:
                result_data = stage.processor(input_data)

                result = StageResult(
                    stage_name=stage.name,
                    success=True,
                    result_data=result_data,
                    execution_time=time.time() - start_time
                )

            except Exception as e:
                result = StageResult(
                    stage_name=stage.name,
                    success=False,
                    error_message=str(e),
                    execution_time=time.time() - start_time
                )

            results[stage.name] = result

        return results

    def _run_mixed(self, input_data: Any) -> Dict[str, StageResult]:
        """Run stages with mixed execution pattern

        Pattern: Parallel fan-out → Sequential aggregation → Parallel validation

        Based on L208 lines 701-726 (Mixed Sequential/Parallel)

        Example from L208 (lines 710-724):
        1. Split document into 5 sections (parallel processing)
        2. Merge results sequentially (order matters)
        3. Validate each merged section in parallel

        Args:
            input_data: Initial input

        Returns:
            Dictionary of stage results
        """
        results = {}

        # Group stages by dependencies
        # Stages with no dependencies can run in parallel
        # Stages with dependencies must wait

        independent_stages = [s for s in self.stages if not s.depends_on]
        dependent_stages = [s for s in self.stages if s.depends_on]

        # Phase 1: Run independent stages (parallel)
        for stage in independent_stages:
            start_time = time.time()

            try:
                result_data = stage.processor(input_data)

                result = StageResult(
                    stage_name=stage.name,
                    success=True,
                    result_data=result_data,
                    execution_time=time.time() - start_time
                )

            except Exception as e:
                result = StageResult(
                    stage_name=stage.name,
                    success=False,
                    error_message=str(e),
                    execution_time=time.time() - start_time
                )

            results[stage.name] = result

        # Phase 2: Run dependent stages (sequential, waiting for dependencies)
        for stage in dependent_stages:
            # Check if all dependencies are met
            dependencies_met = all(
                dep_name in results and results[dep_name].success
                for dep_name in stage.depends_on
            )

            if not dependencies_met:
                results[stage.name] = StageResult(
                    stage_name=stage.name,
                    success=False,
                    error_message="Dependencies not met"
                )
                continue

            start_time = time.time()

            try:
                # Gather dependency results
                dep_data = {
                    dep_name: results[dep_name].result_data
                    for dep_name in stage.depends_on
                }

                # Execute with dependency data
                result_data = stage.processor(dep_data)

                result = StageResult(
                    stage_name=stage.name,
                    success=True,
                    result_data=result_data,
                    execution_time=time.time() - start_time
                )

            except Exception as e:
                result = StageResult(
                    stage_name=stage.name,
                    success=False,
                    error_message=str(e),
                    execution_time=time.time() - start_time
                )

            results[stage.name] = result

        return results


class SimplePipeline:
    """Simplified pipeline for common use cases

    Example:
        pipeline = SimplePipeline()
        pipeline.add_step("validate", validate_func)
        pipeline.add_step("process", process_func)
        pipeline.add_step("publish", publish_func)
        result = pipeline.run(document)
    """

    def __init__(self):
        """Initialize simple pipeline"""
        self.steps: List[tuple] = []  # (name, function)

    def add_step(self, name: str, func: Callable) -> 'SimplePipeline':
        """Add a processing step

        Args:
            name: Step name
            func: Processing function

        Returns:
            Self for method chaining
        """
        self.steps.append((name, func))
        return self

    def run(self, input_data: Any) -> Dict[str, Any]:
        """Run pipeline sequentially

        Args:
            input_data: Initial input

        Returns:
            Dictionary with results from each step
        """
        results = {}
        current_data = input_data

        for name, func in self.steps:
            try:
                current_data = func(current_data)
                results[name] = {'success': True, 'data': current_data}
            except Exception as e:
                results[name] = {'success': False, 'error': str(e)}
                break  # Stop on error

        return results


def create_standard_pipeline() -> PipelineRunner:
    """Create a standard document processing pipeline

    Returns:
        Configured PipelineRunner with standard stages
    """
    pipeline = PipelineRunner()

    # Standard stages (functions would be provided by agent)
    pipeline.add_stage("validate_input", lambda x: x)  # Placeholder
    pipeline.add_stage("extract_content", lambda x: x)  # Placeholder
    pipeline.add_stage("process_llm", lambda x: x)  # Placeholder
    pipeline.add_stage("validate_output", lambda x: x)  # Placeholder
    pipeline.add_stage("publish", lambda x: x)  # Placeholder

    return pipeline
