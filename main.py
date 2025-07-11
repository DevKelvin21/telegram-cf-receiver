import asyncio
from functions_framework import http

import pytz
import os
from google.cloud import pubsub_v1
import json

import logging

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    logger.info(f"Start command received from user {user.full_name} (ID: {user.id})")
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )
    logger.info(f"Start response sent to user {user.full_name}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    user = update.effective_user
    logger.info(f"Help command received from user {user.full_name} (ID: {user.id})")
    await update.message.reply_text("Help!")
    logger.info(f"Help response sent to user {user.full_name}")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    user = update.effective_user
    message_text = update.message.text
    logger.info(f"Echo message received from user {user.full_name} (ID: {user.id}): '{message_text[:50]}{'...' if len(message_text) > 50 else ''}'")
    await update.message.reply_text(update.message.text)
    logger.info(f"Echo response sent to user {user.full_name}")


async def main(request):
    logger.info(f"Received {request.method} request from {request.remote_addr}")
    
    token = os.environ.get('TELEGRAM_TOKEN')
    if not token:
        logger.error("TELEGRAM_TOKEN environment variable not set")
        return "Configuration error", 500
    
    app = Application.builder().token(token).build()
    bot = app.bot

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    if request.method == 'GET':
        webhook_url = f'https://{request.host}/bot_receiver'
        logger.info(f"Setting webhook to: {webhook_url}")
        try:
            await bot.set_webhook(webhook_url)
            logger.info("Webhook set successfully")
            return "webhook set"
        except Exception as e:
            logger.error(f"Failed to set webhook: {str(e)}")
            return f"Webhook error: {str(e)}", 500

    try:
        async with app:
            update = Update.de_json(request.json, bot)
            if update:
                logger.info(f"Processing update {update.update_id}")
                await app.process_update(update)
                logger.info(f"Update {update.update_id} processed successfully")
            else:
                logger.warning("Received empty or invalid update")
    except Exception as e:
        logger.error(f"Error processing update: {str(e)}")
        return f"Processing error: {str(e)}", 500

    return "ok"

@http
def bot_receiver(request):
    logger.info("Cloud Function invoked")
    try:
        result = asyncio.run(main(request))
        logger.info("Cloud Function completed successfully")
        return result
    except Exception as e:
        logger.error(f"Cloud Function error: {str(e)}")
        return f"Function error: {str(e)}", 500