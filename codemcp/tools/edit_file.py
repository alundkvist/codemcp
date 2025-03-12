#!/usr/bin/env python3

import logging
import os
from typing import Dict, List, Optional, Tuple

from .file_utils import (
    check_file_path_and_permissions,
    write_text_content,
)

# Set up logger
logger = logging.getLogger(__name__)

__all__ = [
    "edit_file_content",
    "detect_file_encoding",
]


def detect_file_encoding(file_path: str) -> str:
    """Detect the encoding of a file.

    Args:
        file_path: The path to the file

    Returns:
        The encoding of the file, defaults to 'utf-8'

    """
    # Simple implementation - in a real app, would use chardet or similar
    return "utf-8"


def apply_edit(
    file_path: str,
    old_string: str,
    new_string: str,
) -> Tuple[List[Dict[str, str]], str]:
    """Apply an edit to a file using robust matching strategies.

    Args:
        file_path: The path to the file
        old_string: The text to replace
        new_string: The text to replace it with

    Returns:
        A tuple of (patch, updated_file)

    """
    if os.path.exists(file_path):
        with open(file_path, encoding=detect_file_encoding(file_path)) as f:
            content = f.read()
            
        # Create a patch list to track changes
        patches: List[Dict[str, str]] = []
        
        # Apply the edit
        if old_string in content:
            updated_content = content.replace(old_string, new_string)
            patches.append({"old": old_string, "new": new_string})
            return patches, updated_content
            
    return [], ""


def edit_file_content(
    file_path: str,
    old_string: str,
    new_string: str,
    read_file_timestamps: Optional[Dict[str, float]] = None,
    description: str = "",
) -> str:
    """Edit a file by replacing old_string with new_string.

    Args:
        file_path: The path to the file to edit
        old_string: The text to replace
        new_string: The text to replace it with
        read_file_timestamps: Optional dict of file paths to timestamps
        description: Short description of the change (for logging purposes)

    Returns:
        A success or error message

    Note:
        This function allows creating new files if old_string is empty.
        It will write directly to the local filesystem without Git integration.

    """
    try:
        # Validate file path and permissions
        is_valid, error_message = check_file_path_and_permissions(file_path)
        if not is_valid:
            return error_message or "Invalid file path or permissions"

        # If old_string is empty, this is a new file creation
        if not old_string:
            # Write the new file
            write_text_content(file_path, new_string)
            return f"Successfully created new file {file_path}"

        # For existing files, apply the edit
        if not os.path.exists(file_path):
            return f"Error: File does not exist: {file_path}"

        # Apply the edit
        patches, updated_content = apply_edit(file_path, old_string, new_string)
        if not patches:
            return "Error: Could not find text to replace"

        # Write the updated content
        write_text_content(file_path, updated_content)

        return f"Successfully edited {file_path}"

    except Exception as e:
        logger.error(f"Error editing file: {e!s}", exc_info=True)
        return f"Error editing file: {e!s}"
