import logging
import re
import time

import telebot
from dotenv import load_dotenv
import os
import signal
from openai import OpenAI
from transformers import AutoTokenizer

logging.basicConfig(
    format="%(levelname)s: %(asctime)s %(filename)s:%(funcName)s %(message)s",
    level=logging.INFO,
)

load_dotenv()
bot = telebot.TeleBot(os.getenv("TELEGRAM_TOKEN"))


class Model:
    def __init__(self, name, client):
        self.name = name
        self.client = client

    def generate(self, prompt):
        completion = self.client.chat.completions.create(
            model=self.name,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        )
        response = completion.choices[0].message.content
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        return response


class LlmPipeline:
    def __init__(self, source_model, verification_model):
        self.summary_model = source_model
        self.main_model = verification_model

    def generate(self, prompt, input_tokens):
        if input_tokens > 1000:
            prompt = self.summary_model.generate(f"Сожми этот запрос до одного абзаца: {prompt}")
        response = self.main_model.generate(prompt)
        return response


client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.getenv("HF_TOKEN"),
)

pipeline = LlmPipeline(
    source_model=Model("zai-org/GLM-4.6:novita", client),
    verification_model=Model("deepseek-ai/DeepSeek-R1:fireworks-ai", client),
)


@bot.message_handler(commands=["start"])
def start(message, res=False):
    logging.info("from {} {}".format(message.chat.id, message.from_user.username))
    bot.send_message(message.chat.id, "Добро пожаловать в AI бот. Чем я могу помочь?")


@bot.message_handler(content_types=["text"])
def handle_text(message):
    logging.info("from {} {} > {}".format(message.chat.id, message.from_user.username, message.text))
    prompt = message.text.encode("utf-8", "ignore").decode("utf-8")
    tokenizer = AutoTokenizer.from_pretrained("deepseek-ai/DeepSeek-R1")
    input_tokens = len(tokenizer.encode(prompt))
    bot.send_message(message.chat.id, f"Input tokens: {input_tokens}")
    response = pipeline.generate(prompt, input_tokens)
    output_tokens = len(tokenizer.encode(response))
    bot.send_message(message.chat.id, f"Output tokens: {output_tokens}")
    bot.send_message(message.chat.id, response[:4096])


def signal_handler(sig, frame):
    logging.info("Terminating signal received")
    bot.stop_bot()


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_handler)
    logging.info("Start polling")
    bot.infinity_polling(logger_level=logging.INFO)
    logging.info("Stop polling")
