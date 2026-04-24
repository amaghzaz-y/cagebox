"""Workspace management and path safety for Cagebox."""

from pathlib import Path

from fastmcp.server.lifespan import lifespan


def safe_path(workspace_root: str, rel_path: str) -> str:
    """
    Resolve a relative path within the workspace root.
    
    Raises ValueError if the path escapes the workspace (traversal attack).
    Uses Path.is_relative_to() for robust, cross-platform checking.
    
    Args:
        workspace_root: The configured workspace root directory
        rel_path: A relative path within the workspace
        
    Returns:
        The resolved absolute path
        
    Raises:
        ValueError: If the path escapes the workspace
    """
    workspace_path = Path(workspace_root).resolve()
    target_path = (workspace_path / rel_path).resolve()
    
    # Check if target is within workspace using is_relative_to (Python 3.9+)
    if not target_path.is_relative_to(workspace_path):
        raise ValueError(f"path escapes workspace: {rel_path}")
    
    return str(target_path)


@lifespan
async def workspace_lifespan(server):
    """Server lifespan that manages workspace root initialization."""
    # Workspace root is set by the server initialization code
    # This is just a placeholder for future expansion (e.g., cleanup)
    try:
        yield {}
    finally:
        # Cleanup if needed
        pass
