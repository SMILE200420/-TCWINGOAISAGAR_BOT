"""
Utility functions for the Telegram bot.
"""
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
import logging
import asyncio

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Active prediction messages that need to be updated
active_messages: Dict[str, List[Tuple[int, int]]] = {
    "30 SEC": [],
    "1 MIN": []
}

def register_active_message(duration: str, chat_id: int, message_id: int) -> None:
    """Register a message for auto-updates."""
    active_messages[duration].append((chat_id, message_id))
    logger.debug(f"Registered active message for {duration}: {chat_id}, {message_id}")
    logger.debug(f"Current active messages: {active_messages}")

def unregister_active_message(duration: str, chat_id: int, message_id: int) -> None:
    """Unregister a message from auto-updates."""
    if (chat_id, message_id) in active_messages[duration]:
        active_messages[duration].remove((chat_id, message_id))
        logger.debug(f"Unregistered message for {duration}: {chat_id}, {message_id}")

def get_active_messages(duration: str) -> List[Tuple[int, int]]:
    """Get all active messages for a specific duration."""
    return active_messages[duration]

def clear_old_messages(max_age_minutes: int = 30) -> None:
    """Clear messages that are older than the specified age."""
    # Note: In a real implementation, you would track message creation time
    # For this example, we're just limiting the number of active messages
    
    max_messages = 20  # Maximum number of active messages per duration
    
    for duration in active_messages:
        if len(active_messages[duration]) > max_messages:
            # Keep only the most recent messages
            active_messages[duration] = active_messages[duration][-max_messages:]
            logger.debug(f"Cleared old messages for {duration}, now tracking {len(active_messages[duration])}")
