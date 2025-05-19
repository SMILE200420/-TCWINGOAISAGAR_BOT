"""
Main entry point for the Telegram bot application.
"""
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

import bot
from config import BOT_TOKEN

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main() -> None:
    """Start the bot."""
    logger.info("Starting TC WinGo AI Prediction Bot...")
    
    # Create and configure the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CallbackQueryHandler(bot.button_callback))
    
    # Schedule the update task to run periodically
    if application.job_queue:
        job = application.job_queue.run_repeating(
            bot.update_active_messages, 
            interval=5.0,  # Update every 5 seconds
            first=1.0      # Start after 1 second
        )
        logger.info("Scheduled auto-update task successfully")
    
    # Run the bot
    application.run_polling(allowed_updates=["message", "callback_query"])
    
    logger.info("Bot stopped.")

if __name__ == "__main__":
    main()
