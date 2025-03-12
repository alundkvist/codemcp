#!/usr/bin/env python3

import logging
import os
import subprocess

from .common import normalize_file_path
from .shell import run_command

__all__ = [
    "is_git_repository",
    "commit_pending_changes",
    "commit_changes",
]


def is_git_repository(path: str) -> bool:
    """Check if the path is within a Git repository.

    Args:
        path: The file path to check

    Returns:
        True if path is in a Git repository, False otherwise

    """
    try:
        # Get the directory containing the file or use the path itself if it's a directory
        directory = os.path.dirname(path) if os.path.isfile(path) else path

        # Get the absolute path to ensure consistency
        directory = os.path.abspath(directory)

        # Run git command to verify this is a git repository
        run_command(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=directory,
            check=True,
            capture_output=True,
            text=True,
        )

        # Also get the repository root to use for all git operations
        try:
            run_command(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=directory,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()

            # Store the repository root in a global or class variable if needed
            # This could be used to ensure all git operations use the same root

            return True
        except (subprocess.SubprocessError, OSError):
            # If we can't get the repo root, it's not a proper git repository
            return False
    except (subprocess.SubprocessError, OSError):
        return False


def commit_pending_changes(file_path: str) -> tuple[bool, str]:
    """Check if a file is tracked by git and return its status.
    No longer commits changes, just checks file status.

    Args:
        file_path: The path to the file to check

    Returns:
        A tuple of (success, message)
    """
    try:
        # First, check if this is a git repository
        if not is_git_repository(file_path):
            return False, "File is not in a Git repository"

        directory = os.path.dirname(file_path)

        # Check if the file is tracked by git
        file_status = run_command(
            ["git", "ls-files", "--error-unmatch", file_path],
            cwd=directory,
            capture_output=True,
            text=True,
            check=False,
        )

        file_is_tracked = file_status.returncode == 0

        # If the file is not tracked, return an error
        if not file_is_tracked:
            return (
                False,
                "File is not tracked by git. Please add the file to git tracking first using 'git add <file>'",
            )

        return True, "File status checked successfully"
    except Exception as e:
        logging.warning(
            f"Exception suppressed when checking file status: {e!s}",
            exc_info=True,
        )
        return False, f"Error checking file status: {e!s}"


def commit_changes(path: str, description: str) -> tuple[bool, str]:
    """Add changes to git staging area but do not commit.
    This function now only stages changes without committing.

    Args:
        path: The path to the file or directory to stage
        description: Unused parameter kept for compatibility

    Returns:
        A tuple of (success, message)
    """
    try:
        # First, check if this is a git repository
        if not is_git_repository(path):
            return False, f"Path '{path}' is not in a Git repository"

        # Get absolute paths for consistency
        abs_path = os.path.abspath(path)

        # Get the directory - if path is a file, use its directory, otherwise use the path itself
        directory = os.path.dirname(abs_path) if os.path.isfile(abs_path) else abs_path

        # Try to get the git repository root for more reliable operations
        try:
            repo_root = run_command(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=directory,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()

            # Use the repo root as the working directory for git commands
            git_cwd = repo_root
        except (subprocess.SubprocessError, OSError):
            # Fall back to the directory if we can't get the repo root
            git_cwd = directory

        # If it's a file, check if it exists
        if os.path.isfile(abs_path) and not os.path.exists(abs_path):
            return False, f"File does not exist: {abs_path}"

        # Add the path to git - could be a file or directory
        try:
            # If path is a directory, do git add .
            add_command = (
                ["git", "add", "."]
                if os.path.isdir(abs_path)
                else ["git", "add", abs_path]
            )

            add_result = run_command(
                add_command,
                cwd=git_cwd,
                capture_output=True,
                text=True,
                check=False,
            )
        except Exception as e:
            return False, f"Failed to add to Git: {str(e)}"

        if add_result.returncode != 0:
            return False, f"Failed to add to Git: {add_result.stderr}"

        return True, "Changes staged successfully"
    except Exception as e:
        logging.warning(
            f"Exception suppressed when staging changes: {e!s}",
            exc_info=True,
        )
        return False, f"Error staging changes: {e!s}"
