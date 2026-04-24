"""Integration tests for workspace tools."""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

from fastmcp import FastMCP
from fastmcp.client import Client
from fastmcp.server.lifespan import lifespan

from cagebox.tools import register_tools


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mcp_server(temp_workspace):
    """Create a FastMCP server with tools registered."""

    @lifespan
    async def app_lifespan(server):
        yield {"workspace_root": temp_workspace}

    mcp = FastMCP(name="test-cagebox", lifespan=app_lifespan)
    register_tools(mcp)
    return mcp


@pytest.mark.asyncio
async def test_read_file(mcp_server, temp_workspace):
    """Test reading a file."""
    test_file = os.path.join(temp_workspace, "test.txt")
    test_content = "Hello, World!"
    with open(test_file, "w") as f:
        f.write(test_content)

    async with Client(mcp_server) as client:
        result = await client.call_tool("read_file", {"path": "test.txt"})

    assert result.content[0].text == test_content


@pytest.mark.asyncio
async def test_write_file(mcp_server, temp_workspace):
    """Test writing a file."""
    test_path = "newfile.txt"
    test_content = "New content"

    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "write_file", {"path": test_path, "content": test_content}
        )

    assert json.loads(result.content[0].text) == {"ok": True}

    written_file = os.path.join(temp_workspace, test_path)
    assert os.path.exists(written_file)
    with open(written_file, "r") as f:
        assert f.read() == test_content


@pytest.mark.asyncio
async def test_write_file_with_nested_dir(mcp_server, temp_workspace):
    """Test writing a file in a nested directory (auto-create)."""
    test_path = "dir/subdir/file.txt"
    test_content = "Nested content"

    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "write_file", {"path": test_path, "content": test_content}
        )

    assert json.loads(result.content[0].text) == {"ok": True}

    written_file = os.path.join(temp_workspace, test_path)
    assert os.path.exists(written_file)


@pytest.mark.asyncio
async def test_list_dir(mcp_server, temp_workspace):
    """Test listing directory contents."""
    os.makedirs(os.path.join(temp_workspace, "subdir"))
    Path(os.path.join(temp_workspace, "file1.txt")).touch()
    Path(os.path.join(temp_workspace, "file2.txt")).touch()

    async with Client(mcp_server) as client:
        result = await client.call_tool("list_dir", {"path": "."})

    entries = json.loads(result.content[0].text)["entries"]

    names = {entry["name"] for entry in entries}
    assert "subdir" in names
    assert "file1.txt" in names
    assert "file2.txt" in names


@pytest.mark.asyncio
async def test_create_dir(mcp_server, temp_workspace):
    """Test creating a directory."""
    test_dir = "new_directory"

    async with Client(mcp_server) as client:
        result = await client.call_tool("create_dir", {"path": test_dir})

    assert json.loads(result.content[0].text) == {"ok": True}
    assert os.path.isdir(os.path.join(temp_workspace, test_dir))


@pytest.mark.asyncio
async def test_delete_file(mcp_server, temp_workspace):
    """Test deleting a file."""
    test_file = os.path.join(temp_workspace, "delete_me.txt")
    Path(test_file).touch()

    async with Client(mcp_server) as client:
        result = await client.call_tool("delete_file", {"path": "delete_me.txt"})

    assert json.loads(result.content[0].text) == {"ok": True}
    assert not os.path.exists(test_file)


@pytest.mark.asyncio
async def test_move_file(mcp_server, temp_workspace):
    """Test moving/renaming a file."""
    src = os.path.join(temp_workspace, "original.txt")
    Path(src).touch()

    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "move_file", {"src": "original.txt", "dst": "moved.txt"}
        )

    assert json.loads(result.content[0].text) == {"ok": True}
    assert not os.path.exists(src)
    assert os.path.exists(os.path.join(temp_workspace, "moved.txt"))


@pytest.mark.asyncio
async def test_search_files(mcp_server, temp_workspace):
    """Test searching for files."""
    Path(os.path.join(temp_workspace, "file1.txt")).touch()
    Path(os.path.join(temp_workspace, "file2.txt")).touch()
    Path(os.path.join(temp_workspace, "other.md")).touch()
    os.makedirs(os.path.join(temp_workspace, "subdir"))
    Path(os.path.join(temp_workspace, "subdir", "file3.txt")).touch()

    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "search_files", {"dir": ".", "pattern": "*.txt"}
        )

    matches = json.loads(result.content[0].text)["matches"]

    assert "file1.txt" in matches
    assert "file2.txt" in matches
    assert "other.md" not in matches
    assert (
        "subdir/file3.txt" in matches or os.path.join("subdir", "file3.txt") in matches
    )


@pytest.mark.asyncio
async def test_stat_file(mcp_server, temp_workspace):
    """Test getting file stats."""
    test_file = os.path.join(temp_workspace, "stats.txt")
    with open(test_file, "w") as f:
        f.write("content")

    async with Client(mcp_server) as client:
        result = await client.call_tool("stat_file", {"path": "stats.txt"})

    stats = json.loads(result.content[0].text)

    assert stats["name"] == "stats.txt"
    assert stats["size"] == 7  # length of "content"
    assert stats["is_dir"] is False


@pytest.mark.asyncio
async def test_exec_shell(mcp_server, temp_workspace):
    """Test executing a shell command."""
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "exec_shell",
            {"command": sys.executable, "args": ["-c", "print('hello')"]},
        )

    output = json.loads(result.content[0].text)

    assert output["exit_code"] == 0
    assert "hello" in output["stdout"]


@pytest.mark.asyncio
async def test_exec_shell_failure(mcp_server, temp_workspace):
    """Test executing a command that fails."""
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "exec_shell",
            {"command": sys.executable, "args": ["-c", "import sys; sys.exit(1)"]},
        )

    output = json.loads(result.content[0].text)

    assert output["exit_code"] != 0


@pytest.mark.asyncio
async def test_read_file_traversal_blocked(mcp_server, temp_workspace):
    """Test that path traversal is blocked."""
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "read_file", {"path": "../../etc/passwd"}, raise_on_error=False
        )

    assert result.is_error


@pytest.mark.asyncio
async def test_exec_shell_with_cwd(mcp_server, temp_workspace):
    """Test executing a command with a specific cwd."""
    subdir = os.path.join(temp_workspace, "workdir")
    os.makedirs(subdir)

    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "exec_shell",
            {
                "command": sys.executable,
                "args": ["-c", "import os; print(os.getcwd())"],
                "cwd": "workdir",
            },
        )

    output = json.loads(result.content[0].text)
    assert output["exit_code"] == 0
    assert "workdir" in output["stdout"]
