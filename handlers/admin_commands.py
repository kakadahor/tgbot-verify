"""Admin command handler"""
import asyncio
import logging
from datetime import datetime
import re

from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_USER_ID, ADMIN_IDS, ADMIN_USERNAME, ABA_NOTIFICATION_GROUP_ID, GEM_RATE
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
            "Usage: /addgems <User_ID> <Amount> [Note]\n\n"
            "Examples:\n"
            "• /addgems 123456789 10\n"
            "• /addgems 123456789 10 Bonus reward for testing"
        )
        return

    try:
        target_user_id = int(context.args[0])
        gems_to_add = int(context.args[1])
        
        # Optional note (3rd argument onwards)
        note = " ".join(context.args[2:]) if len(context.args) > 2 else None
        
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

        # Generate transaction ID
        trx_id = f"MANUAL-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        if not db.user_exists(target_user_id):
            await update.message.reply_text("User does not exist.")
            return

        # Build description
        if note:
            description = f"Admin Reward: {note}"
        else:
            description = f"Admin Reward | ID: {trx_id}"

        metadata = {
            'trx_id': trx_id,
            'chat_link': chat_url,
            'manual': True,
            'note': note
        }

        if db.add_balance(target_user_id, gems_to_add, description=description, metadata=metadata, txn_type='reward'):
            user = db.get_user(target_user_id)
            from config import ENVIRONMENT
            env_pref = "⚠️ **TEST MODE**\n" if ENVIRONMENT != "production" else ""
            
            # Build message with conditional chat link to prevent empty message error
            success_msg = (
                f"{env_pref}"
                f"✅ **Successfully added {gems_to_add} Gems** for user `{target_user_id}`.\n"
                f"💰 **Balance:** `{user['balance']} Gems`\n"
            )
            
            if note:
                success_msg += f"📝 **Note:** {note}\n"
            
            success_msg += f"🆔 **Trx ID:** `{trx_id}`\n"
            
            if chat_url:
                success_msg += f"🔗 **Chat Link:** [View Proof]({chat_url})"
            
            await update.message.reply_text(
                success_msg,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            
            # Notify User with custom message if note provided
            try:
                if note:
                    # Custom notification with note
                    user_msg = (
                        f"💎 **Gems Added**\n\n"
                        f"**Amount:** +{gems_to_add} Gems\n"
                        f"**Note:** {note}\n"
                        f"**New Balance:** {user['balance']} Gems\n\n"
                        f"Thank you! 🎉"
                    )
                    await context.bot.send_message(
                        chat_id=target_user_id,
                        text=user_msg,
                        parse_mode="Markdown"
                    )
                else:
                    # Standard deposit notification
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


async def deductgems_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /deductgems command - Admin deducts Gems from user"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /deductgems <User_ID> <Amount> [Reason]\n\n"
            "Example: /deductgems 123456789 10 Refund processing"
        )
        return

    try:
        target_user_id = int(context.args[0])
        gems_to_deduct = int(context.args[1])
        reason = " ".join(context.args[2:]) if len(context.args) > 2 else "Admin deduction"

        if gems_to_deduct <= 0:
            await update.message.reply_text("Amount must be greater than 0.")
            return

        if not db.user_exists(target_user_id):
            await update.message.reply_text("User does not exist.")
            return

        # Check if user has enough balance
        user = db.get_user(target_user_id)
        if user['balance'] < gems_to_deduct:
            await update.message.reply_text(
                f"❌ Insufficient balance. User has `{user['balance']} Gems` but you're trying to deduct `{gems_to_deduct} Gems`.",
                parse_mode="Markdown"
            )
            return

        # Deduct gems
        metadata = {
            'admin_id': user_id,
            'reason': reason,
            'manual': True
        }

        if db.deduct_balance(target_user_id, gems_to_deduct, description=f"Admin Deduction: {reason}", metadata=metadata):
            user = db.get_user(target_user_id)
            from config import ENVIRONMENT
            env_pref = "⚠️ **TEST MODE**\n" if ENVIRONMENT != "production" else ""
            
            await update.message.reply_text(
                f"{env_pref}"
                f"✅ **Successfully deducted {gems_to_deduct} Gems** from user `{target_user_id}`.\n"
                f"💰 **New Balance:** `{user['balance']} Gems`\n"
                f"📝 **Reason:** {reason}",
                parse_mode="Markdown"
            )
            
            # Notify User
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=(
                        f"💎 **Gems Deducted**\n\n"
                        f"**Amount:** -{gems_to_deduct} Gems\n"
                        f"**Reason:** {reason}\n"
                        f"**New Balance:** {user['balance']} Gems\n\n"
                        f"If you have any questions, please contact [Admin](https://t.me/{ADMIN_USERNAME})."
                    ),
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


async def user_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /user command - View user details"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /user <User_ID>\n\nExample: /user 123456789"
        )
        return

    try:
        target_user_id = int(context.args[0])

        user = db.get_user(target_user_id)
        if not user:
            await update.message.reply_text(f"❌ User `{target_user_id}` does not exist.", parse_mode="Markdown")
            return

        # Format user details
        msg = "👤 **User Details**\n\n"
        msg += f"🆔 **User ID:** `{user['user_id']}`\n"
        msg += f"👨 **Username:** @{user['username'] or 'N/A'}\n"
        msg += f"📝 **Full Name:** {user['full_name'] or 'N/A'}\n"
        msg += f"💎 **Balance:** `{user['balance']} Gems`\n"
        
        # Account status
        status = "🚫 Blocked" if user.get('is_blocked') else "✅ Active"
        msg += f"📊 **Status:** {status}\n"
        
        # Registration date
        if user.get('created_at'):
            created_at = datetime.fromisoformat(user['created_at']) if isinstance(user['created_at'], str) else user['created_at']
            msg += f"📅 **Registered:** {created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        # Last check-in
        if user.get('last_checkin'):
            last_checkin = datetime.fromisoformat(user['last_checkin']) if isinstance(user['last_checkin'], str) else user['last_checkin']
            msg += f"🎯 **Last Check-in:** {last_checkin.strftime('%Y-%m-%d')}\n"
        else:
            msg += "🎯 **Last Check-in:** Never\n"
        
        # Invited by (with inviter's name)
        if user.get('invited_by'):
            inviter_id = user['invited_by']
            inviter = db.get_user(inviter_id)
            if inviter:
                inviter_name = inviter.get('full_name') or inviter.get('username') or 'Unknown'
                msg += f"🔗 **Invited By:** `{inviter_id}` ({inviter_name})\n"
            else:
                msg += f"🔗 **Invited By:** `{inviter_id}` (User not found)\n"
        else:
            msg += "🔗 **Invited By:** Direct signup\n"
        
        # Count invited users
        try:
            invited_count = db.get_invite_count(target_user_id)
            msg += f"👥 **Invited Users:** `{invited_count}` people\n"
        except Exception as e:
            logger.error(f"Error counting invited users: {e}")
            msg += "👥 **Invited Users:** Unable to fetch\n"

        await update.message.reply_text(msg, parse_mode="Markdown")

    except ValueError:
        await update.message.reply_text("❌ Invalid User ID format. Please enter a valid number.")
    except Exception as e:
        logger.error(f"Error in user command: {e}")
        await update.message.reply_text(f"❌ An error occurred: {e}")


async def usertrans_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /userTrans command - View user's last 10 payment transactions"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /userTrans <User_ID>\n\nExample: /userTrans 123456789"
        )
        return

    try:
        target_user_id = int(context.args[0])

        if not db.user_exists(target_user_id):
            await update.message.reply_text(f"❌ User `{target_user_id}` does not exist.", parse_mode="Markdown")
            return

        transactions = db.get_user_transactions(target_user_id, limit=10)

        if not transactions:
            await update.message.reply_text(f"📊 User `{target_user_id}` has no transactions.", parse_mode="Markdown")
            return

        msg = f"💳 **Last 10 Transactions for User `{target_user_id}`**\n\n"

        for idx, txn in enumerate(transactions, 1):
            amount = txn['amount']
            amount_str = f"+{amount}" if amount > 0 else str(amount)
            
            msg += f"**{idx}. Transaction #{txn['id']}**\n"
            msg += f"   💰 Amount: `{amount_str} Gems`\n"
            msg += f"   📝 Type: `{txn['type']}`\n"
            
            if txn.get('description'):
                msg += f"   📄 Description: {txn['description']}\n"
            
            # Parse metadata if available
            if txn.get('metadata'):
                try:
                    metadata = json.loads(txn['metadata']) if isinstance(txn['metadata'], str) else txn['metadata']
                    if metadata.get('trx_id'):
                        msg += f"   🆔 Trx ID: `{metadata['trx_id']}`\n"
                    if metadata.get('chat_link'):
                        msg += f"   🔗 [View Proof]({metadata['chat_link']})\n"
                except:
                    pass
            
            # Transaction date
            if txn.get('transaction_at'):
                trans_at = datetime.fromisoformat(txn['transaction_at']) if isinstance(txn['transaction_at'], str) else txn['transaction_at']
                msg += f"   📅 Date: {trans_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            elif txn.get('created_at'):
                created_at = datetime.fromisoformat(txn['created_at']) if isinstance(txn['created_at'], str) else txn['created_at']
                msg += f"   📅 Date: {created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            msg += "\n"

        await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)

    except ValueError:
        await update.message.reply_text("❌ Invalid User ID format. Please enter a valid number.")
    except Exception as e:
        logger.error(f"Error in userTrans command: {e}")
        await update.message.reply_text(f"❌ An error occurred: {e}")


async def userjobs_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /userJobs command - View user's last 10 verification jobs"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /userJobs <User_ID>\n\nExample: /userJobs 123456789"
        )
        return

    try:
        target_user_id = int(context.args[0])

        if not db.user_exists(target_user_id):
            await update.message.reply_text(f"❌ User `{target_user_id}` does not exist.", parse_mode="Markdown")
            return

        jobs = db.get_user_verifications(target_user_id, limit=10)

        if not jobs:
            await update.message.reply_text(f"📋 User `{target_user_id}` has no verification jobs.", parse_mode="Markdown")
            return

        msg = f"🔍 **Last 10 Verification Jobs for User `{target_user_id}`**\n\n"

        for idx, job in enumerate(jobs, 1):
            # Status emoji
            status_emoji = "✅" if job['status'] == 'success' else "❌" if job['status'] == 'failed' else "⏳"
            
            msg += f"**{idx}. Job #{job['id']}**\n"
            msg += f"   🏷️ Type: `{job['verification_type']}`\n"
            msg += f"   {status_emoji} Status: `{job['status']}`\n"
            
            if job.get('verification_id'):
                msg += f"   🆔 Verification ID: `{job['verification_id']}`\n"
            
            if job.get('result'):
                # Truncate long results
                result = job['result']
                if len(result) > 100:
                    result = result[:100] + "..."
                msg += f"   📄 Result: {result}\n"
            
            if job.get('verification_url'):
                msg += f"   🔗 [View URL]({job['verification_url']})\n"
            
            # Created date
            if job.get('created_at'):
                created_at = job['created_at'] if isinstance(job['created_at'], datetime) else datetime.fromisoformat(str(job['created_at']))
                msg += f"   📅 Date: {created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            msg += "\n"

        await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)

    except ValueError:
        await update.message.reply_text("❌ Invalid User ID format. Please enter a valid number.")
    except Exception as e:
        logger.error(f"Error in userJobs command: {e}")
        await update.message.reply_text(f"❌ An error occurred: {e}")



async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /users command - Show user statistics or list recent users"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    try:
        # Check if user wants to list recent users
        if context.args and len(context.args) > 0:
            # List mode: /users <number>
            try:
                limit = int(context.args[0])
                if limit <= 0 or limit > 50:
                    await update.message.reply_text("❌ Please specify a number between 1 and 50.")
                    return
                
                recent_users = db.get_recent_users(limit)
                
                if not recent_users:
                    await update.message.reply_text("No users found.")
                    return
                
                # Build user list message
                message = f"📋 **Last {len(recent_users)} Recent Active Users**\n\n"
                
                for idx, user in enumerate(recent_users, 1):
                    user_id_str = user.get('user_id', 'N/A')
                    username = user.get('username', 'N/A')
                    full_name = user.get('full_name', 'N/A')
                    balance = user.get('balance', 0)
                    
                    # Parse dates
                    created_at = user.get('created_at', 'N/A')
                    if created_at != 'N/A':
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            created_at = dt.strftime('%Y-%m-%d')
                        except:
                            pass
                    
                    last_checkin = user.get('last_checkin', 'Never')
                    if last_checkin and last_checkin != 'Never':
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(last_checkin.replace('Z', '+00:00'))
                            last_checkin = dt.strftime('%Y-%m-%d')
                        except:
                            pass
                    
                    # Get inviter info
                    invited_by_text = "Direct"
                    if user.get('invited_by'):
                        inviter_id = user['invited_by']
                        inviter = db.get_user(inviter_id)
                        if inviter:
                            inviter_name = inviter.get('full_name') or inviter.get('username') or 'Unknown'
                            invited_by_text = f"{inviter_id} ({inviter_name})"
                        else:
                            invited_by_text = f"{inviter_id}"
                    
                    # Count invited users
                    invited_count = db.get_invite_count(user_id_str)
                    
                    message += (
                        f"{idx}. **{full_name}** (@{username})\n"
                        f"   • ID: `{user_id_str}`\n"
                        f"   • Joined: {created_at}\n"
                        f"   • Last Check-in: {last_checkin}\n"
                        f"   • Balance: {balance} 💎\n"
                        f"   • Invited By: {invited_by_text}\n"
                        f"   • Invited: {invited_count} people\n\n"
                    )
                
                await update.message.reply_text(message, parse_mode="Markdown")
                
            except ValueError:
                await update.message.reply_text("❌ Invalid number format. Usage: /users <number>")
        else:
            # Dashboard mode: /users
            stats = db.get_user_stats()
            
            from config import ENVIRONMENT
            env_pref = "⚠️ **TEST MODE**\n" if ENVIRONMENT != "production" else ""
            
            message = (
                f"{env_pref}"
                f"📊 **User Statistics Dashboard**\n\n"
                f"👥 **Total Users:** `{stats['total_users']}`\n"
                f"✅ **Active Users (7 days):** `{stats['active_users']}`\n"
                f"💎 **Total Gems in Circulation:** `{stats['total_gems']}`\n"
                f"🚫 **Blocked Users:** `{stats['blocked_users']}`\n"
                f"🆕 **New Users Today:** `{stats['new_users_today']}`\n\n"
                f"💡 Use `/users <number>` to list recent active users"
            )
            
            await update.message.reply_text(message, parse_mode="Markdown")
            
    except Exception as e:
        logger.error(f"Error in users command: {e}")
        await update.message.reply_text(f"❌ An error occurred: {e}")


async def setinvitealert_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /setinvitealert command - Set referral milestone threshold and reward"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    from config import INVITE_ALERT_THRESHOLD, INVITE_MILESTONE_REWARD
    
    if not context.args:
        current_threshold = db.get_setting('invite_alert_threshold', INVITE_ALERT_THRESHOLD)
        current_reward = db.get_setting('invite_milestone_reward', INVITE_MILESTONE_REWARD)
        await update.message.reply_text(
            f"📊 **Referral Milestone Settings:**\n"
            f"🎯 **Base Threshold:** `{current_threshold}` invitations\n"
            f"🎁 **Reward Setting:** `{current_reward}`\n\n"
            "💡 **Note:** Alerts trigger at `Threshold`, `2x`, `4x`, `8x`... (e.g., 10, 20, 40, 80)\n\n"
            "Usage: `/setinvitealert <base_threshold> [reward_detail]`\n"
            "Example: `/setinvitealert 10 20_Gems`",
            parse_mode="Markdown"
        )
        return

    try:
        new_threshold = int(context.args[0])
        new_reward = context.args[1] if len(context.args) > 1 else db.get_setting('invite_milestone_reward', INVITE_MILESTONE_REWARD)
        
        if new_threshold < 1:
            await update.message.reply_text("❌ Base threshold must be at least 1.")
            return

        success = db.set_setting('invite_alert_threshold', new_threshold)
        if len(context.args) > 1:
            success = success and db.set_setting('invite_milestone_reward', str(new_reward))

        if success:
            await update.message.reply_text(
                f"✅ **Referral Milestone Updated!**\n\n"
                f"🎯 **Base Threshold:** `{new_threshold}` invitations\n"
                f"🎁 **Reward Detail:** `{new_reward}`\n\n"
                f"💡 Alerts trigger at: `{new_threshold}, {new_threshold*2}, {new_threshold*4}, {new_threshold*8}...`",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ Failed to update settings in database.")
            
    except ValueError:
        await update.message.reply_text("❌ Invalid format. Please enter valid integers.")
    except Exception as e:
        logger.error(f"Error in setinvitealert command: {e}")
        await update.message.reply_text(f"❌ An error occurred: {e}")
