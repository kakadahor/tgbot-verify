"""Admin command handler"""
import asyncio
import logging
from datetime import datetime
import re

from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_USER_ID, ADMIN_IDS, ABA_NOTIFICATION_GROUP_ID, GEM_RATE
from database.base import Database
from utils.checks import reject_group_command
from utils.messages import get_deposit_notification, get_rejection_notification

logger = logging.getLogger(__name__)


async def approve_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Admin approve command by replying to a proof photo: /approve <user_id> <trx_id> <amount>"""
    # Check if admin
    if update.effective_user.id not in ADMIN_IDS:
        return

    # Must be in the admin group
    if update.effective_chat.id != ABA_NOTIFICATION_GROUP_ID:
        return

    # Check if it's a reply
    reply_to = update.message.reply_to_message
    if not reply_to:
        await update.message.reply_text("❌ Please use this command by replying to a payment proof photo.")
        return

    # Parse parameters: /approve <user_id> <trx_id> <amount>
    args = context.args
    if not args:
        await update.message.reply_text("❌ Usage: `/approve <user_id> <trx_id> <amount>`", parse_mode="Markdown")
        return

    try:
        target_user_id = None
        trx_id = None
        amount_usd = 0.0
        transaction_at = None
        chat_url = None

        # 1. Capture Chat URL from reply ALWAYS
        if reply_to:
            try:
                chat_id_str = str(reply_to.chat_id)
                thread_id = reply_to.message_thread_id if reply_to.is_topic_message else None
                
                if chat_id_str.startswith("-100"):
                    # Supergroup
                    chat_id_short = chat_id_str[4:]
                    if thread_id:
                        chat_url = f"https://t.me/c/{chat_id_short}/{thread_id}/{reply_to.message_id}"
                    else:
                        chat_url = f"https://t.me/c/{chat_id_short}/{reply_to.message_id}"
                elif reply_to.chat.username:
                    # Public channel/group
                    username = reply_to.chat.username
                    if thread_id:
                        chat_url = f"https://t.me/{username}/{thread_id}/{reply_to.message_id}"
                    else:
                        chat_url = f"https://t.me/{username}/{reply_to.message_id}"
                else:
                    # Basic Group - Use tg:// deep link
                    chat_url = f"tg://msg?chat_id={reply_to.chat_id}&message_id={reply_to.message_id}"
            except Exception as e:
                logger.warning(f"Failed to generate chat link: {e}")

        # 2. Parse Args: 
        # Case A: /approve <user_id> <amount> (2 args) -> trx_id = chat_url
        # Case B: /approve <user_id> <trx_id> <amount> (3 args)
        
        if len(args) == 2:
            try: 
                target_user_id = int(args[0])
                amount_usd = float(args[1])
                trx_id = "" # Keep blank as requested
            except:
                await update.message.reply_text("❌ Invalid format. Use: `/approve <user_id> <amount>`")
                return
        elif len(args) >= 3:
            try:
                target_user_id = int(args[0])
                if args[1].lower() in ["chat_link", "manual", "none", "-"]:
                    trx_id = ""
                else:
                    trx_id = args[1]
                amount_usd = float(args[2])
            except:
                await update.message.reply_text("❌ Invalid format. Use: `/approve <user_id> <trx_id> <amount>`")
                return
        else:
            await update.message.reply_text("❌ Missing arguments. Use:\n• `/approve <user_id> <amount>`\n• `/approve <user_id> <trx_id> <amount>`")
            return

        # 3. Extraction fallbacks (if args failed but IDs exist in message)
        if not target_user_id:
            caption = reply_to.caption or reply_to.text or ""
            id_match = re.search(r"(?:🆔|👤|User\s*ID:?)\s*`?(\d+)`?", caption, re.IGNORECASE)
            if id_match:
                target_user_id = int(id_match.group(1))
            elif not reply_to.from_user.is_bot:
                target_user_id = reply_to.from_user.id

        if not target_user_id:
            await update.message.reply_text("❌ Could not determine User ID. Please specify it correctly.")
            return

        if amount_usd <= 0:
            await update.message.reply_text("❌ Invalid amount.")
            return

        gems_to_add = int(amount_usd * GEM_RATE)
        
        # Prepare metadata 
        metadata = {
            'trx_id': trx_id or "Manual",
            'chat_link': chat_url,
            'manual': True
        }

        display_trx = trx_id if trx_id else "Manual Approval"
        if db.add_balance(target_user_id, gems_to_add, description=f"Top-up ({display_trx})", metadata=metadata, transaction_at=transaction_at, txn_type='topup'):
            from config import ENVIRONMENT
            env_pref = "⚠️ **TEST MODE**\n" if ENVIRONMENT != "production" else ""
            
            await update.message.reply_text(
                f"{env_pref}"
                f"✅ **Deposit Approved!**\n"
                f"👤 **User ID:** `{target_user_id}`\n"
                f"💎 **Added:** `{gems_to_add} Gems` ($`{amount_usd:.2f}`)\n"
                f"🆔 **Bank Trx:** `{trx_id}`\n"
                f"🔗 **Chat Link:** [View Proof]({chat_url})" if chat_url else "",
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            
            # Notify the user
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=get_deposit_notification(amount_usd, gems_to_add, trx_id),
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Failed to notify user {target_user_id}: {e}")
        else:
            await update.message.reply_text("❌ Failed to add Gems. Please check if User ID is still valid.")
            
    except ValueError:
        await update.message.reply_text("❌ Invalid input. Use numbers for amount and user ID.")
    except Exception as e:
        logger.error(f"Error in approve command: {e}")
        await update.message.reply_text(f"❌ An error occurred: {e}")
    return


async def reject_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Admin reject command by replying to a proof message"""
    # Check if admin
    if update.effective_user.id not in ADMIN_IDS:
        return

    # Must be in the admin group
    if update.effective_chat.id != ABA_NOTIFICATION_GROUP_ID:
        return

    # Check if it's a reply
    reply_to = update.message.reply_to_message
    if not reply_to:
        await update.message.reply_text("❌ Please use this command by replying to a payment proof.")
        return

    # Parse reason from args
    reason = " ".join(context.args) if context.args else None
    
    # Try to extract User ID from reply
    target_user_id = None
    caption = reply_to.caption or reply_to.text or ""
    
    # Search for User ID with 🆔 or 👤 or "User ID:"
    id_match = re.search(r"(?:🆔|👤|User\s*ID:?)\s*`?(\d+)`?", caption, re.IGNORECASE)
    if id_match:
        target_user_id = int(id_match.group(1))
    
    # If still nothing, check if the reply is a message FROM a user
    if not target_user_id and not reply_to.from_user.is_bot:
        target_user_id = reply_to.from_user.id

    if not target_user_id:
        await update.message.reply_text("❌ Could not determine User ID. Please specify it manually if needed.")
        return

    # Notify the user
    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=get_rejection_notification(reason),
            parse_mode="Markdown"
        )
        # Notify the Admin Group
        await update.message.reply_text(
            f"🚫 **Payment Rejected**\n"
            f"👤 **User ID:** `{target_user_id}`\n"
            f"📝 **Reason:** `{reason if reason else 'No reason provided'}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Failed to notify user {target_user_id} of rejection: {e}")
        await update.message.reply_text(f"❌ User notification failed, but rejection acknowledged locally. Error: {e}")


async def addgems_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /addgems command - Admin adds Gems"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /addgems <User_ID> <Amount>\n\nExample: /addgems 123456789 10"
        )
        return

    try:
        target_user_id = int(context.args[0])
        gems_to_add = int(context.args[1])
        
        # Capture Chat URL if it's a reply
        reply_to = update.message.reply_to_message
        chat_url = None
        if reply_to:
            try:
                chat_id_str = str(reply_to.chat_id)
                thread_id = reply_to.message_thread_id if reply_to.is_topic_message else None
                
                if chat_id_str.startswith("-100"):
                    # Supergroup
                    chat_id_short = chat_id_str[4:]
                    if thread_id:
                        chat_url = f"https://t.me/c/{chat_id_short}/{thread_id}/{reply_to.message_id}"
                    else:
                        chat_url = f"https://t.me/c/{chat_id_short}/{reply_to.message_id}"
                elif reply_to.chat.username:
                    # Public channel/group
                    username = reply_to.chat.username
                    if thread_id:
                        chat_url = f"https://t.me/{username}/{thread_id}/{reply_to.message_id}"
                    else:
                        chat_url = f"https://t.me/{username}/{reply_to.message_id}"
                else:
                    # Basic Group - Use tg:// deep link
                    chat_url = f"tg://msg?chat_id={reply_to.chat_id}&message_id={reply_to.message_id}"
            except Exception as e:
                logger.warning(f"Failed to generate chat link in addgems: {e}")

        # Optional Trx ID and Time
        trx_id = context.args[2] if len(context.args) > 2 else f"MANUAL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        transaction_at = None
        if len(context.args) > 3:
            try: transaction_at = datetime.fromisoformat(context.args[3])
            except: pass

        if not db.user_exists(target_user_id):
            await update.message.reply_text("User does not exist.")
            return

        metadata = {
            'trx_id': trx_id,
            'chat_link': chat_url,
            'manual': True
        }

        if db.add_balance(target_user_id, gems_to_add, description=f"Admin Reward | ID: {trx_id}", metadata=metadata, transaction_at=transaction_at, txn_type='reward'):
            user = db.get_user(target_user_id)
            from config import ENVIRONMENT
            env_pref = "⚠️ **TEST MODE**\n" if ENVIRONMENT != "production" else ""
            
            await update.message.reply_text(
                f"{env_pref}"
                f"✅ **Successfully added {gems_to_add} Gems** for user `{target_user_id}`.\n"
                f"💰 **Balance:** `{user['balance']} Gems`\n"
                f"🆔 **Bank Trx:** `{trx_id}`\n"
                f"🔗 **Chat Link:** [View Proof]({chat_url})" if chat_url else "",
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            
            # Notify User with beautiful message
            try:
                amount_usd = gems_to_add / GEM_RATE
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=get_deposit_notification(amount_usd, gems_to_add, trx_id),
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Failed to notify user {target_user_id}: {e}")
        else:
            await update.message.reply_text("Operation failed. Please try again later.")
    except ValueError:
        await update.message.reply_text("Invalid parameter format. Please enter valid numbers.")


async def block_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /block command - Admin blacklists user"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /block <User_ID>\n\nExample: /block 123456789"
        )
        return

    try:
        target_user_id = int(context.args[0])

        if not db.user_exists(target_user_id):
            await update.message.reply_text("User does not exist.")
            return

        if db.block_user(target_user_id):
            await update.message.reply_text(f"✅ User {target_user_id} has been blacklisted.")
        else:
            await update.message.reply_text("Operation failed. Please try again later.")
    except ValueError:
        await update.message.reply_text("Invalid parameter format. Please enter a valid User ID.")


async def white_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /white command - Admin removes blacklist"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /white <User_ID>\n\nExample: /white 123456789"
        )
        return

    try:
        target_user_id = int(context.args[0])

        if not db.user_exists(target_user_id):
            await update.message.reply_text("User does not exist.")
            return

        if db.unblock_user(target_user_id):
            await update.message.reply_text(f"✅ User {target_user_id} has been removed from the blacklist.")
        else:
            await update.message.reply_text("Operation failed. Please try again later.")
    except ValueError:
        await update.message.reply_text("Invalid parameter format. Please enter a valid User ID.")


async def blacklist_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /blacklist command - View blacklist"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    blacklist = db.get_blacklist()

    if not blacklist:
        await update.message.reply_text("Blacklist is empty.")
        return

    msg = "📋 Blacklist:\n\n"
    for user in blacklist:
        msg += f"User ID: {user['user_id']}\n"
        msg += f"Username: @{user['username']}\n"
        msg += f"Full Name: {user['full_name']}\n"
        msg += "---\n"

    await update.message.reply_text(msg)


async def genkey_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /genkey command - Admin generates card key"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /genkey <key> <Gems> [uses] [expire_days]\n\n"
            "Example:\n"
            "/genkey test123 20 - Generate a 20-Gem key (1 use, no expiry)\n"
            "/genkey vip100 50 10 - Generate a 50-Gem key (10 uses, no expiry)\n"
            "/genkey temp 30 1 7 - Generate a 30-Gem key (1 use, expires in 7 days)"
        )
        return

    try:
        key_code = context.args[0].strip()
        balance = int(context.args[1])
        max_uses = int(context.args[2]) if len(context.args) > 2 else 1
        expire_days = int(context.args[3]) if len(context.args) > 3 else None

        if balance <= 0:
            await update.message.reply_text("Gems must be greater than 0.")
            return

        if max_uses <= 0:
            await update.message.reply_text("Uses must be greater than 0.")
            return

        if db.create_card_key(key_code, balance, user_id, max_uses, expire_days):
            msg = (
                "✅ Card key generated successfully!\n\n"
                f"Key: {key_code}\n"
                f"Gems: {balance}\n"
                f"Uses: {max_uses}\n"
            )
            if expire_days:
                msg += f"Expiry: {expire_days} days\n"
            else:
                msg += "Expiry: Never\n"
            msg += f"\nUser usage: /use {key_code}"
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("Key already exists or generation failed. Please try a different name.")
    except ValueError:
        await update.message.reply_text("Invalid parameter format. Please enter valid numbers.")


async def listkeys_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /listkeys command - Admin views card key list"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    keys = db.get_all_card_keys()

    if not keys:
        await update.message.reply_text("No card keys found.")
        return

    msg = "📋 Card Key List:\n\n"
    for key in keys[:20]:  # Show top 20
        msg += f"Key: {key['key_code']}\n"
        msg += f"Gems: {key['balance']}\n"
        msg += f"Uses: {key['current_uses']}/{key['max_uses']}\n"

        if key["expire_at"]:
            expire_time = datetime.fromisoformat(key["expire_at"])
            if datetime.now() > expire_time:
                msg += "Status: Expired\n"
            else:
                days_left = (expire_time - datetime.now()).days
                msg += f"Status: Valid ({days_left} days left)\n"
        else:
            msg += "Status: Permanent\n"

        msg += "---\n"

    if len(keys) > 20:
        msg += f"\n(Displaying top 20 out of {len(keys)})"

    await update.message.reply_text(msg)


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /broadcast command - Admin sends broadcast notification"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    text = " ".join(context.args).strip() if context.args else ""
    if not text and update.message.reply_to_message:
        text = update.message.reply_to_message.text or ""

    if not text:
        await update.message.reply_text("Usage: /broadcast <text>, or send /broadcast while replying to a message.")
        return

    user_ids = db.get_all_user_ids()
    success, failed = 0, 0

    status_msg = await update.message.reply_text(f"📢 Starting broadcast to {len(user_ids)} users...")

    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=uid, text=text)
            success += 1
            await asyncio.sleep(0.05)  # Moderate speed limiting to avoid triggering limits
        except Exception as e:
            logger.warning("Broadcast to %s failed: %s", uid, e)
            failed += 1

    await status_msg.edit_text(f"✅ Broadcast complete!\nSuccess: {success}\nFailed: {failed}")
