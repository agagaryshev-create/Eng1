import os
from gtts import gTTS
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8202889793:AAGl6vm4dMCyex1CrmNzVUTxG2wF6TiLADQ"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Отправь команду /say ТЕКСТ, и я пришлю озвучку."
    )

async def say(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Используй: /say ТЕКСТ")
        return

    text = " ".join(context.args)
    tts = gTTS(text=text, lang='en')
    filename = "output.mp3"
    tts.save(filename)

    # Отправка аудио пользователю
    await update.message.reply_audio(audio=open(filename, 'rb'))

    # Удаляем файл после отправки
    os.remove(filename)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("say", say))

    print("Бот запущен...")
    app.run_polling()
