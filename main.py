import logging
import telebot
from dotenv import load_dotenv
import os
import signal
from google import genai

logging.basicConfig(
    format="%(levelname)s: %(asctime)s %(filename)s:%(funcName)s %(message)s",
    level=logging.INFO,
)

load_dotenv()
print(os.getenv("TELEGRAM_TOKEN"))
bot = telebot.TeleBot(os.getenv("TELEGRAM_TOKEN"))

gemini_client = genai.Client(api_key=os.getenv("GEMINI_TOKEN"))
model = os.getenv("MODEL_NAME")


@bot.message_handler(commands=["start"])
def start(message, res=False):
    logging.info("from {} {}".format(message.chat.id, message.from_user.username))
    bot.send_message(message.chat.id, "Добро пожаловать в AI бот. Чем я могу помочь?")


@bot.message_handler(content_types=["text"])
def handle_text(message):
    logging.info("from {} {} > ".format(message.chat.id, message.from_user.username, message.text))
    prompt = message.text.encode("utf-8", "ignore").decode("utf-8")
    response = gemini_client.models.generate_content(model = model, contents = prompt).text.strip()
    bot.send_message(message.chat.id, response)


def signal_handler(sig, frame):
    logging.info("Terminating signal received")
    bot.stop_bot()


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_handler)
    logging.info("Start polling")
    bot.infinity_polling(logger_level=logging.INFO)
    logging.info("Stop polling")
