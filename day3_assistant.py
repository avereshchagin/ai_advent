import logging
import telebot
from dotenv import load_dotenv
import os
import signal
from google import genai

start_prompt = """
Ты опытный Андроид разработчик.
Твоя задача сформировать список зависимосей для нового Андроид проекта.
В чате уточни требования у пользователя к проекту.
Задавай только короткие вопросы. По одному вопросу за раз.
Количество вопросов не должно превышать 8.
"""

chat_prompt = """
Ты опытный Андроид разработчик.
Твоя задача сформировать список зависимосей для нового Андроид проекта.
В чате уточни требования у пользователя к проекту.
Проанализируй историю переписки.
Если ответов достаточно либо уже было задано 8 вопросов, выведи рекомендуемый список зависимостей.
Если данных недостаточно, задай следующий вопрос.
Задавай только короткие вопросы. По одному вопросу за раз.

Не используй markdown. Первой строчкой перед списком зависимостей должно быть слово ==FINAL==.
Список зависимостей необходимо вывести по одной зависимости на строчку в следующем формате:
<group>:<name>:<version>

Пример:
==FINAL==
androidx.core:core-ktx:1.9.0
androidx.test.espresso:espresso-core:3.6.1

История: {}
"""

logging.basicConfig(
    format="%(levelname)s: %(asctime)s %(filename)s:%(funcName)s %(message)s",
    level=logging.INFO,
)

load_dotenv()
bot = telebot.TeleBot(os.getenv("TELEGRAM_TOKEN"))

gemini_client = genai.Client(api_key=os.getenv("GEMINI_TOKEN"))
model = os.getenv("MODEL_NAME")

history = {}

@bot.message_handler(commands=["start"])
def start(message, res=False):
    logging.info("from {} {}".format(message.chat.id, message.from_user.username))
    # bot.send_message(message.chat.id, "Добро пожаловать в AI бот. Чем я могу помочь?")
    response = gemini_client.models.generate_content(model=model, contents=start_prompt).text.strip()
    history_line = "Ассистент: " + response
    history[message.chat.id] = [history_line]
    bot.send_message(message.chat.id, response)


@bot.message_handler(content_types=["text"])
def handle_text(message):
    logging.info("from {} {} > {}".format(message.chat.id, message.from_user.username, message.text))
    history_line = "Пользователь: " + message.text.encode("utf-8", "ignore").decode("utf-8")
    if message.chat.id in history:
        history[message.chat.id].append(history_line)
    else:
        history[message.chat.id] = [history_line]
    prompt = chat_prompt.format("\n".join(history[message.chat.id]))
    response = gemini_client.models.generate_content(model=model, contents=prompt).text.strip()
    if response.startswith("==FINAL=="):
        response = "\n".join(response.splitlines()[1:])
        del history[message.chat.id]
    else:
        history_line = "Ассистент: " + response
        if message.chat.id in history:
            history[message.chat.id].append(history_line)
        else:
            history[message.chat.id] = [history_line]
    bot.send_message(message.chat.id, response[:4096])


def signal_handler(sig, frame):
    logging.info("Terminating signal received")
    bot.stop_bot()


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_handler)
    logging.info("Start polling")
    bot.infinity_polling(logger_level=logging.INFO)
    logging.info("Stop polling")
