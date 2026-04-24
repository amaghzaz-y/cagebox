"""Cagebox - MCP server for workspace file operations."""

__version__ = "0.1.0"

import argparse
import os
import sys

from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan
from starlette.responses import PlainTextResponse

from .tools import register_tools


def create_app_lifespan(workspace_root):
    """Factory function to create a lifespan that captures workspace_root."""
    @lifespan
    async def app_lifespan(server):
        """Initialize workspace root on server startup."""
        try:
            yield {"workspace_root": workspace_root}
        finally:
            # Cleanup if needed
            pass
    return app_lifespan


def main():
    """Main entry point for the MCP server."""
    parser = argparse.ArgumentParser(description="Cagebox MCP server")
    parser.add_argument(
        "workspace",
        nargs="?",
        default=".",
        help="Workspace root directory (default: current directory)"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="http",
        help="Transport protocol (default: http)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    
    args = parser.parse_args()
    
    # Resolve and validate workspace root
    workspace_root = os.path.abspath(args.workspace)
    
    try:
        os.makedirs(workspace_root, exist_ok=True)
    except Exception as e:
        print(f"Cannot create workspace root {workspace_root}: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Validate that it's not the filesystem root
    if workspace_root.rstrip(os.sep) == os.path.splitdrive(workspace_root)[0]:
        print("Workspace root cannot be the filesystem root", file=sys.stderr)
        sys.exit(1)
    
    # Create FastMCP server
    mcp = FastMCP(
        name="cagebox",
        instructions="Workspace file operation tools for manipulating files, directories, and executing shell commands within a sandbox.",
    )
    
    # Register tools
    register_tools(mcp)
    
    # Add health check route
    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request):
        return PlainTextResponse("OK")
    
    # Create lifespan with workspace_root
    app_lifespan = create_app_lifespan(workspace_root)
    
    # Run the server
    try:
        if args.transport == "http":
            mcp.run(
                transport="http",
                host=args.host,
                port=args.port,
            )
        else:
            mcp.run()
    except KeyboardInterrupt:
        print("Server stopped", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
