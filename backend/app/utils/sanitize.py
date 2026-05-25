"""Input sanitization utilities for security."""
import os
import re
import logging

logger = logging.getLogger(__name__)

# Characters not allowed in filenames
UNSAFE_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

# Maximum filename length
MAX_FILENAME_LENGTH = 255


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal and other attacks.

    - Removes directory separators and path components
    - Removes null bytes and control characters
    - Limits length
    - Removes leading dots (hidden files)
    """
    if not filename:
        return "unnamed_file"

    # Get only the basename (prevent path traversal)
    filename = os.path.basename(filename)

    # Remove unsafe characters
    filename = UNSAFE_FILENAME_CHARS.sub("_", filename)

    # Remove leading dots
    filename = filename.lstrip(".")

    # Limit length
    if len(filename) > MAX_FILENAME_LENGTH:
        name, ext = os.path.splitext(filename)
        filename = name[:MAX_FILENAME_LENGTH - len(ext)] + ext

    # Fallback if empty after sanitization
    if not filename:
        return "unnamed_file"

    return filename


def validate_session_id(session_id: str) -> bool:
    """
    Validate that a session ID is a proper UUID format.
    Prevents injection attacks through session IDs.
    """
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(session_id))


def sanitize_query(query: str, max_length: int = 2000) -> str:
    """
    Sanitize user query input.

    - Strips leading/trailing whitespace
    - Limits length
    - Removes null bytes
    """
    if not query:
        return ""

    # Remove null bytes
    query = query.replace("\x00", "")

    # Strip whitespace
    query = query.strip()

    # Limit length
    if len(query) > max_length:
        query = query[:max_length]

    return query
