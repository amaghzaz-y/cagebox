"""MCP tools for file and shell operations within a workspace."""

import glob as glob_module
import os
import subprocess
from typing import Optional

from fastmcp import Context
from fastmcp.dependencies import CurrentContext

from .workspace import safe_path


def register_tools(mcp):
    """Register all workspace tools with the FastMCP server."""
    
    @mcp.tool()
    def read_file(path: str, ctx: Context = CurrentContext()) -> str:
        """Read the contents of a file inside the workspace."""
        try:
            workspace_root = ctx.lifespan_context.get("workspace_root", ".")
            safe_file_path = safe_path(workspace_root, path)
            with open(safe_file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"Failed to read file: {e}")

    @mcp.tool()
    def write_file(path: str, content: str, ctx: Context = CurrentContext()) -> dict:
        """Write (or overwrite) a file inside the workspace. Parent directories are created automatically."""
        try:
            workspace_root = ctx.lifespan_context.get("workspace_root", ".")
            safe_file_path = safe_path(workspace_root, path)
            os.makedirs(os.path.dirname(safe_file_path) or workspace_root, exist_ok=True)
            with open(safe_file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"ok": True}
        except Exception as e:
            raise ValueError(f"Failed to write file: {e}")

    @mcp.tool()
    def list_dir(path: str, ctx: Context = CurrentContext()) -> dict:
        """List the contents of a directory inside the workspace."""
        try:
            workspace_root = ctx.lifespan_context.get("workspace_root", ".")
            safe_dir_path = safe_path(workspace_root, path)
            entries = []
            for entry in os.listdir(safe_dir_path):
                entry_path = os.path.join(safe_dir_path, entry)
                is_dir = os.path.isdir(entry_path)
                size = os.path.getsize(entry_path) if not is_dir else 0
                entries.append({
                    "name": entry,
                    "is_dir": is_dir,
                    "size": size,
                })
            return {"entries": entries}
        except Exception as e:
            raise ValueError(f"Failed to list directory: {e}")

    @mcp.tool()
    def create_dir(path: str, ctx: Context = CurrentContext()) -> dict:
        """Create a directory (and any missing parents) inside the workspace."""
        try:
            workspace_root = ctx.lifespan_context.get("workspace_root", ".")
            safe_dir_path = safe_path(workspace_root, path)
            os.makedirs(safe_dir_path, exist_ok=True)
            return {"ok": True}
        except Exception as e:
            raise ValueError(f"Failed to create directory: {e}")

    @mcp.tool()
    def delete_file(path: str, ctx: Context = CurrentContext()) -> dict:
        """Delete a single file inside the workspace."""
        try:
            workspace_root = ctx.lifespan_context.get("workspace_root", ".")
            safe_file_path = safe_path(workspace_root, path)
            os.remove(safe_file_path)
            return {"ok": True}
        except Exception as e:
            raise ValueError(f"Failed to delete file: {e}")

    @mcp.tool()
    def move_file(src: str, dst: str, ctx: Context = CurrentContext()) -> dict:
        """Move or rename a file inside the workspace."""
        try:
            workspace_root = ctx.lifespan_context.get("workspace_root", ".")
            safe_src = safe_path(workspace_root, src)
            safe_dst = safe_path(workspace_root, dst)
            os.makedirs(os.path.dirname(safe_dst) or workspace_root, exist_ok=True)
            os.rename(safe_src, safe_dst)
            return {"ok": True}
        except Exception as e:
            raise ValueError(f"Failed to move file: {e}")

    @mcp.tool()
    def search_files(dir: str, pattern: str, ctx: Context = CurrentContext()) -> dict:
        """Recursively search for files matching a glob pattern inside a workspace directory."""
        try:
            workspace_root = ctx.lifespan_context.get("workspace_root", ".")
            safe_dir_path = safe_path(workspace_root, dir)
            matches = []
            
            # Search recursively: **/{pattern}
            glob_pattern = os.path.join(safe_dir_path, "**", pattern)
            for match in glob_module.glob(glob_pattern, recursive=True):
                rel_match = os.path.relpath(match, safe_dir_path)
                matches.append(rel_match)
            
            # Also search at the top level: {dir}/{pattern}
            glob_pattern_top = os.path.join(safe_dir_path, pattern)
            for match in glob_module.glob(glob_pattern_top):
                rel_match = os.path.relpath(match, safe_dir_path)
                if rel_match not in matches:  # Avoid duplicates
                    matches.append(rel_match)
            
            return {"matches": sorted(matches)}
        except Exception as e:
            raise ValueError(f"Failed to search files: {e}")

    @mcp.tool()
    def stat_file(path: str, ctx: Context = CurrentContext()) -> dict:
        """Return metadata (name, size, type, permissions) for a path inside the workspace."""
        try:
            workspace_root = ctx.lifespan_context.get("workspace_root", ".")
            safe_file_path = safe_path(workspace_root, path)
            stat_info = os.stat(safe_file_path)
            return {
                "name": os.path.basename(safe_file_path),
                "size": stat_info.st_size,
                "is_dir": os.path.isdir(safe_file_path),
                "mode": oct(stat_info.st_mode)[2:],
            }
        except Exception as e:
            raise ValueError(f"Failed to stat file: {e}")

    @mcp.tool()
    def exec_shell(command: str, args: list, cwd: Optional[str] = None, ctx: Context = CurrentContext()) -> dict:
        """Execute a command inside the workspace. Returns stdout, stderr, and exit code."""
        try:
            workspace_root = ctx.lifespan_context.get("workspace_root", ".")
            work_dir = workspace_root
            if cwd:
                work_dir = safe_path(workspace_root, cwd)
            
            cmd = [command] + args
            result = subprocess.run(
                cmd,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": "Command timed out",
                "exit_code": -1,
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
            }
