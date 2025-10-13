import asyncio
import logging
import re
import time

import telebot
from dotenv import load_dotenv
import os
import signal
from openai import OpenAI
from transformers import AutoTokenizer
from fastmcp import Client

logging.basicConfig(
    format="%(levelname)s: %(asctime)s %(filename)s:%(funcName)s %(message)s",
    level=logging.INFO,
)

load_dotenv()
bot = telebot.TeleBot(os.getenv("TELEGRAM_TOKEN"))

client = Client("http://localhost:8080/mcp")

async def list_mcp_tools():
    async with client:
        return await client.list_tools()


@bot.message_handler(commands=["start"])
def start(message, res=False):
    logging.info("from {} {}".format(message.chat.id, message.from_user.username))
    bot.send_message(message.chat.id, "Добро пожаловать в AI бот. Чем я могу помочь?")


@bot.message_handler(commands=["tools"])
def tools_call(message, res=False):
    logging.info("from {} {}".format(message.chat.id, message.from_user.username))
    tools = asyncio.run(list_mcp_tools())
    tools_names = [t.name for t in tools]
    bot.send_message(message.chat.id, f"Available tools: {tools_names}")


@bot.message_handler(content_types=["text"])
def handle_text(message):
    logging.info("from {} {} > {}".format(message.chat.id, message.from_user.username, message.text))


def signal_handler(sig, frame):
    logging.info("Terminating signal received")
    bot.stop_bot()


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_handler)
    logging.info("Start polling")
    bot.infinity_polling(logger_level=logging.INFO)
    logging.info("Stop polling")
