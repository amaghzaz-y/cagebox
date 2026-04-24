# cagebox

MCP server for workspace file operations, implemented in Python with FastMCP.

## Installation

Install dependencies using uv:

```bash
uv sync
```

## Running

Start the server with a workspace root directory:

```bash
uv run cagebox /path/to/workspace
```

If no workspace path is provided, the current directory is used as the workspace root.

## Tools

The server provides the following tools:

- `read_file`: Read file contents
- `write_file`: Write or overwrite a file
- `list_dir`: List directory contents
- `create_dir`: Create a directory
- `delete_file`: Delete a file
- `move_file`: Move or rename a file
- `search_files`: Search for files matching a glob pattern
- `stat_file`: Get file metadata
- `exec_shell`: Execute shell commands

## Project Structure

```
cagebox/
  └── main.py         # MCP server implementation
pyproject.toml        # Project configuration and dependencies
```
