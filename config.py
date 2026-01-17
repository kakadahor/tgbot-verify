"""Global Configuration File"""
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Environment Support FIRST (needed for token)
ENVIRONMENT = os.getenv("ENVIRONMENT", "development") # "production" or "development"

# Telegram Bot Configuration
if ENVIRONMENT == "development":
    # Use Test bot if available, otherwise fallback
    BOT_TOKEN = os.getenv("TEST_BOT_TOKEN") or os.getenv("BOT_TOKEN")
else:
    # Always use Prod token in production
    BOT_TOKEN = os.getenv("BOT_TOKEN")

CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "")
CHANNEL_URL = os.getenv("CHANNEL_URL", "")

# 管理员配置 (Safe integer conversion)
try:
    ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "123456789"))
except (ValueError, TypeError):
    print("BOOTSTRAP WARNING: ADMIN_USER_ID is not a valid integer. Using default.")
    ADMIN_USER_ID = 123456789

ADMIN_IDS = [ADMIN_USER_ID]
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "kakada66")
ADMIN_SUPPORT_LINK = f"https://t.me/{ADMIN_USERNAME}"

# Gem Configuration
SERVICE_COSTS = {
    "gemini_one_pro": 5,        # /verify
    "chatgpt_teacher_k12": 5,    # /verify2
    "spotify_student": 4,       # /verify3
    "bolt_teacher": 5,          # /verify4
    "youtube_student": 4,       # /verify5
}
VERIFY_COST = 5  # Default/Fallback cost
CHECKIN_REWARD = 1  # Gems rewarded for check-in
INVITE_REWARD = 2  # Gems rewarded for inviting
REGISTER_REWARD = 1  # Gems rewarded for registration
GEM_RATE = 10  # 1 USD = 10 Gems

# Automation & Topup
# Automation & Topup
ABA_NOTIFICATION_GROUP_ID = -1003490347596  # Group ID where PayWay notifications arrive
ADMIN_TOPIC_ID = 28  # Topic/Thread ID for payments if group is forum-enabled

# File Paths (Relative to project root for Cloud Run compatibility)
ABA_QR_PATH_LIVE = os.getenv("ABA_QR_PATH_LIVE", "assets/aba_live.jpg")
ABA_QR_PATH_TEST = os.getenv("ABA_QR_PATH_TEST", "assets/aba_test.jpg")
BINANCE_QR_PATH = os.getenv("BINANCE_QR_PATH", "assets/binance_usdt.jpg")

ABA_PAYMENT_LINK_LIVE = "https://link.payway.com.kh/ABAPAYc0407873p"
ABA_PAYMENT_LINK_TEST = "https://link.payway.com.kh/ABAPAYKJ407872V"

if ENVIRONMENT == "production":
    # In production, prioritize ENV variables or falls back to relative assets
    ABA_QR_PATH = ABA_QR_PATH_LIVE
    ABA_PAYMENT_LINK = ABA_PAYMENT_LINK_LIVE
else:
    ABA_QR_PATH = ABA_QR_PATH_TEST
    ABA_PAYMENT_LINK = ABA_PAYMENT_LINK_TEST

# Features
RATE_LIMIT_DELAY = 1.5  # Seconds between messages
MAINTENANCE_MODE = False
MAINTENANCE_REASON = "System upgrade in progress. Please check back later."

# Help Link
HELP_NOTION_URL = "https://rhetorical-era-3f3.notion.site/dd78531dbac745af9bbac156b51da9cc"

# Multi-Environment Support (Logic moved to top for early config)
# ENVIRONMENT variable is already handled above

# Collection Names based on Environment
if ENVIRONMENT == "production":
    FS_COLLECTIONS = {
        'users': 'users',
        'verifications': 'verifications',
        'card_keys': 'card_keys',
        'card_key_usage': 'card_key_usage',
        'invitations': 'invitations',
        'ledger': 'ledger'
    }
else:
    FS_COLLECTIONS = {
        'users': 'users_dev',
        'verifications': 'verifications_dev',
        'card_keys': 'card_keys_dev',
        'card_key_usage': 'card_key_usage_dev',
        'invitations': 'invitations_dev',
        'ledger': 'ledger_dev'
    }
