"""Payment automation handler for ABA Bank notifications"""
import re
import logging
import os
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from config import ABA_NOTIFICATION_GROUP_ID, GEM_RATE
from database.base import Database
from utils.messages import get_deposit_notification
from utils.ocr import extract_receipt_data

logger = logging.getLogger(__name__)

async def aba_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle messages from PayWay bot in the notification group"""
    try:
        print(f"[PAYMENT_HANDLER] Handler triggered")  # Cloud Run captures print better
        
        # 1. Safer Extraction for linked channel posts or bot messages
        chat = update.effective_chat
        user = update.effective_user
        msg = update.message or update.channel_post
        
        if not msg or not chat:
            print(f"[PAYMENT_HANDLER] No message or chat, returning")
            return

        message_text = msg.text or msg.caption or ""
        
        # Log for debugging (Safe against None sender)
        username = user.username if user else "ChannelPost/OfficialBot"
        user_id_sender = user.id if user else 0
        print(f"[PAYMENT_HANDLER] MSG RECEIVED - Chat: {chat.id} | From: {username} ({user_id_sender})")
        logger.info(f"--- MSG RECEIVED --- Chat: {chat.id} | From: {username} ({user_id_sender})")
        
        # Check if this is from the notification group
        if chat.id != ABA_NOTIFICATION_GROUP_ID:
            print(f"[PAYMENT_HANDLER] Wrong chat ID {chat.id}, expected {ABA_NOTIFICATION_GROUP_ID}")
            return

        if not message_text:
            print(f"[PAYMENT_HANDLER] No message text")
            return

        print(f"[PAYMENT_HANDLER] Processing message: {message_text[:100]}")
        logger.info(f"Processing group message: {message_text[:100]}...")

        # Flexible Regex Patterns
        # 1. Amount: Matches "$5.00" or "USD 5.00"
        amount_match = re.search(r"(\$|USD\s?)([\d\.]+)", message_text)
        
        # 2. Remark: Extract the section after "Remark:" but before next label
        remark_text = "Empty"
        user_id = None
        reason = "User ID not found in Remark"
        
        remark_section_match = re.search(r"Remark:\s*(.*?)(?=\. Trx|\. APV|$)", message_text, re.DOTALL | re.IGNORECASE)
        if remark_section_match:
            remark_content = remark_section_match.group(1).strip()
            remark_text = remark_content
            print(f"[PAYMENT_HANDLER] Found remark: {remark_text}")
            
            # Search for a sequence of 6-11 digits (typical Telegram/Bot User IDs)
            id_candidates = re.findall(r"\d{6,11}", remark_content)
            
            for candidate in id_candidates:
                candidate_id = int(candidate)
                if db.user_exists(candidate_id):
                    user_id = candidate_id
                    print(f"[PAYMENT_HANDLER] Found valid user ID: {user_id}")
                    break # Found a valid user ID!
        else:
            print(f"[PAYMENT_HANDLER] No remark field found in message")
        
        # 3. Trx ID: Common formats "Trx. ID:", "Trx ID:", "Transaction ID:", "Trans ID:"
        trx_id_match = re.search(r"(Trx\.?\s*ID|Trans(action)?\s*ID):\s*(\d+)", message_text, re.IGNORECASE)

        if not amount_match or not trx_id_match:
            print(f"[PAYMENT_HANDLER] Missing amount or trx_id - amount_match: {bool(amount_match)}, trx_id_match: {bool(trx_id_match)}")
            return

        amount_usd = float(amount_match.group(2))
        trx_id = trx_id_match.group(3)
        
        print(f"[PAYMENT_HANDLER] Extracted - Amount: ${amount_usd}, Trx: {trx_id}, User: {user_id}")

        # 4. Security Check: Block Sandbox or Test transactions in production
        if "sandbox" in message_text.lower() or "test" in message_text.lower():
            from config import ENVIRONMENT
            if ENVIRONMENT == "production":
                print(f"[PAYMENT_HANDLER] SECURITY: Blocked Sandbox transaction {trx_id}")
                logger.warning(f"SECURITY: Blocked Sandbox transaction attempt {trx_id}")
                return
            else:
                logger.info(f"Processing TEST transaction as requested in dev mode: {trx_id}")

        # 5. Security Check: Verify Merchant Name based on Environment
        is_test_merchant = "KCK" in message_text
        is_live_merchant = "K.HOR" in message_text and not is_test_merchant

        from config import ENVIRONMENT
        if ENVIRONMENT == "production":
            if not is_live_merchant:
                print(f"[PAYMENT_HANDLER] SECURITY: Production bot ignoring merchant (found: {message_text[:30]}...)")
                return
        else:
            if not is_test_merchant:
                print(f"[PAYMENT_HANDLER] SECURITY: Test bot ignoring merchant (found: {message_text[:30]}...)")
                return

        # 6. Transaction Time: Matches "Time: 17-Jan-2026 08:32:43"
        transaction_at = None
        time_match = re.search(r"Time:\s*([\d\w\-:\s]+)", message_text, re.IGNORECASE)
        if time_match:
            time_str = time_match.group(1).strip()
            try:
                # Try to parse the specific format: 17-Jan-2026 08:32:43
                transaction_at = datetime.strptime(time_str, "%d-%b-%Y %H:%M:%S")
            except:
                logger.warning(f"Could not parse transaction time: {time_str}")
        
        # === DUPLICATE CHECK ===
        if db.trx_exists(trx_id):
            print(f"[PAYMENT_HANDLER] Duplicate transaction: {trx_id}")
            logger.info(f"Duplicate transaction ignored: {trx_id}")
            msg_text = (
                "🏦 **DUPLICATE TRANSACTION**\n"
                "━━━━━━━━━━━━━━━━━━\n"
                f"🆔 **Trx ID:** `{trx_id}`\n"
                "❌ **Status:** Already processed.\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "💡 *This transaction has already been credited to a user.*"
            )
            # Using reply_text if possible, else bot.send_message
            if update.message:
                await update.message.reply_text(msg_text, parse_mode="Markdown")
            else:
                await context.bot.send_message(chat_id=chat.id, text=msg_text, parse_mode="Markdown")
            return
        
        # === AUTO-TOPUP SUCCESS ===
        if user_id:
            print(f"[PAYMENT_HANDLER] AUTO-TOPUP for user {user_id}")
            gems_to_add = int(amount_usd * GEM_RATE)
            
            # User details for notification
            user_info = db.get_user(user_id)
            user_name = user_info.get('full_name', 'Unknown') if user_info else 'Unknown'
            
            if db.add_balance(user_id, gems_to_add, description=f"Automated ABA Top-up", metadata={'trx_id': trx_id, 'amount_usd': amount_usd}, transaction_at=transaction_at):
                
                # 1. Notify the User (Private Message)
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=get_deposit_notification(amount_usd, gems_to_add, trx_id),
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify user {user_id}: {e}")
                
                # 2. Notify the Group (Success)
                from datetime import datetime
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                success_msg = (
                    "✅ **AUTO-TOPUP SUCCESS**\n"
                    "━━━━━━━━━━━━━━━━━━\n"
                    f"👤 **User:** {user_name} (`{user_id}`)\n"
                    f"💰 **Amount:** `${amount_usd:.2f}`\n"
                    f"💎 **Credit:** `+{gems_to_add} Gems`\n"
                    f"🆔 **Trx ID:** `{trx_id}`\n"
                    f"📅 **Time:** {now}\n"
                    "━━━━━━━━━━━━━━━━━━\n"
                )
                
                # Thread safety for topic groups
                thread_id = update.effective_message.message_thread_id if update.effective_message else None

                if update.message:
                    await update.message.reply_text(success_msg, parse_mode="Markdown")
                else:
                    await context.bot.send_message(chat_id=chat.id, text=success_msg, parse_mode="Markdown", message_thread_id=thread_id)
                
                logger.info(f"Successfully credited {gems_to_add} Gems to user {user_id} for Trx {trx_id}")
                print(f"[PAYMENT_HANDLER] SUCCESS: Credited {gems_to_add} gems to user {user_id}")

            else:
                # DB Error
                error_msg = f"❌ **DB ERROR**\nFailed to add Gems to user `{user_id}`.\nTrx: `{trx_id}`"
                if update.message:
                    await update.message.reply_text(error_msg, parse_mode="Markdown")
                else:
                    await context.bot.send_message(chat_id=chat.id, text=error_msg, parse_mode="Markdown")

        # === MANUAL CHECK REQUIRED ===
        else:
            print(f"[PAYMENT_HANDLER] MANUAL CHECK REQUIRED - No user ID found")
            from datetime import datetime
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Try to extract a potential User ID from invalid remark
            potential_user_id = user_id or "USER_ID" 
            id_match = re.search(r"(\d{8,10})", remark_text)
            if id_match:
                potential_user_id = id_match.group(1)

            alert_msg = (
                "⚠️ **MANUAL CHECK REQUIRED**\n"
                "━━━━━━━━━━━━━━━━━━\n"
                f"💰 **Amount:** `${amount_usd:.2f}`\n"
                f"📝 **Remark:** `{remark_text}`\n"
                f"🆔 **Trx ID:** `{trx_id}`\n"
                f"📅 **Time:** {now}\n"
                "━━━━━━━━━━━━━━━━━━\n"
                f"❌ **Reason:** {reason}\n\n"
                "🛠️ **ADMIN ACTIONS (COPY & PASTE)**\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "✅ **Approve Top-up:**\n"
                f"`/approve {potential_user_id} {trx_id if trx_id else ''}\u00A0\u00A0` `[AMOUNT]`\n\n"
                "❌ **Reject Payment:**\n"
                f"`/reject \"Invalid Transaction ID\"`\n"
                f"`/reject \"Incorrect details\"`\n\n"
                "💎 **Add Custom Gems:**\n"
                f"`/addgems {potential_user_id}\u00A0\u00A0` `[GEMS]`"
            )
            
            thread_id = update.effective_message.message_thread_id if update.effective_message else None
            print(f"[PAYMENT_HANDLER] Sending manual check alert to chat {chat.id}")
            
            if update.message:
                await update.message.reply_text(alert_msg, parse_mode="Markdown")
            else:
                await context.bot.send_message(chat_id=chat.id, text=alert_msg, parse_mode="Markdown", message_thread_id=thread_id)
            
            print(f"[PAYMENT_HANDLER] Manual check alert sent successfully")
    
    except Exception as e:
        print(f"[PAYMENT_HANDLER] CRITICAL ERROR: {str(e)}")
        logger.error(f"Critical error in payment handler: {e}", exc_info=True)
        # Try to notify admin about the error
        try:
            await context.bot.send_message(
                chat_id=ABA_NOTIFICATION_GROUP_ID,
                text=f"🚨 **PAYMENT HANDLER ERROR**\n```\n{str(e)}\n```",
                parse_mode="Markdown"
            )
        except:
            pass


async def receipt_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle receipt photos uploaded by users"""
    if not context.user_data.get('waiting_for_proof'):
        return

    # Only process in private chat
    if update.effective_chat.type != "private":
        return

    # Clear the state
    context.user_data['waiting_for_proof'] = False
    
    user_id = update.effective_user.id
    user_full_name = update.effective_user.full_name
    username = update.effective_user.username or "NoUsername"
    
    # Forward the photo to the admin notification group
    photo_file_id = update.message.photo[-1].file_id
    
    # --- SIMPLE OCR HINT ---
    extracted_trx_id = ""
    try:
        # Download photo for a quick check (just ID/User ID hints)
        new_file = await context.bot.get_file(photo_file_id)
        temp_path = f"temp_receipt_{user_id}.jpg"
        await new_file.download_to_drive(temp_path)
        extracted = extract_receipt_data(temp_path)
        extracted_trx_id = extracted.get('trx_id', '')
        if os.path.exists(temp_path): os.remove(temp_path)
    except Exception as e:
        logger.error(f"OCR hint failed: {e}")

    # Construct the alert with manual amount entry
    alert_msg = (
        "📥 **NEW PAYMENT PROOF**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 **User:** {user_full_name} (@{username})\n"
        f"🆔 **User ID:** `{user_id}`\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🛠️ **ADMIN ACTIONS (COPY & PASTE)**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "✅ **Approve:**\n"
        f"`/approve {user_id} {extracted_trx_id if extracted_trx_id else ''}\u00A0\u00A0` `[AMOUNT]`\n\n"
        "❌ **Reject Payment:**\n"
        f"`/reject \"Could not verify ID\"`\n"
        f"`/reject \"Wrong screenshot\"`\n"
        f"`/reject \"Amount mismatch\"`\n\n"
        "💎 **Quick Add Gems:**\n"
        f"`/addgems {user_id}\u00A0\u00A0` `[GEMS]`\n\n"
        "💡 *Look at the photo and enter the [AMOUNT] manually.*"
    )
    
    try:
        from config import ABA_NOTIFICATION_GROUP_ID, ADMIN_TOPIC_ID
        await context.bot.send_photo(
            chat_id=ABA_NOTIFICATION_GROUP_ID,
            message_thread_id=ADMIN_TOPIC_ID,
            photo=photo_file_id,
            caption=alert_msg,
            parse_mode="Markdown"
        )
        
        await update.message.reply_text(
            "✅ **Payment proof submitted!**\n\n"
            "Our team will verify your payment and credit the Gems to your account soon.\n"
            "You will receive a notification once it's done.",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Failed to forward proof to admin group: {e}")
        await update.message.reply_text("❌ Failed to submit proof. Please try again later or contact support.")
