"""Integration Tests for Document Processor

Tests critical workflows, script integration, and system contracts:
- End-to-end document processing workflows
- Script-module integration
- Version compliance and directory structure
- Multi-module interactions

Complements smoke_test.py (20 tests) with integration and contract validation.
"""

import sys
import json
import tempfile
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_workflow_validate_process_publish():
    """Test complete workflow: validation → processing → publishing"""
    from ingestion.validator import DocumentValidator
    from ingestion.queue_manager import QueueManager
    from security.input_sanitizer import InputSanitizer
    from output.version_manager import VersionManager
    from output.publisher import FilesystemPublisher

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test document
        test_doc = Path(tmpdir) / "test_doc.txt"
        test_doc.write_text("Sample document content for testing workflow")

        # Stage 1: Validation
        validator = DocumentValidator(rules=[])
        validation_result = validator.validate(str(test_doc))
        assert validation_result.valid, "Document should be valid"

        # Stage 2: Queue enrollment
        queue_file = Path(tmpdir) / "queue.json"
        queue = QueueManager(queue_file=str(queue_file))
        doc_id = "test_doc"
        doc_size = test_doc.stat().st_size

        queue_item = queue.add_candidate(doc_id, str(test_doc), doc_size)
        assert queue_item is not None
        queue.mark_pending(doc_id)

        # Stage 3: Sanitization
        sanitizer = InputSanitizer(max_length=50000)
        content = test_doc.read_text()
        sanitized_content = sanitizer.sanitize(content)
        assert sanitized_content == content  # Clean content should pass through

        # Stage 4: Version creation
        versions_dir = Path(tmpdir) / "versions"
        version_manager = VersionManager(versions_dir=str(versions_dir))
        version = version_manager.create_version(
            doc_id,
            sanitized_content,
            {"validated": True, "sanitized": True},
            "Workflow test version"
        )
        assert version.number == 1
        assert version.document_id == doc_id

        # Stage 5: Publishing
        output_dir = Path(tmpdir) / "output"
        publisher = FilesystemPublisher(output_dir=str(output_dir))
        result = publisher.publish(doc_id, sanitized_content, {"version": 1})
        assert result.success

        # Mark as processed in queue
        queue.mark_processed(doc_id, {"version_id": version.version_id})

        # Verify queue state
        status = queue.get_status()
        assert status['processed'] == 1
        assert status['failed'] == 0

        print("✅ Complete workflow successful (validation → processing → publishing)")


def test_script_integration_validate():
    """Test validate.py script uses DocumentValidator correctly"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test document content")
        test_file = f.name

    # Run validate.py script
    result = subprocess.run(
        ["python3", "scripts/validate.py", test_file],
        capture_output=True,
        text=True
    )

    # Should succeed (exit code 0)
    assert result.returncode == 0, f"Validation failed: {result.stderr}"
    assert "VALID" in result.stdout or "✅" in result.stdout

    # Clean up
    Path(test_file).unlink()

    print("✅ validate.py script integration successful")


def test_script_integration_queue_status():
    """Test queue_status.py script uses QueueManager correctly"""
    # Run queue_status.py script
    result = subprocess.run(
        ["python3", "scripts/queue_status.py"],
        capture_output=True,
        text=True
    )

    # Should succeed (exit code 0)
    assert result.returncode == 0, f"Queue status failed: {result.stderr}"

    # Should show queue statistics
    assert "Total items" in result.stdout or "Candidates" in result.stdout

    print("✅ queue_status.py script integration successful")


def test_contract_version_compliance():
    """Test version.json structure and compliance"""
    version_file = Path(".aget/version.json")

    # Version file must exist
    assert version_file.exists(), "version.json must exist"

    # Parse and validate structure
    with open(version_file) as f:
        version_data = json.load(f)

    # Required fields
    required_fields = [
        "agent_name",
        "aget_version",
        "instance_type",
        "domain",
        "created_at"
    ]

    for field in required_fields:
        assert field in version_data, f"Required field '{field}' missing from version.json"

    # Validate field values
    assert isinstance(version_data['agent_name'], str)
    assert len(version_data['agent_name']) > 0

    assert isinstance(version_data['aget_version'], str)
    assert version_data['aget_version'].startswith('2.')  # Version 2.x expected

    assert version_data['instance_type'] in ['AGET', 'aget']

    assert isinstance(version_data['domain'], str)

    print("✅ Version compliance validation successful")


def test_contract_directory_structure():
    """Test required directories are present"""
    required_dirs = [
        ".aget",
        ".aget/docs",
        ".aget/docs/protocols",
        ".aget/specs",
        ".aget/tools",
        "src",
        "src/ingestion",
        "src/processing",
        "src/output",
        "src/security",
        "src/pipeline",
        "src/wikitext",
        "scripts",
        "tests",
        "configs",
        "configs/schemas",
        "configs/wikitext"
    ]

    missing_dirs = []
    for dir_path in required_dirs:
        if not Path(dir_path).is_dir():
            missing_dirs.append(dir_path)

    assert len(missing_dirs) == 0, f"Missing required directories: {missing_dirs}"

    # Check required files
    required_files = [
        ".aget/version.json",
        "AGENTS.md",
        "README.md",
        "tests/smoke_test.py"
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).is_file():
            missing_files.append(file_path)

    assert len(missing_files) == 0, f"Missing required files: {missing_files}"

    print("✅ Directory structure validation successful")


def run_all_integration_tests():
    """Run all integration tests"""
    tests = [
        ("workflow_validate_process_publish", test_workflow_validate_process_publish),
        ("script_integration_validate", test_script_integration_validate),
        ("script_integration_queue_status", test_script_integration_queue_status),
        ("contract_version_compliance", test_contract_version_compliance),
        ("contract_directory_structure", test_contract_directory_structure),
    ]

    print("=" * 70)
    print("Gate 5: Integration & Contract Tests - Batch 1")
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
    print(f"Batch 1 Results: {passed} passed, {failed} failed (out of {len(tests)} total)")
    print("=" * 70)

    if errors:
        print()
        print("Failed Tests:")
        for name, error in errors:
            print(f"  - {name}: {error}")

    return passed, failed, errors


if __name__ == "__main__":
    passed, failed, errors = run_all_integration_tests()
    sys.exit(0 if failed == 0 else 1)
