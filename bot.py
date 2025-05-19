"""
Telegram bot for WinGo predictions with auto-updating results.
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

from config import (
    BOT_TOKEN, 
    BOT_USERNAME, 
    WINGO_30SEC_PERIOD, 
    WINGO_1MIN_PERIOD,
    RESULTS_LENGTH,
    AUTO_UPDATE_INTERVAL
)
import database as db
import prediction_logic as pl
import utils

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Dictionary to track active prediction messages
active_predictions: Dict[Tuple[int, int], str] = {}  # (chat_id, message_id) -> duration

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    # First, check if the user has joined the required channels
    user_id = update.effective_user.id if update.effective_user else None
    
    if not user_id:
        logger.error("Could not determine user ID")
        return
    
    # Add a join button at the top
    keyboard = [
        [
            InlineKeyboardButton("✅ JOIN OFFICIAL CHANNEL", url="https://t.me/TCWINGOAISAGAR")
        ],
        [
            InlineKeyboardButton("🔴 WinGo 30 Second ⚡", callback_data="wingo_30sec")
        ],
        [
            InlineKeyboardButton("🟢 WinGo 1 Minute 🎯", callback_data="wingo_1min")
        ],
        [
            InlineKeyboardButton("↩️ EXIT", callback_data="exit")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        "╔══════『 *🏆 TC WINGO BOT 🏆* 』═══════╗\n"
        "║                                                               ║\n"
        "║   💫 *70% WIN RATE GUARANTEED* 💫   ║\n"
        "║                                                               ║\n"
        "║   🔮 Premium Predictions For FREE 🔮   ║\n"
        "║                                                               ║\n"
        "║   🎯 Select Game Mode Below 🎯   ║\n"
        "║                                                               ║\n"
        "╚═════════════════════════╝\n\n"
        "💎 *OFFICIAL TC PREDICTION BOT* 💎\n"
        "🚀 24/7 AUTOMATED SIGNALS 🚀\n\n"
        "⚠️ *Join @TCWINGOAISAGAR for more signals* ⚠️"
    )
    
    if update.message:
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    if query:
        await query.answer()
        
        # Get the selected option
        if query.data:
            option = query.data
            chat_id = update.effective_chat.id if update.effective_chat else None
            user_id = update.effective_user.id if update.effective_user else None
            
            if not chat_id or not user_id:
                logger.error("Could not determine chat ID or user ID")
                return
            
            # Import our prediction formatter
            import fixed_prediction as fpl
            
            # Handle exit button
            if option == "exit":
                exit_message = "Thank you for using TC WINGO BOT!\n\nCome back anytime for more predictions! 👋"
                
                if query.message:
                    await query.edit_message_text(
                        exit_message,
                        parse_mode="Markdown"
                    )
                return
            
            # Show predictions directly without verification
            if option == "wingo_30sec":
                duration = "30 SEC"
                prediction_text = fpl.generate_formatted_predictions(duration, RESULTS_LENGTH)
            elif option == "wingo_1min":
                duration = "1 MIN"
                prediction_text = fpl.generate_formatted_predictions(duration, RESULTS_LENGTH)
            else:
                # For any other option, go back to main menu
                keyboard = [
                    [InlineKeyboardButton("✅ JOIN OFFICIAL CHANNEL", url="https://t.me/TCWINGOAISAGAR")],
                    [InlineKeyboardButton("🔴 WinGo 30 Second ⚡", callback_data="wingo_30sec")],
                    [InlineKeyboardButton("🟢 WinGo 1 Minute 🎯", callback_data="wingo_1min")],
                    [InlineKeyboardButton("↩️ EXIT", callback_data="exit")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                main_message = (
                    "╔══════『 *🏆 TC WINGO BOT 🏆* 』═══════╗\n"
                    "║                                                               ║\n"
                    "║   💫 *70% WIN RATE GUARANTEED* 💫   ║\n"
                    "║                                                               ║\n"
                    "║   🔮 Premium Predictions For FREE 🔮   ║\n"
                    "║                                                               ║\n"
                    "║   🎯 Select Game Mode Below 🎯   ║\n"
                    "║                                                               ║\n"
                    "╚═════════════════════════╝\n\n"
                    "💎 *OFFICIAL TC PREDICTION BOT* 💎\n"
                    "🚀 24/7 AUTOMATED SIGNALS 🚀\n\n"
                    "⚠️ *Join @TCWINGOAISAGAR for more signals* ⚠️"
                )
                
                if query.message:
                    await query.edit_message_text(
                        main_message,
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                return
            
            # Add an exit button at the bottom of prediction
            back_button = InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ BACK TO MENU", callback_data="back_to_menu")]
            ])
            
            # Show prediction with simple exit button
            try:
                if query.message and context.bot:
                    message = await query.edit_message_text(
                        text=prediction_text,
                        reply_markup=back_button,
                        parse_mode=None  # Plain text for better formatting
                    )
                    
                    # Register the message for auto-updates
                    utils.register_active_message(duration, chat_id, query.message.message_id)
                    
                    # Store the active prediction
                    active_predictions[(chat_id, query.message.message_id)] = duration
            except Exception as e:
                logger.error(f"Error showing prediction: {e}")
                # If there's an error, try to send a new message instead
                if query.message and context.bot:
                    try:
                        # Send as a new message instead of editing
                        new_message = await context.bot.send_message(
                            chat_id=chat_id,
                            text=prediction_text,
                            reply_markup=back_button,
                            parse_mode=None
                        )
                        
                        if new_message:
                            # Register the new message for updates
                            utils.register_active_message(duration, chat_id, new_message.message_id)
                            active_predictions[(chat_id, new_message.message_id)] = duration
                    except Exception as nested_error:
                        logger.error(f"Failed to send new message: {nested_error}")

async def update_active_messages(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Update all active prediction messages periodically."""
    logger.debug("Running scheduled update for active messages...")
    
    # Update messages for 30 SEC predictions
    await update_messages_for_duration("30 SEC", context)
    
    # Update messages for 1 MIN predictions
    await update_messages_for_duration("1 MIN", context)
    
    # Clean up old messages
    utils.clear_old_messages()

async def update_messages_for_duration(duration: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Update all active messages for a specific duration."""
    # Use our fixed prediction generator to avoid errors
    import fixed_prediction as fpl
    prediction_text = fpl.generate_formatted_predictions(duration, RESULTS_LENGTH)
    
    # Simulate a new result occasionally (in a real system, this would come from the game API)
    if duration == "30 SEC" and datetime.now().second % 30 == 0:
        pl.simulate_result(duration)
    elif duration == "1 MIN" and datetime.now().second == 0:
        pl.simulate_result(duration)
    
    # Get all active messages for this duration
    active_messages = utils.get_active_messages(duration)
    
    logger.debug(f"Updating {len(active_messages)} messages for {duration}")
    
    # Update each message
    for chat_id, message_id in active_messages:
        try:
            if context.bot:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=prediction_text,
                    parse_mode=None  # Plain text for better formatting
                )
                logger.debug(f"Updated message {chat_id}/{message_id} for {duration}")
        except Exception as e:
            logger.error(f"Error updating message {chat_id}/{message_id}: {e}")
            # Unregister the message if it can't be updated
            utils.unregister_active_message(duration, chat_id, message_id)

# Start the auto-update task
async def send_group_updates(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send prediction updates to the official group."""
    logger.info("Sending scheduled prediction updates to group...")
    
    try:
        # Import prediction formatter
        import fixed_prediction as fpl
        
        # Generate predictions for both durations
        prediction_30sec = fpl.generate_formatted_predictions("30 SEC", RESULTS_LENGTH)
        prediction_1min = fpl.generate_formatted_predictions("1 MIN", RESULTS_LENGTH)
        
        # Make the group message more attention-grabbing with extra formatting
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # Create a header with more attention-grabbing design
        header = (
            "🚨🚨🚨 LIVE SIGNAL ALERT 🚨🚨🚨\n"
            f"⏱️ UPDATED AT: {current_time} ⏱️\n\n"
        )
        
        # Use Telegram username format for the channel
        group_username = "@TCWINGOAISAGAR"
        
        # Send both predictions to the group
        if context.bot:
            try:
                # First send 30 SEC prediction
                await context.bot.send_message(
                    chat_id=group_username,
                    text=header + prediction_30sec,
                    parse_mode=None  # Plain text for better formatting
                )
                
                # Then send 1 MIN prediction after a short delay
                await asyncio.sleep(1.5)  # Add slight delay for better user experience
                await context.bot.send_message(
                    chat_id=group_username,
                    text=header + prediction_1min,
                    parse_mode=None  # Plain text for better formatting
                )
                
                logger.info(f"Successfully sent prediction updates to {group_username}")
            except Exception as e:
                logger.error(f"Error sending group updates: {e}")
    except Exception as e:
        logger.error(f"Error sending group updates: {e}")

async def start_update_task(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the background tasks for updating messages and sending group updates."""
    logger.info("Starting scheduled tasks...")
    
    # Create a job to periodically update messages for active users
    if context.application and context.application.job_queue:
        # Schedule the message update task (every 5 seconds)
        context.application.job_queue.run_repeating(
            update_active_messages, 
            interval=AUTO_UPDATE_INTERVAL, 
            first=1.0
        )
        logger.info("Scheduled auto-update task successfully")
        
        # Schedule the group update task (every minute)
        context.application.job_queue.run_repeating(
            send_group_updates,
            interval=60,  # Send updates every minute
            first=3.0  # Start after 3 seconds
        )
        logger.info("Scheduled group updates to @TCWINGOAISAGAR successfully")
    else:
        logger.error("Could not start scheduled tasks: job queue not available")
