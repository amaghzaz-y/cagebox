"""Unit tests for workspace path safety."""

import os
import tempfile
from pathlib import Path

import pytest

from cagebox.workspace import safe_path


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_safe_path_valid_relative(temp_workspace):
    """Test resolving a valid relative path."""
    result = safe_path(temp_workspace, "file.txt")
    assert result == os.path.join(temp_workspace, "file.txt")
    assert Path(result).is_relative_to(Path(temp_workspace))


def test_safe_path_valid_nested(temp_workspace):
    """Test resolving a valid nested path."""
    result = safe_path(temp_workspace, "subdir/nested/file.txt")
    expected = os.path.join(temp_workspace, "subdir", "nested", "file.txt")
    assert result == expected


def test_safe_path_traversal_escape(temp_workspace):
    """Test that path traversal attempts are blocked."""
    with pytest.raises(ValueError, match="path escapes workspace"):
        safe_path(temp_workspace, "../../../etc/passwd")


def test_safe_path_dot_dot_escape(temp_workspace):
    """Test that .. at the start is caught."""
    with pytest.raises(ValueError, match="path escapes workspace"):
        safe_path(temp_workspace, "..")


def test_safe_path_absolute_escape():
    """Test that absolute paths outside workspace are blocked."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Try to use /etc/passwd (or Windows equivalent)
        if os.name == "nt":
            escape_path = "C:\\Windows\\System32"
        else:
            escape_path = "/etc/passwd"
        
        with pytest.raises(ValueError, match="path escapes workspace"):
            safe_path(tmpdir, escape_path)


def test_safe_path_workspace_root(temp_workspace):
    """Test that the workspace root itself is valid."""
    result = safe_path(temp_workspace, ".")
    # Should resolve to the workspace root
    assert Path(result).is_relative_to(Path(temp_workspace))


def test_safe_path_empty_string(temp_workspace):
    """Test with empty path string."""
    result = safe_path(temp_workspace, "")
    # Should resolve to the workspace root
    assert Path(result).is_relative_to(Path(temp_workspace))


def test_safe_path_normalization(temp_workspace):
    """Test that paths are normalized (redundant separators removed)."""
    result = safe_path(temp_workspace, "subdir//file.txt")
    expected = os.path.join(temp_workspace, "subdir", "file.txt")
    assert result == expected


def test_safe_path_mixed_separators(temp_workspace):
    """Test that mixed path separators work."""
    # This test is primarily for Windows where both / and \\ are valid
    result = safe_path(temp_workspace, "subdir/file.txt")
    assert Path(result).is_relative_to(Path(temp_workspace))
