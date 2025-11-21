
import json
import os
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

DATA_FILE = "reminders.json"

# ---------------- Работа с файлом ----------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ---------------- Отправка напоминания ----------------
async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    text = job.data
    await context.bot.send_message(chat_id=chat_id, text=text)

# ---------------- Команды бота ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот-напоминалка.\n"
        "Команды:\n"
        "/set 22:00 Текст — добавить напоминание\n"
        "/list — список напоминаний\n"
        "/remove 22:00 — удалить напоминание"
    )

async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Использование: /set 22:00 текст")
        return

    time_str = context.args[0]
    text = " ".join(context.args[1:])
    chat_id = str(update.effective_chat.id)

    # Сохраняем в файл
    data = load_data()
    if chat_id not in data:
        data[chat_id] = {}
    data[chat_id][time_str] = text
    save_data(data)

    # Ставим напоминание в JobQueue
    schedule_job(context, chat_id, time_str, text)

    await update.message.reply_text(f"Напоминание добавлено: {time_str} — {text}")

async def list_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    chat_id = str(update.effective_chat.id)
    if chat_id not in data or not data[chat_id]:
        await update.message.reply_text("Нет напоминаний.")
        return

    msg = "Ваши напоминания:\n"
    for t, text in data[chat_id].items():
        msg += f"▪️ {t} — {text}\n"
    await update.message.reply_text(msg)

async def remove_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Использование: /remove 22:00")
        return

    time_str = context.args[0]
    chat_id = str(update.effective_chat.id)
    data = load_data()
    if chat_id in data and time_str in data[chat_id]:
        del data[chat_id][time_str]
        save_data(data)

        # Удаляем задачу из JobQueue
        job_id = f"{chat_id}_{time_str}"
        current_jobs = context.job_queue.get_jobs_by_name(job_id)
        for job in current_jobs:
            job.schedule_removal()

        await update.message.reply_text(f"Удалено напоминание: {time_str}")
    else:
        await update.message.reply_text("Нет такого напоминания.")

# ---------------- Планирование задач ----------------
def schedule_job(context: ContextTypes.DEFAULT_TYPE, chat_id, time_str, text):
    hour, minute = map(int, time_str.split(":"))
    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target < now:
        target += timedelta(days=1)
    delay = (target - now).total_seconds()

    job_id = f"{chat_id}_{time_str}"
    context.job_queue.run_once(send_reminder, delay, chat_id=chat_id, data=text, name=job_id)

def schedule_saved_reminders(app):
    data = load_data()
    for chat_id, reminders in data.items():
        for time_str, text in reminders.items():
            schedule_job(app, chat_id, time_str, text)

# ---------------- Основная часть ----------------
app = ApplicationBuilder().token("8459007187:AAEbPSYgpiWBNwi4VnJMSHGm0ImhEdMIeDU").build()

# Добавляем обработчики команд
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("set", set_reminder))
app.add_handler(CommandHandler("list", list_reminders))
app.add_handler(CommandHandler("remove", remove_reminder))

# Восстанавливаем напоминания при старте
schedule_saved_reminders(app)

# Запуск бота
app.run_polling()
