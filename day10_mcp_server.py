import os
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

# Instantiate the MCP server
mcp = FastMCP("SimpleMCPServer")

# Define a “ping” tool
@mcp.tool()
def list_files(path: str = ".") -> list[str]:
    """
    List files and directories in the given path (relative or absolute).
    """
    print(f"list_files: {path}")
    if not os.path.exists(path):
        raise ToolError(f"Path not found: {path}")

    if not os.path.isdir(path):
        raise ToolError(f"Path is not a directory: {path}")

    try:
        entries = os.listdir(path)
    except PermissionError:
        raise ToolError(f"Permission denied: {path}")
    except Exception as e:
        raise ToolError(f"Could not list directory {path!r}: {e}")
    print(f"entries: {entries}")
    return entries


if __name__ == "__main__":
    mcp.run(transport="http", host="localhost", port=8080)
