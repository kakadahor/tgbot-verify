print("BOOTSTRAP: Starting bot.py")
"""Telegram Bot Main Program"""
import logging
import os
import threading
import http.server
import socketserver
from functools import partial

from telegram.ext import Application, CommandHandler

from config import BOT_TOKEN
from database import get_database  # New database factory
from handlers.user_commands import (
    start_command,
    about_command,
    help_command,
    balance_command,
    checkin_command,
    invite_command,
    use_command,
)
from handlers.verify_commands import (
    verify_command,
    verify2_command,
    verify3_command,
    verify4_command,
    getV4Code_command,
)
from handlers.admin_commands import (
    addbalance_command,
    block_command,
    white_command,
    blacklist_command,
    genkey_command,
    listkeys_command,
    broadcast_command,
)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def error_handler(update: object, context) -> None:
    """Global error handler"""
    logger.exception("An exception occurred while handling update: %s", context.error, exc_info=context.error)


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
    application.add_handler(CommandHandler("balance", partial(balance_command, db=db)))
    application.add_handler(CommandHandler("qd", partial(checkin_command, db=db)))
    application.add_handler(CommandHandler("invite", partial(invite_command, db=db)))
    application.add_handler(CommandHandler("use", partial(use_command, db=db)))

    # Register verification commands
    application.add_handler(CommandHandler("verify", partial(verify_command, db=db)))
    application.add_handler(CommandHandler("verify2", partial(verify2_command, db=db)))
    application.add_handler(CommandHandler("verify3", partial(verify3_command, db=db)))
    application.add_handler(CommandHandler("verify4", partial(verify4_command, db=db)))
    application.add_handler(CommandHandler("getV4Code", partial(getV4Code_command, db=db)))

    # Register admin commands
    application.add_handler(CommandHandler("addbalance", partial(addbalance_command, db=db)))
    application.add_handler(CommandHandler("block", partial(block_command, db=db)))
    application.add_handler(CommandHandler("white", partial(white_command, db=db)))
    application.add_handler(CommandHandler("blacklist", partial(blacklist_command, db=db)))
    application.add_handler(CommandHandler("genkey", partial(genkey_command, db=db)))
    application.add_handler(CommandHandler("listkeys", partial(listkeys_command, db=db)))
    application.add_handler(CommandHandler("broadcast", partial(broadcast_command, db=db)))

    # Register error handler
    application.add_error_handler(error_handler)

    # Detect Environment
    PORT = int(os.environ.get("PORT", "8080"))
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
    IS_CLOUD = os.environ.get("K_SERVICE")  # Detected by Cloud Run

    if IS_CLOUD:
        # 🌩️ RUNNING IN CLOUD
        print(f"BOOTSTRAP: Cloud Run Detected. Port: {PORT}")
        
        if not WEBHOOK_URL or "placeholder.com" in WEBHOOK_URL:
            # FIRST RUN: We don't have a URL yet.
            # We must bind to the port to pass health checks, but we shouldn't 
            # try to start the Telegram Webhook yet because it will crash.
            print("BOOTSTRAP: No WEBHOOK_URL provided. Starting PASSIVE Health Check Server.")
            
            # Simple HTTP Handler to pass Google Cloud Health Check
            class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
                def do_GET(self):
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"Bot is waiting for WEBHOOK_URL configuration. Please set it in GitHub Secrets.")

            with socketserver.TCPServer(("0.0.0.0", PORT), HealthCheckHandler) as httpd:
                print(f"BOOTSTRAP: Health Check Server live on port {PORT}. Waiting for URL...")
                httpd.serve_forever()
        else:
            # SECOND RUN: We have the actual URL!
            logger.info(f"Starting bot in CLOUD mode on port {PORT}")
            try:
                application.run_webhook(
                    listen="0.0.0.0",
                    port=PORT,
                    url_path=BOT_TOKEN,
                    webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
                    drop_pending_updates=True
                )
            except Exception as e:
                logger.critical(f"FATAL: Bot failed to start in Cloud: {e}", exc_info=True)
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
