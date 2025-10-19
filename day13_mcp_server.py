import logging
import subprocess

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

logging.basicConfig(
    format="%(levelname)s: %(asctime)s %(filename)s:%(funcName)s %(message)s",
    level=logging.INFO,
)

# Instantiate the MCP server
mcp = FastMCP("SimpleMCPServer")

@mcp.tool()
def call_adb(command: str) -> str:
    try:
        logging.info(f"Executing: {command}")
        args = command.split()
        if args[0] != "adb":
            raise ToolError("No adb call")

        output = subprocess.run(
            args=args,
            capture_output=True,
            text=True
        ).stdout
        return output
    except subprocess.CalledProcessError as e:
        raise ToolError(f"Could not execute command: {e}")


if __name__ == "__main__":
    mcp.run(transport="http", host="localhost", port=8080)
