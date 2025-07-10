import asyncio
from functions_framework import http
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import pytz
import os
from telegram import Update
from google.cloud import pubsub_v1
import json

@http
def telegram_bot(request):
    return asyncio.run(main(request))


async def main(request):
    token = os.environ.get('TELEGRAM_TOKEN')
    app = Application.builder().token(token).build()
    bot = app.bot

    app.add_handler(CommandHandler("start", on_start))
    app.add_handler(MessageHandler(filters.TEXT, on_message))

    if request.method == 'GET':
        await bot.set_webhook(f'https://{request.host}/telegram_receiver')
        return "webhook set"

    async with app:
        update = Update.de_json(request.json, bot)
        await app.process_update(update)

    return "ok"

# async def on_start(update: Update, context):
#     await context.bot.send_message(
#         chat_id=update.effective_chat.id,
#         text="Hola, soy tu bot de ventas y gastos para la floristería Morale's 🌸"
#     )

# async def on_message(update: Update, context):
    message = update.message
    chat_id = update.effective_chat.id
    print(f"Received message from chat {chat_id}: {message.text}")
    if not message:
        return

    el_salvador_tz = pytz.timezone("America/El_Salvador")
    local_timestamp = update.message.date.astimezone(el_salvador_tz)

    data = {
        "text": message.text,
        "chat_id": chat_id,
        "message_id": update.update_id,
        "user_name": update.effective_user.full_name,
        "timestamp": local_timestamp.isoformat(),
    }

    print (f"Publishing message to Pub/Sub: {data}")

    publisher = pubsub_v1.PublisherClient()
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    topic_path = publisher.topic_path(project_id, "telegram-transactions")
    publisher.publish(topic_path, json.dumps(data).encode("utf-8"))

    await context.bot.send_message(
        chat_id=chat_id,
        text="Tu mensaje ha sido recibido y procesado. Gracias por tu paciencia."
    )

async def on_start(update: Update, context):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Hello, I'm your first bot!"
    )


async def on_message(update: Update, context):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=update.message.text
    )