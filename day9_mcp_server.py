
from fastmcp import FastMCP

# Instantiate the MCP server
mcp = FastMCP("SimpleMCPServer")

# Define a “ping” tool
@mcp.tool()
def ping() -> str:
    """Return 'pong' to test connectivity."""
    return "pong"


if __name__ == "__main__":
    mcp.run(transport="http", host="localhost", port=8080)
