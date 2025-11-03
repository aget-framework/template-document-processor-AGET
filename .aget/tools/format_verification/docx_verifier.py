"""
DOCX-Specific Format Verifiers

Checks for Track Changes, comments, and other OOXML structures.
Prevents L245-type failures (100% Track Changes loss).
"""

from pathlib import Path
from typing import Tuple, Dict, List, Any
from zipfile import ZipFile
import re
import logging

from .verification_framework import (
    VerificationResult,
    FormatType,
    verify_format_preserved,
)

logger = logging.getLogger(__name__)


def check_track_changes(docx_path: Path) -> Tuple[bool, int, Dict[str, Any]]:
    """
    Check if DOCX file contains Track Changes markup.

    Args:
        docx_path: Path to DOCX file

    Returns:
        Tuple of (present: bool, count: int, details: dict)
        - present: True if any Track Changes found
        - count: Total number of insertions + deletions
        - details: Dict with insertion/deletion counts and examples

    Implementation:
        Uses zipfile to inspect document.xml for OOXML markup:
        - <w:ins>: Insertions (green underline in Word)
        - <w:del>: Deletions (red strikethrough in Word)

    Example:
        present, count, details = check_track_changes('output.docx')
        if not present:
            print("WARNING: No Track Changes found")
    """
    docx_path = Path(docx_path)

    try:
        with ZipFile(docx_path, 'r') as docx:
            # Read document.xml (main document content)
            doc_xml = docx.read('word/document.xml').decode('utf-8')

            # Count insertions (<w:ins>)
            insertions = re.findall(r'<w:ins[^>]*>', doc_xml)
            insertion_count = len(insertions)

            # Count deletions (<w:del>)
            deletions = re.findall(r'<w:del[^>]*>', doc_xml)
            deletion_count = len(deletions)

            # Extract sample text from first few changes
            insertion_samples = []
            deletion_samples = []

            # Extract text from insertions (simplified)
            for match in re.finditer(r'<w:ins[^>]*>(.*?)</w:ins>', doc_xml, re.DOTALL):
                text_content = re.findall(r'<w:t[^>]*>(.*?)</w:t>', match.group(1))
                if text_content:
                    insertion_samples.append(''.join(text_content[:3]))  # First 3 text runs
                if len(insertion_samples) >= 3:
                    break

            # Extract text from deletions (simplified)
            for match in re.finditer(r'<w:del[^>]*>(.*?)</w:del>', doc_xml, re.DOTALL):
                text_content = re.findall(r'<w:t[^>]*>(.*?)</w:t>', match.group(1))
                if text_content:
                    deletion_samples.append(''.join(text_content[:3]))
                if len(deletion_samples) >= 3:
                    break

            total_count = insertion_count + deletion_count
            present = total_count > 0

            details = {
                "insertion_count": insertion_count,
                "deletion_count": deletion_count,
                "total_count": total_count,
                "insertion_samples": insertion_samples[:3],
                "deletion_samples": deletion_samples[:3],
            }

            return present, total_count, details

    except KeyError:
        # document.xml not found (corrupted DOCX or not a DOCX file)
        logger.warning(f"document.xml not found in {docx_path}")
        return False, 0, {"error": "document_xml_not_found"}

    except Exception as e:
        logger.exception(f"Error checking Track Changes in {docx_path}")
        return False, 0, {"error": str(e)}


def check_comments(docx_path: Path) -> Tuple[bool, int, Dict[str, Any]]:
    """
    Check if DOCX file contains comments.

    Args:
        docx_path: Path to DOCX file

    Returns:
        Tuple of (present: bool, count: int, details: dict)
        - present: True if any comments found
        - count: Number of comments
        - details: Dict with comment counts and samples

    Implementation:
        Checks comments.xml for comment markup (<w:comment>)

    Example:
        present, count, details = check_comments('output.docx')
        if count > 0:
            print(f"Found {count} comments")
    """
    docx_path = Path(docx_path)

    try:
        with ZipFile(docx_path, 'r') as docx:
            # Check if comments.xml exists
            if 'word/comments.xml' not in docx.namelist():
                return False, 0, {"note": "no_comments_file"}

            # Read comments.xml
            comments_xml = docx.read('word/comments.xml').decode('utf-8')

            # Count comments (<w:comment>)
            comments = re.findall(r'<w:comment[^>]*>', comments_xml)
            comment_count = len(comments)

            # Extract authors
            authors = re.findall(r'<w:comment[^>]*w:author="([^"]*)"', comments_xml)
            unique_authors = list(set(authors))

            # Extract sample comment text (first 3)
            comment_samples = []
            for match in re.finditer(r'<w:comment[^>]*>(.*?)</w:comment>', comments_xml, re.DOTALL):
                text_content = re.findall(r'<w:t[^>]*>(.*?)</w:t>', match.group(1))
                if text_content:
                    comment_samples.append(' '.join(text_content[:5]))  # First 5 text runs
                if len(comment_samples) >= 3:
                    break

            present = comment_count > 0

            details = {
                "comment_count": comment_count,
                "unique_authors": unique_authors,
                "author_count": len(unique_authors),
                "comment_samples": comment_samples[:3],
            }

            return present, comment_count, details

    except KeyError:
        # comments.xml not found (no comments in document)
        return False, 0, {"note": "no_comments_file"}

    except Exception as e:
        logger.exception(f"Error checking comments in {docx_path}")
        return False, 0, {"error": str(e)}


def has_track_changes(docx_path: Path) -> bool:
    """
    Quick check if DOCX has Track Changes (no details).

    Args:
        docx_path: Path to DOCX file

    Returns:
        True if Track Changes present, False otherwise

    Example:
        if not has_track_changes('output.docx'):
            raise ValueError("Track Changes lost (L245 failure)")
    """
    present, _, _ = check_track_changes(docx_path)
    return present


def has_comments(docx_path: Path) -> bool:
    """
    Quick check if DOCX has comments (no details).

    Args:
        docx_path: Path to DOCX file

    Returns:
        True if comments present, False otherwise

    Example:
        if has_comments('input.docx') and not has_comments('output.docx'):
            print("WARNING: Comments lost")
    """
    present, _, _ = check_comments(docx_path)
    return present


def verify_track_changes(before_path: Path, after_path: Path) -> VerificationResult:
    """
    Verify Track Changes preserved between two DOCX files.

    Args:
        before_path: Path to DOCX before processing
        after_path: Path to DOCX after processing

    Returns:
        VerificationResult with pass/fail and evidence

    Example:
        result = verify_track_changes('input.docx', 'output.docx')
        if not result.passed:
            logger.error(result.report())
            raise ValueError("Track Changes lost (L245 failure)")
    """
    return verify_format_preserved(
        before_path,
        after_path,
        FormatType.TRACK_CHANGES,
        check_track_changes
    )


def verify_comments(before_path: Path, after_path: Path) -> VerificationResult:
    """
    Verify comments preserved between two DOCX files.

    Args:
        before_path: Path to DOCX before processing
        after_path: Path to DOCX after processing

    Returns:
        VerificationResult with pass/fail and evidence

    Example:
        result = verify_comments('input.docx', 'output.docx')
        if not result.passed:
            logger.warning(result.report())
    """
    return verify_format_preserved(
        before_path,
        after_path,
        FormatType.COMMENTS,
        check_comments
    )


def verify_round_trip(
    original_path: Path,
    processed_path: Path,
    format_types: List[FormatType] = None
) -> List[VerificationResult]:
    """
    Verify round-trip preservation for multiple format types.

    Args:
        original_path: Path to original DOCX
        processed_path: Path to processed DOCX
        format_types: List of format types to verify (default: Track Changes + Comments)

    Returns:
        List of VerificationResult (one per format type)

    Example:
        results = verify_round_trip('input.docx', 'output.docx')
        failed = [r for r in results if not r.passed]
        if failed:
            for result in failed:
                logger.error(result.report())
            raise ValueError(f"{len(failed)} format checks failed")
    """
    if format_types is None:
        format_types = [FormatType.TRACK_CHANGES, FormatType.COMMENTS]

    verifier_registry = {
        FormatType.TRACK_CHANGES: check_track_changes,
        FormatType.COMMENTS: check_comments,
    }

    from .verification_framework import verify_multiple_formats

    return verify_multiple_formats(
        original_path,
        processed_path,
        format_types,
        verifier_registry
    )


def extract_track_changes_text(docx_path: Path) -> Dict[str, List[str]]:
    """
    Extract text from Track Changes for debugging/inspection.

    Args:
        docx_path: Path to DOCX file

    Returns:
        Dict with 'insertions' and 'deletions' lists of text snippets

    Example:
        changes = extract_track_changes_text('output.docx')
        print(f"Insertions: {changes['insertions']}")
        print(f"Deletions: {changes['deletions']}")
    """
    docx_path = Path(docx_path)

    insertions = []
    deletions = []

    try:
        with ZipFile(docx_path, 'r') as docx:
            doc_xml = docx.read('word/document.xml').decode('utf-8')

            # Extract insertions
            for match in re.finditer(r'<w:ins[^>]*>(.*?)</w:ins>', doc_xml, re.DOTALL):
                text_content = re.findall(r'<w:t[^>]*>(.*?)</w:t>', match.group(1))
                if text_content:
                    insertions.append(''.join(text_content))

            # Extract deletions
            for match in re.finditer(r'<w:del[^>]*>(.*?)</w:del>', doc_xml, re.DOTALL):
                text_content = re.findall(r'<w:t[^>]*>(.*?)</w:t>', match.group(1))
                if text_content:
                    deletions.append(''.join(text_content))

    except Exception as e:
        logger.exception(f"Error extracting Track Changes text from {docx_path}")
        return {"insertions": [], "deletions": [], "error": str(e)}

    return {
        "insertions": insertions,
        "deletions": deletions,
        "insertion_count": len(insertions),
        "deletion_count": len(deletions),
    }
