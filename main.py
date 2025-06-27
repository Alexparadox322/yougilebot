import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import requests

# Загрузка переменных окружения
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
YOUGILE_TOKEN = os.getenv("YOUGILE_TOKEN")
COLUMN_ID = os.getenv("COLUMN_ID")
ASSIGNEE_ID = os.getenv("ASSIGNEE_ID")
NOTIFY_CHAT_ID = os.getenv("NOTIFY_CHAT_ID")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

user_states = {}

PROJECT_PREFIXES = {
    "Декада": "Декада",
    "ЗТЧ": "ЗТЧ",
    "Броктон": "Броктон",
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Оставить запрос", callback_data="leave_request")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Выберите действие:", reply_markup=reply_markup)

async def project_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "leave_request":
        keyboard = [
            [InlineKeyboardButton(name, callback_data=f"project_{name}")]
            for name in PROJECT_PREFIXES.keys()
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите проект:", reply_markup=reply_markup)
    elif query.data.startswith("project_"):
        project = query.data.split("_", 1)[1]
        user_states[query.from_user.id] = {"project": project}
        await query.edit_message_text(f"Вы выбрали проект: {project}. Введите ваш запрос.")

async def request_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    state = user_states.get(user_id)

    if state and "project" in state:
        project = state["project"]
        description = update.message.text.strip()

        # Генерация заголовка задачи
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        title = f"{PROJECT_PREFIXES[project]}_{timestamp}"

        # Подготовка дедлайна
        now_ts = int(datetime.now().timestamp() * 1000)
        deadline_obj = {
            "deadline": now_ts,
            "startDate": now_ts,
            "withTime": True,
            "history": [],
            "blockedPoints": [],
            "links": [],
        }

        data = {
            "title": title,
            "columnId": COLUMN_ID,
            "description": description,
            "assigned": [ASSIGNEE_ID],
            "deadline": deadline_obj,
        }

        headers = {
            "Authorization": f"Bearer {YOUGILE_TOKEN}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                "https://ru.yougile.com/api-v2/tasks", json=data, headers=headers
            )
            if response.status_code == 201:
                await update.message.reply_text(f"✅ Заявка зарегистрирована: {title}")

                # Отправка уведомления в канал
                notify_msg = f"📬 Новая заявка **{title}** зарегистрирована"
                requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                    data={
                        "chat_id": NOTIFY_CHAT_ID,
                        "text": notify_msg,
                        "parse_mode": "Markdown",
                    },
                )
            else:
                logging.error(response.text)
                await update.message.reply_text("❌ Ошибка при создании задачи.")
        except Exception as e:
            logging.exception("Ошибка при запросе:")
            await update.message.reply_text("⚠️ Ошибка при отправке запроса.")
        finally:
            user_states.pop(user_id, None)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(project_choice_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, request_input_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
