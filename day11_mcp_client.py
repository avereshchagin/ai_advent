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


def run_prompt(prompt, chat_id):
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
                        name="list_commits",
                        description="List latest commits in the git repository",
                        parameters={
                            "type": "string"
                        }
                    )
                )
            ],
            tool_choice="auto"
        )
        response = completion.choices[0].message.content
        if response.strip():
            messages.append({"role": "assistant", "content": response})
            bot.send_message(chat_id, response[:4096])

        tool_calls = completion.choices[0].message.tool_calls
        if isinstance(tool_calls, Sequence) and len(tool_calls) > 0:
            tool_call = tool_calls[0]
            name = tool_call.function.name
            logging.info(f"Tool call: {name}")
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


# Start script with cron task once a day
if __name__ == "__main__":
    chat_id=os.getenv("CHAT_ID")
    run_prompt("Собери саммари коммитов в репозитории за сегодняшний день", chat_id)

