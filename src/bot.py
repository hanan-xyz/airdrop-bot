import logging
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ConversationHandler, TypeHandler
)
from src.config import Config
from src.handlers.conversation import *
from src.handlers.commands import help_command, backup_command, list_command
from src.sheets import GoogleSheetsClient
import time

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def limit_rate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    last_request = context.user_data.get('last_request', 0)
    if time.time() - last_request < Config.RATE_LIMIT_SECONDS:
        await update.message.reply_text(f"⏳ Tunggu {Config.RATE_LIMIT_SECONDS} detik")
        raise Application.handler_stop
    context.user_data['last_request'] = time.time()

def main() -> None:
    Config.validate()
    application = Application.builder().token(Config.BOT_TOKEN).build()
    sheets_client = GoogleSheetsClient()

    # Job harian untuk backup dan update status
    application.job_queue.run_daily(
        lambda ctx: sheets_client.backup(),
        time=time(hour=23, minute=59),
        days=tuple(range(7))
    )
    application.job_queue.run_daily(
        lambda ctx: sheets_client.update_status(),
        time=time(hour=0, minute=0),
        days=tuple(range(7))
    )

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAMA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_nama)],
            TWITTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_twitter)],
            DISCORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_discord)],
            TELEGRAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_telegram)],
            LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_link)],
            TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_type)],
            DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_deadline)],
            REWARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_reward)],
            NETWORK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_network)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        conversation_timeout=Config.CONVERSATION_TIMEOUT
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('backup', backup_command))
    application.add_handler(CommandHandler('list', list_command))
    application.add_handler(TypeHandler(Update, limit_rate), group=-1)

    logger.info("Bot dimulai")
    application.run_polling()

if __name__ == '__main__':
    main()
