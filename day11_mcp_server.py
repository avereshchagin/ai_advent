import os
import subprocess

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

# Instantiate the MCP server
mcp = FastMCP("SimpleMCPServer")

# Define a “ping” tool
@mcp.tool()
def list_commits() -> str:
    """
    List latest commits in the git repository.
    """
    try:
        output = subprocess.run(
            ["git", "fetch"],
            cwd="../../IdeaProjects/kotlin",
            capture_output=True,
            text=True
        )
        output = subprocess.run(
            ["git", "log", "--since=yesterday"],
            cwd="../../IdeaProjects/kotlin",
            capture_output=True,
            text=True
        ).stdout
        return output
    except subprocess.CalledProcessError as e:
        raise ToolError(f"Could not execute command: {e}")


if __name__ == "__main__":
    mcp.run(transport="http", host="localhost", port=8080)
