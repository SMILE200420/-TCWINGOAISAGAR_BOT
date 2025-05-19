"""
Configuration settings for the Telegram bot.
"""
import os

# Telegram Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "6822520253:AAFscMRKG2H5h-NTnnC7tr4wE7w4GQ5GGsI")
BOT_USERNAME = "@TCWINGOAISAGAR_BOT"

# Database configuration
DATABASE_FILE = "wingo_database.sqlite"

# Prediction configuration
WINGO_30SEC_PERIOD = 30  # seconds
WINGO_1MIN_PERIOD = 60  # seconds
RESULTS_LENGTH = 10  # Number of results to display
AUTO_UPDATE_INTERVAL = 5  # How often to update messages (seconds)

# Promotional information
CONTACT_USER = "@Kaalsagar"
WEBSITE_URL = "https://47lottery.online/#/register?invitationCode=026321022444"

# Win rate configuration (70% win rate)
WIN_RATE = 0.7  # 70% win probability

# Channel and group settings
OFFICIAL_CHANNEL = "@TCWINGOAISAGAR"  # Official channel ID
OFFICIAL_GROUP_ID = "@TCWINGOAISAGAR"  # Group to send predictions to
GROUP_UPDATE_INTERVAL = 60  # Send updates to group every minute
