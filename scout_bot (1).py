import csv
import os
from datetime import datetime

from telegram import Update
from telegram.ext import (Application, CommandHandler, ConversationHandler,
                          MessageHandler, ContextTypes, filters)

# ============ НАСТРОЙКИ ============
TOKEN = "СЮДА_ВСТАВЬТЕ_ТОКЕН_ОТ_@BotFather"
SCOUT_CHAT_ID = 0  # ваш числовой chat_id (узнать: написать боту @userinfobot)
CSV_FILE = "candidates.csv"

QUESTIONS = [
    ("Как вас зовут? Как хотите, чтобы я к вам обращался?", "имя"),
    ("Сколько вам полных лет?", "возраст"),
    ("Из какого вы города?", "город"),
    ("Есть ли опыт работы моделью / стримов? Коротко опишите.", "опыт"),
    ("Какое оборудование есть? (камера, свет, микрофон, интернет)", "оборудование"),
    ("Какой график сможете вести? Например: вечер 18-24, ночной, свободный", "график"),
    ("Удобный способ связи: оставьте ник для связи, если не хотите через бота", "контакт"),
]

NAME, AGE, CITY, EXP, EQUIP, SCHED, CONTACT = range(7)


def save_row(data: dict):
    is_new = not os.path.exists(CSV_FILE)
    fields = ["date", "tg_id", "tg_username"] + [k for _, k in QUESTIONS]
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if is_new:
            w.writeheader()
        w.writerow(data)


# ============ СЦЕНАРИЙ ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Привет! Я бот скаутинга. 🌟\n"
        "Расскажу про работу и задам несколько коротких вопросов.\n"
        "На любом шаге напишите /cancel, чтобы остановиться."
    )
    await update.message.reply_text(QUESTIONS[0][0])
    return NAME


async def get_age(update, context):
    context.user_data["имя"] = update.message.text
    await update.message.reply_text(QUESTIONS[1][0])
    return AGE


async def get_city(update, context):
    context.user_data["возраст"] = update.message.text
    await update.message.reply_text(QUESTIONS[2][0])
    return CITY


async def get_exp(update, context):
    context.user_data["город"] = update.message.text
    await update.message.reply_text(QUESTIONS[3][0])
    return EXP


async def get_equip(update, context):
    context.user_data["опыт"] = update.message.text
    await update.message.reply_text(QUESTIONS[4][0])
    return EQUIP


async def get_sched(update, context):
    context.user_data["оборудование"] = update.message.text
    await update.message.reply_text(QUESTIONS[5][0])
    return SCHED


async def get_contact(update, context):
    context.user_data["график"] = update.message.text
    await update.message.reply_text(QUESTIONS[6][0])
    return CONTACT


async def finish(update, context):
    context.user_data["контакт"] = update.message.text
    u = update.effective_user
    data = {"date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "tg_id": u.id, "tg_username": u.username or "-"}
    data.update(context.user_data)
    save_row(data)

    summary = "\n".join("• {0}: {1}".format(k, data[k]) for _, k in QUESTIONS)
    username = data["tg_username"]
    tg_id = data["tg_id"]
    await update.message.reply_text(
        "Спасибо, анкета принята! ✅\n"
        "Я передал её скауту — он свяжется с вами лично в ближайшее время."
    )
    if SCOUT_CHAT_ID:
        try:
            await context.bot.send_message(
                SCOUT_CHAT_ID,
                "🆕 Новый кандидат!\n@" + username + " (id: " + str(tg_id) + ")\n\n" + summary,
            )
        except Exception:
            pass  # если SCOUT_CHAT_ID ещё не задан — просто пропускаем
    return ConversationHandler.END


async def cancel(update, context):
    await update.message.reply_text("Хорошо, остановились. Напишите /start, если передумаете.")
    return ConversationHandler.END


def main():
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_exp)],
            EXP: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_equip)],
            EQUIP: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_sched)],
            SCHED: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv)
    print("Бот запущен. Нажмите Ctrl+C для остановки.")
    app.run_polling()


if __name__ == "__main__":
    main()
