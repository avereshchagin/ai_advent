import logging
import os
import subprocess

import telebot
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

logging.basicConfig(
    format="%(levelname)s: %(asctime)s %(filename)s:%(funcName)s %(message)s",
    level=logging.INFO,
)

# Instantiate the MCP server
mcp = FastMCP("SimpleMCPServer")

load_dotenv()
bot = telebot.TeleBot(os.getenv("TELEGRAM_TOKEN"))
chat_id=os.getenv("CHAT_ID")


@mcp.tool()
def list_commits() -> str:
    try:
        logging.info("git fetch")
        subprocess.run(
            ["git", "fetch"],
            cwd="../../IdeaProjects/kotlin",
            capture_output=True,
            text=True
        )
        logging.info("git log")
        output = subprocess.run(
            ["git", "log", "--since=yesterday"],
            cwd="../../IdeaProjects/kotlin",
            capture_output=True,
            text=True
        ).stdout
        return output
    except subprocess.CalledProcessError as e:
        raise ToolError(f"Could not execute command: {e}")


@mcp.tool()
def notify(message: str):
    try:
        bot.send_message(chat_id, message[:4096])
    except Exception as e:
        raise ToolError(f"Could not send message: {e}")


if __name__ == "__main__":
    mcp.run(transport="http", host="localhost", port=8080)
