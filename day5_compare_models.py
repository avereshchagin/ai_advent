import logging
import re
import time

import telebot
from dotenv import load_dotenv
import os
import signal
from openai import OpenAI

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

models = ["zai-org/GLM-4.6:novita", "moonshotai/Kimi-K2-Instruct-0905", "Qwen/Qwen3-32B:cerebras"]

@bot.message_handler(commands=["start"])
def start(message, res=False):
    logging.info("from {} {}".format(message.chat.id, message.from_user.username))
    bot.send_message(message.chat.id, "Добро пожаловать в AI бот. Чем я могу помочь?")


@bot.message_handler(content_types=["text"])
def handle_text(message):
    logging.info("from {} {} > {}".format(message.chat.id, message.from_user.username, message.text))
    prompt = message.text.encode("utf-8", "ignore").decode("utf-8")

    for model in models:
        start_time = time.time()
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        )
        duration = time.time() - start_time
        response = completion.choices[0].message.content
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        bot.send_message(message.chat.id, (f"Model {model}\nDuration: {duration:.2f}\n" + response)[:4096])


def signal_handler(sig, frame):
    logging.info("Terminating signal received")
    bot.stop_bot()


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_handler)
    logging.info("Start polling")
    bot.infinity_polling(logger_level=logging.INFO)
    logging.info("Stop polling")
