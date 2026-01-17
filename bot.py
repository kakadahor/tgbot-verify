"""Telegram Bot Main Program"""
import logging
import os
import http.server
import socketserver
from functools import partial

from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from config import BOT_TOKEN
from database import get_database  # New database factory
from handlers.user_commands import (
    start_command,
    about_command,
    help_command,
    balance_command,
    me_command,
    topup_command,
    verify_receipt_command,
    checkin_command,
    invite_command,
    use_command,
    myjobs_command,
    lsgd_command,
    lang_command,
    guide_command,
    services_command,
    guide_callback_handler,
    guide_back_handler,
    topup_local_callback,
    topup_intl_callback,
    proof_command,
)
from handlers.verify_commands import (
    verify_command,
    verify2_command,
    verify3_command,
    verify4_command,
    getV4Code_command,
)
from handlers.admin_commands import (
    addgems_command,
    block_command,
    white_command,
    blacklist_command,
    genkey_command,
    listkeys_command,
    broadcast_command,
    approve_command,
    reject_command,
)
from handlers.payment_automation import aba_payment_handler, receipt_photo_handler
from telegram.ext import MessageHandler, filters

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def error_handler(update: object, context) -> None:
    """Global error handler - Send user-friendly messages instead of silent failures"""
    logger.exception("An exception occurred while handling update: %s", context.error, exc_info=context.error)
    
    # Try to notify the user about the error
    try:
        if update and hasattr(update, 'effective_message') and update.effective_message:
            error_message = (
                "⚠️ **Oops! Something went wrong**\n\n"
                "We encountered an unexpected error while processing your request.\n\n"
                "**What you can do:**\n"
                "• Try the command again in a few moments\n"
                "• If the issue persists, please contact support\n\n"
                "We apologize for the inconvenience!"
            )
            
            # Add specific error info for admins
            from config import ADMIN_IDS
            if update.effective_user and update.effective_user.id in ADMIN_IDS:
                error_type = type(context.error).__name__
                error_message += f"\n\n🔧 **Admin Info:**\n`{error_type}: {str(context.error)[:100]}`"
            
            await update.effective_message.reply_text(
                error_message,
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Failed to send error message to user: {e}")


def main():
    """Main function"""
    # Initialize database (automatically selects MySQL or Firestore based on DB_TYPE env variable)
    db = get_database()

    # Create application - Enable concurrent processing
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)  # Key: Enable concurrent processing of multiple commands
        .build()
    )

    # Register user commands (using partial to pass db parameter)
    application.add_handler(CommandHandler("start", partial(start_command, db=db)))
    application.add_handler(CommandHandler("about", partial(about_command, db=db)))
    application.add_handler(CommandHandler("help", partial(help_command, db=db)))
    application.add_handler(CommandHandler("me", partial(me_command, db=db)))
    application.add_handler(CommandHandler("topup", partial(topup_command, db=db)))
    # Crypto command removed as it's merged into topup, but keeping handler just in case of old links
    application.add_handler(CommandHandler("crypto", partial(topup_command, db=db))) 
    application.add_handler(CommandHandler("proof", partial(proof_command, db=db))) 
    application.add_handler(CommandHandler("verify_receipt", partial(verify_receipt_command, db=db)))
    application.add_handler(CommandHandler("balance", partial(balance_command, db=db)))
    application.add_handler(CommandHandler("checkin", partial(checkin_command, db=db)))
    application.add_handler(CommandHandler("qd", partial(checkin_command, db=db)))
    application.add_handler(CommandHandler("invite", partial(invite_command, db=db)))
    application.add_handler(CommandHandler("use", partial(use_command, db=db)))
    application.add_handler(CommandHandler("myjobs", partial(myjobs_command, db=db)))
    application.add_handler(CommandHandler("lsgd", partial(lsgd_command, db=db)))
    application.add_handler(CommandHandler("lang", partial(lang_command, db=db)))
    application.add_handler(CommandHandler("hdsd", partial(guide_command, db=db)))
    application.add_handler(CommandHandler("guide", partial(guide_command, db=db)))
    application.add_handler(CommandHandler("services", partial(services_command, db=db)))

    # Register verification commands
    application.add_handler(CommandHandler("verify", partial(verify_command, db=db)))
    application.add_handler(CommandHandler("getV4Code", partial(getV4Code_command, db=db)))
    application.add_handler(CommandHandler("getv4code", partial(getV4Code_command, db=db)))  # Lowercase alias

    # Register admin commands
    application.add_handler(CommandHandler("addgems", partial(addgems_command, db=db)))
    application.add_handler(CommandHandler("block", partial(block_command, db=db)))
    application.add_handler(CommandHandler("white", partial(white_command, db=db)))
    application.add_handler(CommandHandler("blacklist", partial(blacklist_command, db=db)))
    application.add_handler(CommandHandler("genkey", partial(genkey_command, db=db)))
    application.add_handler(CommandHandler("listkeys", partial(listkeys_command, db=db)))
    application.add_handler(CommandHandler("broadcast", partial(broadcast_command, db=db)))
    application.add_handler(CommandHandler("approve", partial(approve_command, db=db)))
    application.add_handler(CommandHandler("reject", partial(reject_command, db=db)))

    # Register message handlers (Automation & Receipts)
    # Using a broader filter to ensure we catch linked channel posts in the supergroup
    payment_filter = (filters.TEXT | filters.CAPTION) & (~filters.COMMAND)
    application.add_handler(MessageHandler(payment_filter, partial(aba_payment_handler, db=db)))
    application.add_handler(MessageHandler(filters.PHOTO, partial(receipt_photo_handler, db=db)))

    # Register callback query handlers for interactive menus
    application.add_handler(CallbackQueryHandler(guide_callback_handler, pattern="^guide_(google_one|spotify|youtube|chatgpt|bolt|general)$"))
    application.add_handler(CallbackQueryHandler(guide_back_handler, pattern="^guide_back$"))
    application.add_handler(CallbackQueryHandler(topup_local_callback, pattern="^topup_local$"))
    application.add_handler(CallbackQueryHandler(topup_intl_callback, pattern="^topup_intl$"))

    # Set bot commands menu on startup
    async def post_init(application: Application) -> None:
        from telegram import BotCommand, BotCommandScopeChat
        from config import ADMIN_USER_ID, ABA_NOTIFICATION_GROUP_ID

        # 1. Commands for EVERYONE (Regular Users)
        user_commands = [
            BotCommand("start", "🚀 Start bot & Get Welcome Message"),
            BotCommand("about", "ℹ️ About this bot"),
            BotCommand("services", "💰 View Services & Pricing"),
            BotCommand("topup", "💎 Top-up Gems (ABA/USDT)"),
            BotCommand("verify", "✅ Start Account Verification"),
            BotCommand("getv4code", "🔑 Get V4 verification code"),
            BotCommand("proof", "📸 Submit Payment Screenshot"),
            BotCommand("me", "👤 My Profile & Balance"),
            BotCommand("balance", "💰 Check Gem Balance"),
            BotCommand("guide", "📖 How to use/buy guides"),
            BotCommand("myjobs", "📋 Check my verification status"),
            BotCommand("lsgd", "📜 Transaction History"),
            BotCommand("checkin", "🎁 Daily Reward (+1 Gem)"),
            BotCommand("invite", "👥 Earn Gems by inviting friends"),
            BotCommand("use", "🎟️ Redeem card key/voucher code"),
            BotCommand("lang", "🌐 Language Settings"),
            BotCommand("help", "❓ Get assistance"),
        ]
        from telegram import BotCommandScopeAllPrivateChats
        try:
            await application.bot.set_my_commands(user_commands, scope=BotCommandScopeAllPrivateChats())
        except Exception as e:
            logger.warning(f"Could not set default user commands: {e}")

        # 2. Commands for ADMIN (will show in the Private Chat with bot)
        admin_commands = user_commands + [
            BotCommand("addgems", "💰 [Admin] Add Gems to User"),
            BotCommand("approve", "✅ [Admin] Approve Payment"),
            BotCommand("reject", "❌ [Admin] Reject Payment"),
            BotCommand("block", "🚫 [Admin] Block User"),
            BotCommand("white", "✅ [Admin] Unblock User"),
            BotCommand("blacklist", "📋 [Admin] View Blacklist"),
            BotCommand("genkey", "� [Admin] Generate Card Key"),
            BotCommand("listkeys", "📜 [Admin] List All Card Keys"),
            BotCommand("broadcast", "�📣 [Admin] Send message to all"),
        ]
        try:
            await application.bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=ADMIN_USER_ID))
        except Exception as e:
            logger.warning(f"Could not set admin user commands: {e}")

        # 3. Commands for ADMIN GROUP (Fast for the admin group)
        group_commands = [
            BotCommand("approve", "✅ /approve <user_id> <amount> OR <user_id> <trx_id> <amount>"),
            BotCommand("reject", "❌ Reply to proof: /reject [reason]"),
            BotCommand("addgems", "💰 Add Gems: /addgems <id> <amount>"),
        ]
        try:
            await application.bot.set_my_commands(group_commands, scope=BotCommandScopeChat(chat_id=ABA_NOTIFICATION_GROUP_ID))
        except Exception as e:
            # This might fail if the ID is not correct or bot is not in group yet
            logger.warning(f"Could not set admin group commands: {e}")

    # Attach post_init hook
    application.post_init = post_init

    # Register error handler
    application.add_error_handler(error_handler)

    # Detect Environment
    PORT = int(os.environ.get("PORT", "8080"))
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
    IS_CLOUD = os.environ.get("K_SERVICE")  # Detected by Cloud Run

    if IS_CLOUD:
        # 🌩️ RUNNING IN CLOUD (WEBHOOK MODE)
        logger.info(f"Detected Cloud Run environment. Port: {PORT}")
        
        if not WEBHOOK_URL or "placeholder" in WEBHOOK_URL:
            # If the URL is missing, we start a simple server to pass health checks
            # so the service stays alive while the user fixes their settings.
            logger.warning("WEBHOOK_URL is missing. Starting safety health-check server.")
            
            class SafeHealthHandler(http.server.SimpleHTTPRequestHandler):
                def do_GET(self):
                    self.send_response(200)
                    self.send_header("Content-type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"Bot is live but pending WEBHOOK_URL configuration.")

            with socketserver.TCPServer(("0.0.0.0", PORT), SafeHealthHandler) as httpd:
                logger.info(f"Safety server listening on port {PORT}")
                httpd.serve_forever()
        else:
            # PRODUCTION WEBHOOK MODE
            logger.info(f"Starting bot in WEBHOOK mode on port {PORT}")
            try:
                application.run_webhook(
                    listen="0.0.0.0",
                    port=PORT,
                    url_path=BOT_TOKEN,
                    webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
                    drop_pending_updates=True
                )
            except Exception as e:
                logger.critical(f"FATAL: Bot failed to start in Webhook Mode: {e}", exc_info=True)
                raise
    else:
        # 💻 RUNNING LOCALLY (POLLING MODE)
        logger.info("Starting bot in LOCAL POLLING mode")
        application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Main loop crashed: {e}")
