import logging
import time
from functools import wraps
from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from config import CHANNEL_USERNAME, MAINTENANCE_MODE, MAINTENANCE_REASON, RATE_LIMIT_DELAY

logger = logging.getLogger(__name__)

# Global rate limit storage (user_id -> last_command_time)
_user_last_command_time = {}


def is_group_chat(update: Update) -> bool:
    """Check if it's a group chat"""
    chat = update.effective_chat
    return chat and chat.type in ("group", "supergroup")


async def reject_group_command(update: Update) -> bool:
    """Group chat limit: Only allow /verify series, unless in Admin Group for management"""
    if not is_group_chat(update):
        return False

    from config import ABA_NOTIFICATION_GROUP_ID, ADMIN_IDS
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    message_text = update.message.text or ""
    
    # Allowed public group commands
    allowed_group_commands = ("/verify", "/verify2", "/verify3", "/verify4", "/verify5", "/qd", "/getV4Code", "/getv4code", "/use")
    if any(message_text.startswith(cmd) for cmd in allowed_group_commands):
        return False

    # Commands specifically allowed in Admin Group (Admin only)
    if chat_id == ABA_NOTIFICATION_GROUP_ID and user_id in ADMIN_IDS:
        admin_group_commands = ("/addgems", "/ok", "/block", "/white")
        if any(message_text.startswith(cmd) for cmd in admin_group_commands):
            return False

    await update.message.reply_text(
        "❌ **Group Restriction**\n\n"
        "Standard commands are disabled in groups to maintain privacy.\n"
        "Please use this command in **Private Chat** with the bot.",
        parse_mode="Markdown"
    )
    return True


async def check_channel_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the user has joined the channel"""
    try:
        member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ["member", "administrator", "creator"]
    except TelegramError as e:
        logger.error("Failed to check channel membership: %s", e)
        return False


def global_checks(registration_required=True):
    """Decorator for global checks: Maintenance, Rate Limit, Blacklist, Registration"""
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            if not update.effective_user:
                return

            user_id = update.effective_user.id

            # 1. Maintenance Mode Check
            if MAINTENANCE_MODE:
                # Allow admin to bypass maintenance if needed
                from config import ADMIN_USER_ID
                if user_id != ADMIN_USER_ID:
                    await update.message.reply_text(f"🚧 **System Maintenance**\n\n{MAINTENANCE_REASON}", parse_mode="Markdown")
                    return

            # 2. Rate Limit Check (Global per-user 1.5s)
            now = time.time()
            last_time = _user_last_command_time.get(user_id, 0)
            if now - last_time < RATE_LIMIT_DELAY:
                # Optional: Send a warning or just ignore
                return 
            _user_last_command_time[user_id] = now

            # 3. Blacklist Check (if db is provided in args or kwargs)
            # This is a bit tricky since db is passed via partial
            db = kwargs.get('db')
            if not db and args:
                # Find db in args (Database instance)
                for arg in args:
                    if hasattr(arg, 'is_user_blocked'):
                        db = arg
                        break
            
            if db and db.is_user_blocked(user_id):
                await update.message.reply_text("❌ Your account is restricted. Please contact support.")
                return

            # 4. Registration Check
            if registration_required and db:
                if not db.user_exists(user_id):
                    await update.message.reply_text("Please register using /start first.")
                    return

            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator
