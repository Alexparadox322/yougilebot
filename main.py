import logging
import time
import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
YOUGILE_API_TOKEN = os.getenv("YOUGILE_API_TOKEN")
COLUMN_ID = os.getenv("COLUMN_ID")
ASSIGNED_USER_IDS = [os.getenv("ASSIGNED_USER_ID")]
NOTIFY_CHANNEL_ID = int(os.getenv("NOTIFY_CHANNEL_ID"))

CHOOSE_PROJECT, GET_DESCRIPTION = range(2)

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Оставить запрос", callback_data="leave_request")]]
    await update.message.reply_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))

async def leave_request_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("Декада", callback_data="Декада")],
        [InlineKeyboardButton("ЗТЧ", callback_data="ЗТЧ")],
        [InlineKeyboardButton("Броктон", callback_data="Броктон")],
    ]
    await query.edit_message_text("Выберите проект:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSE_PROJECT

async def choose_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    project = query.data
    context.user_data["project"] = project
    await query.answer()
    await query.edit_message_text(f"Вы выбрали: {project}\n\nВведите описание запроса:")
    return GET_DESCRIPTION

async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    project = context.user_data["project"]
    description = update.message.text
    now = int(time.time())
    now_ms = now * 1000
    title = f"{project}_{now}"

    data = {
        "title": title,
        "columnId": COLUMN_ID,
        "description": description,
        "assigned": ASSIGNED_USER_IDS,
        "deadline": {
            "deadline": now_ms,
            "startDate": now_ms,
            "withTime": True,
            "history": [],
            "blockedPoints": [],
            "links": []
        }
    }

    headers = {
        "Authorization": f"Bearer {YOUGILE_API_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post("https://ru.yougile.com/api-v2/tasks", json=data, headers=headers)

    if response.status_code == 201:
        title = data["title"]
        await update.message.reply_text(f"✅ Заявка {title} успешно зарегистрирована!")
        await context.bot.send_message(chat_id=NOTIFY_CHANNEL_ID, text=f"🆕 Новая заявка № {title} зарегистрирована")
    else:
        await update.message.reply_text(f"❌ Ошибка при отправке: {response.status_code}\n{response.text}")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(leave_request_callback, pattern="leave_request")],
        states={
            CHOOSE_PROJECT: [CallbackQueryHandler(choose_project)],
            GET_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
