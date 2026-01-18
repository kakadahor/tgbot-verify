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

# System Settings
MAINTENANCE_MODE = os.getenv("MAINTENANCE_MODE", "False").lower() == "true"
MAINTENANCE_REASON = os.getenv("MAINTENANCE_REASON", "We are currently performing scheduled maintenance. Please check back later.")
RATE_LIMIT_DELAY = float(os.getenv("RATE_LIMIT_DELAY", "1.5"))

# 管理员配置 (Safe integer conversion)
try:
    ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "123456789"))
except (ValueError, TypeError):
    print("BOOTSTRAP WARNING: ADMIN_USER_ID is not a valid integer. Using default.")
    ADMIN_USER_ID = 123456789

ADMIN_IDS = [ADMIN_USER_ID]
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "kakada66")
ADMIN_SUPPORT_LINK = f"https://t.me/{ADMIN_USERNAME}"

# Database Configuration
DB_TYPE = os.getenv("DB_TYPE", "mysql")  # "mysql" or "firestore"

# MySQL Configuration
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "telegram_bot")

# Verification Cost
VERIFY_COST = 5  # Gems per verification

# ABA Payment Configuration - Multi-environment support
ABA_QR_PATH_LIVE = os.getenv("ABA_QR_PATH_LIVE", "assets/aba_live.jpg")
ABA_QR_PATH_TEST = os.getenv("ABA_QR_PATH_TEST", "assets/aba_test.jpg")

if ENVIRONMENT == "production":
    ABA_QR_PATH = ABA_QR_PATH_LIVE
else:
    ABA_QR_PATH = ABA_QR_PATH_TEST

# ABA Payment Link - Multi-environment support
ABA_PAYMENT_LINK_LIVE = os.getenv("ABA_PAYMENT_LINK_LIVE", "https://link.payway.com.kh/aba/kck001")
ABA_PAYMENT_LINK_TEST = os.getenv("ABA_PAYMENT_LINK_TEST", "https://link.payway.com.kh/aba/kck001test")

if ENVIRONMENT == "production":
    ABA_PAYMENT_LINK = ABA_PAYMENT_LINK_LIVE
else:
    ABA_PAYMENT_LINK = ABA_PAYMENT_LINK_TEST

# Binance USDT Configuration
BINANCE_QR_PATH = os.getenv("BINANCE_QR_PATH", "assets/binance_usdt.jpg")
BINANCE_WALLET_ADDRESS = os.getenv("BINANCE_WALLET_ADDRESS", "0x1234567890abcdef")

# Gem Rate
GEM_RATE = 10  # 1 USD = 10 Gems

# ABA Notification Group ID (for payment automation)
ABA_NOTIFICATION_GROUP_ID = int(os.getenv("ABA_NOTIFICATION_GROUP_ID", "-1003490347596"))
ADMIN_TOPIC_ID = int(os.getenv("ADMIN_TOPIC_ID", "2"))  # Default to topic ID 2

# Bot Username (for invite links)
BOT_USERNAME = os.getenv("BOT_USERNAME", "sheerid_verify_bot")

# Firestore Collections - Environment-specific
if ENVIRONMENT == "production":
    FS_COLLECTIONS = {
        'users': 'users',
        'verifications': 'verifications',
        'card_keys': 'card_keys',
        'card_key_usage': 'card_key_usage',
        'invitations': 'invitations',
        'ledger': 'ledger',
        'settings': 'settings'
    }
else:
    FS_COLLECTIONS = {
        'users': 'users_dev',
        'verifications': 'verifications_dev',
        'card_keys': 'card_keys_dev',
        'card_key_usage': 'card_key_usage_dev',
        'invitations': 'invitations_dev',
        'ledger': 'ledger_dev',
        'settings': 'settings_dev'
    }

# Referral System
INVITE_ALERT_THRESHOLD = int(os.getenv("INVITE_ALERT_THRESHOLD", "10"))  # Notify admin when user invites X people
INVITE_MILESTONE_REWARD = int(os.getenv("INVITE_MILESTONE_REWARD", "10"))  # Default reward gems

# Service-specific costs (in Gems)
SERVICE_COSTS = {
    'gemini_one_pro': 5,
    'chatgpt_teacher_k12': 5,
    'spotify_student': 4,
    'bolt_teacher': 5,
    'youtube_student': 4,
}
