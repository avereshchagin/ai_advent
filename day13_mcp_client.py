import asyncio
import json
import logging
import os
import signal
from typing import Sequence

import telebot
from dotenv import load_dotenv
from fastmcp import Client
from openai import OpenAI
from openai.types.chat import ChatCompletionToolParam
from openai.types.shared_params import FunctionDefinition

logging.basicConfig(
    format="%(levelname)s: %(asctime)s %(filename)s:%(funcName)s %(message)s",
    level=logging.INFO,
)

load_dotenv()
bot = telebot.TeleBot(os.getenv("TELEGRAM_TOKEN"))

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.getenv("HF_TOKEN"),
)

messages = []

mcp_client = Client("http://localhost:8080/mcp")

async def list_mcp_tools():
    async with mcp_client:
        return await mcp_client.list_tools()

async def call_tool(tool_name, tool_args):
    async with mcp_client:
        return await mcp_client.call_tool(tool_name, tool_args)

tools = asyncio.run(list_mcp_tools())


@bot.message_handler(commands=["start"])
def start(message, res=False):
    logging.info("from {} {}".format(message.chat.id, message.from_user.username))
    bot.send_message(message.chat.id, "Добро пожаловать в AI бот. Чем я могу помочь?")


@bot.message_handler(content_types=["text"])
def handle_text(message):
    logging.info("from {} {} > {}".format(message.chat.id, message.from_user.username, message.text))
    prompt = message.text.encode("utf-8", "ignore").decode("utf-8")
    messages.clear()
    messages.append({"role": "user", "content": prompt})
    is_finished = False

    while not is_finished:
        completion = client.chat.completions.create(
            model="zai-org/GLM-4.6:novita",
            messages=messages,
            tools=[
                ChatCompletionToolParam(
                    type="function",
                    function=FunctionDefinition(
                        name="call_adb",
                        description="Calls adb command. Example command argument: 'adb shell pm list packages'",
                        parameters={
                            "type": ["string"],
                            "properties": {"command": {"type": "string"}},
                            "required": ["command"]
                        }
                    )
                )
            ],
            tool_choice="auto"
        )
        response = completion.choices[0].message.content
        messages.append({"role": "assistant", "content": response})
        bot.send_message(message.chat.id, response[:4096])

        tool_calls = completion.choices[0].message.tool_calls
        if isinstance(tool_calls, Sequence) and len(tool_calls) > 0:
            tool_call = tool_calls[0]
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            tool_result = asyncio.run(call_tool(name, args))
            logging.info(f"Tool result: {tool_result}")
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result.structured_content)
            })
        else:
            is_finished = True



def signal_handler(sig, frame):
    logging.info("Terminating signal received")
    bot.stop_bot()


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_handler)
    logging.info("Start polling")
    bot.infinity_polling(logger_level=logging.INFO)
    logging.info("Stop polling")
