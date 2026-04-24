# Agent Instructions

## Overview
`cagebox` is a Python MCP server for workspace file operations. It is built with `fastmcp`, exposing a sandboxed set of filesystem and shell tools against a configured workspace root.

## Project Structure
```
cagebox/
  main.py         — Entry point and FastMCP server setup
  tools.py        — Tool registration and workspace operations
  workspace.py    — Workspace root path safety utilities
tests/
  conftest.py     — pytest fixtures and test setup
  test_tools.py   — tool behavior tests
  test_workspace.py — path safety tests
pyproject.toml     — package configuration and dependencies
AGENT.md           — agent instructions and implementation summary
README.md          — project usage documentation
```

## Stack
- **Language**: Python 3.10+
- **MCP Framework**: `fastmcp`
- **Server**: built-in `fastmcp` runtime with optional HTTP transport
- **ASGI**: `uvicorn` for running the server in HTTP mode
- **Tests**: `pytest` with `pytest-asyncio`

## Commands
| Command | Description |
|---------|-------------|
| `uv sync` | Install/update dependencies from `pyproject.toml` |
| `uv run cagebox [workspace]` | Start the MCP server with optional workspace root |
| `pytest` | Run the test suite |

## Behavior
- Defaults workspace root to the current directory when none is provided.
- Validates that the workspace root is not the filesystem root.
- Creates the workspace directory if it does not exist.
- Exposes a `/health` endpoint for simple liveness checks.

## Tools
All tools resolve paths safely within the configured workspace root using `workspace.safe_path`. Attempts to escape the workspace root raise an error.

| Tool | Signature | Description |
|------|-----------|-------------|
| `read_file` | `(path: str) -> str` | Read file contents |
| `write_file` | `(path: str, content: str) -> dict` | Write or overwrite a file, creating parent directories |
| `list_dir` | `(path: str) -> dict` | List entries in a directory with `name`, `is_dir`, and `size` |
| `create_dir` | `(path: str) -> dict` | Create a directory and any missing parents |
| `delete_file` | `(path: str) -> dict` | Delete a file |
| `move_file` | `(src: str, dst: str) -> dict` | Move or rename a file |
| `search_files` | `(dir: str, pattern: str) -> dict` | Recursively search for glob matches within a directory |
| `stat_file` | `(path: str) -> dict` | Return metadata for a path (`name`, `size`, `is_dir`, `mode`) |
| `exec_shell` | `(command: str, args: list, cwd: Optional[str] = None) -> dict` | Execute a shell command in the workspace, returning `stdout`, `stderr`, and `exit_code` |

## Safety
- All operations are sandboxed to the configured workspace root.
- `workspace.safe_path` uses `pathlib.Path.resolve()` and `is_relative_to()` to prevent directory traversal attacks.
- Shell execution is limited to commands run from within the workspace and times out after 30 seconds.

## Notes
- `main.py` initializes the FastMCP server and registers tools from `tools.py`.
- `workspace.py` contains the path safety helper and lifespan placeholder.
- `tests/` validate tool functionality and workspace path safety behavior.
