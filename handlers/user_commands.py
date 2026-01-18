"""User command handler"""
import logging
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_USER_ID, ABA_QR_PATH, BINANCE_QR_PATH
from database.base import Database
from utils.checks import reject_group_command, global_checks
from utils.messages import (
    get_welcome_message,
    get_about_message,
    get_help_message,
    get_profile_message,
    get_topup_message,
    get_topup_message,
    get_crypto_message,
    get_pricing_menu,
)

logger = logging.getLogger(__name__)


@global_checks(registration_required=False)
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /start command"""
    if await reject_group_command(update):
        return

    user = update.effective_user
    user_id = user.id
    username = user.username or ""
    full_name = user.full_name or ""

    # If already initialized, we still show the full welcome message as a guide
    if db.user_exists(user_id):
        welcome_msg = get_welcome_message(full_name, is_new_user=False)
        await update.message.reply_text(welcome_msg, parse_mode="Markdown")
        return

    # Handle invitation
    invited_by: Optional[int] = None
    if context.args:
        try:
            invited_by = int(context.args[0])
            if not db.user_exists(invited_by):
                invited_by = None
        except Exception:
            invited_by = None

    # Create user
    if db.create_user(user_id, username, full_name, invited_by):
        welcome_msg = get_welcome_message(full_name, bool(invited_by), is_new_user=True)
        await update.message.reply_text(welcome_msg, parse_mode="Markdown")
        
        # Check if inviter reached a milestone
        if invited_by:
            try:
                # Use setting if available, otherwise fallback to config
                from config import INVITE_ALERT_THRESHOLD, ADMIN_USER_ID
                threshold = db.get_setting('invite_alert_threshold', INVITE_ALERT_THRESHOLD)
                
                invite_count = db.get_invite_count(invited_by)
                
                # Doubling milestone logic (Threshold, 2x, 4x, 8x...)
                # Check if (invite_count / threshold) is a power of 2
                is_milestone = False
                if invite_count >= threshold and invite_count % threshold == 0:
                    ratio = invite_count // threshold
                    if ratio > 0 and (ratio & (ratio - 1)) == 0:
                        is_milestone = True

                if is_milestone:
                    # Notify Admin
                    inviter = db.get_user(invited_by)
                    inviter_name = inviter.get('full_name') or inviter.get('username') or 'Unknown'
                    reward_detail = db.get_setting('invite_milestone_reward', INVITE_MILESTONE_REWARD)
                    
                    admin_msg = (
                        "🎊 **Referral Milestone Reached!**\n\n"
                        f"👤 **User:** {inviter_name} (`{invited_by}`)\n"
                        f"📈 **Total Invitations:** `{invite_count}`\n"
                        f"🎯 **Milestone Range:** `{threshold} (Doubling Logic)`\n"
                        f"🎁 **Reward To Process:** `{reward_detail}`\n\n"
                        "This user has reached a doubling referral milestone! 🚀"
                    )
                    
                    try:
                        await context.bot.send_message(
                            chat_id=ADMIN_USER_ID,
                            text=admin_msg,
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        logger.error(f"Failed to notify admin about referral milestone: {e}")
            except Exception as e:
                logger.error(f"Error checking referral milestone: {e}")
    else:
        await update.message.reply_text("Registration failed. Please try again later.")


@global_checks()
async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /about command"""
    if await reject_group_command(update):
        return

    await update.message.reply_text(get_about_message(), parse_mode="Markdown")


@global_checks()
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /help command"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id
    is_admin = user_id == ADMIN_USER_ID
    await update.message.reply_text(
        get_help_message(is_admin),
        parse_mode="Markdown",
        disable_web_page_preview=True
    )


@global_checks()
async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /balance command"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if db.is_user_blocked(user_id):
        await update.message.reply_text("You are blacklisted and cannot use this feature.")
        return

    user = db.get_user(user_id)
    if not user:
        await update.message.reply_text("Please register using /start first.")
        return

    await update.message.reply_text(
        f"💰 **Gem Balance**\n\nYour Current Balance: `{user['balance']}` Gems",
        parse_mode="Markdown"
    )


@global_checks()
async def checkin_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /checkin or /qd command - Daily check-in"""
    user_id = update.effective_user.id

    # Check-in logic

    # Level 1 check: Check at command handler level
    if not db.can_checkin(user_id):
        await update.message.reply_text("❌ You have already checked in today. Please try again tomorrow!")
        return

    # Level 2 check: Execute at database level
    if db.checkin(user_id):
        await update.message.reply_text("✅ Check-in successful! +1 Gems")
    else:
        # If database level returns False, user already checked in (double insurance)
        await update.message.reply_text("❌ You have already checked in today. Please try again tomorrow!")


@global_checks()
async def invite_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /invite command"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id


    # Invite logic
    bot_username = context.bot.username
    invite_link = f"https://t.me/{bot_username}?start={user_id}"

    # Get threshold and reward for note
    from config import INVITE_ALERT_THRESHOLD, INVITE_MILESTONE_REWARD
    threshold = db.get_setting('invite_alert_threshold', INVITE_ALERT_THRESHOLD)
    reward = db.get_setting('invite_milestone_reward', INVITE_MILESTONE_REWARD)

    msg = (
        f"🎁 **Your exclusive invitation link:**\n`{invite_link}`\n\n"
        "You will receive **2 Gems** for every successfully registered person you invite.\n"
        f"💡 *Note: Reach `{threshold}` invitations to unlock exclusive milestone rewards!*"
    )

    await update.message.reply_text(msg, parse_mode="Markdown")


@global_checks()
async def use_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /use command - use card key"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id


    # Use logic

    if not context.args:
        await update.message.reply_text(
            "Usage: /use <key>\n\nExample: /use NEWYEAR26"
        )
        return

    key_code = context.args[0].strip()
    result = db.use_card_key(key_code, user_id)

    if result is None:
        await update.message.reply_text("Card key does not exist. Please check and try again.")
    elif result == -1:
        await update.message.reply_text("This card key has reached its maximum uses.")
    elif result == -2:
        await update.message.reply_text("This card key has expired.")
    elif result == -3:
        await update.message.reply_text("You have already used this card key.")
    else:
        user = db.get_user(user_id)
        await update.message.reply_text(
            f"Card key used successfully!\nGems received: {result}\nCurrent balance: {user['balance']}"
        )


@global_checks()
async def me_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /me command - View user profile"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    
    # Get inviter info
    inviter_name = "Direct"
    if user_data.get('invited_by'):
        inviter_id = user_data['invited_by']
        inviter = db.get_user(inviter_id)
        if inviter:
            inv_name = inviter.get('full_name') or inviter.get('username') or "Unknown"
            inviter_name = f"{inviter_id} ({inv_name})"
        else:
            inviter_name = f"{inviter_id}"
            
    # Get invite count
    try:
        invited_count = db.get_invite_count(user_id)
    except Exception as e:
        logger.error(f"Error getting invite count in me_command for {user_id}: {e}")
        invited_count = 0

    await update.message.reply_text(
        get_profile_message(user_data, inviter_name, invited_count),
        parse_mode="Markdown"
    )


@global_checks()
async def topup_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /topup command - Choice between Local and International"""
    if await reject_group_command(update):
        return

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [
            InlineKeyboardButton("🇰🇭 Local (ABA KHQR)", callback_data="topup_local"),
            InlineKeyboardButton("🌐 International (USDT)", callback_data="topup_intl")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "💳 **TOP-UP GEMS**\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Please select your preferred payment method:\n\n"
        "🇰🇭 **Local**: ABA Bank (KH Only)\n"
        "🌐 **International**: USDT (Binance/Global)\n\n"
        "💵 **Rate**: 1 USD = 10 Gems",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def topup_local_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle local topup selection"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    from config import ABA_QR_PATH
    from utils.messages import get_topup_message
    
    try:
        # Edit the existing message to show ABA info
        with open(ABA_QR_PATH, 'rb') as photo:
            await query.message.reply_photo(
                photo=photo,
                caption=get_topup_message(user_id),
                parse_mode="Markdown"
            )
            # Remove the original selection message
            await query.message.delete()
    except Exception as e:
        logger.error(f"Error in topup_local_callback: {e}")
        await query.message.reply_text("❌ An error occurred. Please try again later.")


async def topup_intl_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle international topup selection"""
    query = update.callback_query
    await query.answer()
    
    from config import BINANCE_QR_PATH
    from utils.messages import get_crypto_message
    
    try:
        # Edit the existing message to show Binance info
        with open(BINANCE_QR_PATH, 'rb') as photo:
            await query.message.reply_photo(
                photo=photo,
                caption=get_crypto_message(),
                parse_mode="Markdown"
            )
            # Remove the original selection message
            await query.message.delete()
    except Exception as e:
        logger.error(f"Error in topup_intl_callback: {e}")
        await query.message.reply_text("❌ An error occurred. Please try again later.")


@global_checks()
async def proof_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /proof command to start receipt upload flow"""
    if await reject_group_command(update):
        return
    context.user_data['waiting_for_proof'] = True
    await update.message.reply_text(
        "📸 **Payment Proof Upload**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Please send the **screenshot** of your transaction now.\n\n"
        "💡 *The admin will verify it and credit your Gems shortly.*",
        parse_mode="Markdown"
    )

@global_checks()
async def verify_receipt_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Alias for /proof"""
    return await proof_command(update, context, db)


@global_checks()
async def lsgd_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /lsgd command - View transaction history"""
    try:
        if await reject_group_command(update):
            return

        user_id = update.effective_user.id
        
        # Fetch user's current balance
        user = db.get_user(user_id)
        current_balance = user.get('balance', 0)
        
        # Fetch transaction history
        transactions = db.get_user_transactions(user_id, limit=10)
        
        # Import the message formatter
        from utils.messages import get_transaction_history_message
        
        await update.message.reply_text(
            get_transaction_history_message(transactions, current_balance),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error in lsgd_command: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ An error occurred while fetching your transaction history. Please try again later."
        )


@global_checks()
async def myjobs_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /myjobs command - View running or queued jobs"""
    try:
        logger.info(f"myjobs_command called by user {update.effective_user.id}")
        
        if await reject_group_command(update):
            return

        user_id = update.effective_user.id
        
        # Fetch user's verification history
        logger.info(f"Fetching verifications for user {user_id}")
        verifications = db.get_user_verifications(user_id, limit=10)
        
        logger.info(f"User {user_id} requested /myjobs, found {len(verifications)} verifications")
        logger.info(f"Verification data: {verifications[:2] if verifications else 'None'}")  # Log first 2 for debugging
        
        # Import the message formatter
        from utils.messages import get_jobs_message
        
        message = get_jobs_message(verifications)
        logger.info(f"Generated message length: {len(message)}")
        
        await update.message.reply_text(
            message,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error in myjobs_command: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ An error occurred while fetching your jobs. Please try again later."
        )


@global_checks()
async def lang_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /lang command - Language switcher (English Only)"""
    if await reject_group_command(update):
        return

    await update.message.reply_text(
        "🌐 **LANGUAGE SETTINGS**\n\n"
        "Currently, only **English** is supported. We are working on adding more languages soon!",
        parse_mode="Markdown"
    )


@global_checks()
async def guide_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /guide | /hdsd command - Interactive guide"""
    if await reject_group_command(update):
        return

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    # Create inline keyboard with service buttons
    keyboard = [
        [InlineKeyboardButton("🔵 Google One", callback_data="guide_google_one")],
        [InlineKeyboardButton("🟢 Spotify Premium", callback_data="guide_spotify")],
        [InlineKeyboardButton("🔴 YouTube Premium", callback_data="guide_youtube")],
        [InlineKeyboardButton("⚫ ChatGPT Teachers", callback_data="guide_chatgpt")],
        [InlineKeyboardButton("⚡ Bolt.new", callback_data="guide_bolt")],
        [InlineKeyboardButton("💡 General Guide", callback_data="guide_general")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    guide_message = (
        "📚 **Guides for services supported by the bot**\n\n"
        "Choose the service you want to see the detailed guide for:\n\n"
        "👇 **Tap a button below to view the guide**"
    )
    
    await update.message.reply_text(
        guide_message,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


@global_checks()
async def services_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /services command - View service list and pricing"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    await update.message.reply_text(
        get_pricing_menu(user['balance']),
        parse_mode="Markdown"
    )


async def guide_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle guide button callbacks"""
    query = update.callback_query
    await query.answer()
    
    from config import VERIFY_COST, SERVICE_COSTS
    import os
    
    service = query.data.replace("guide_", "")
    
    # Map internal guide keys to SERVICE_COSTS keys
    cost_map = {
        "google_one": "gemini_one_pro",
        "spotify": "spotify_student",
        "youtube": "youtube_student",
        "chatgpt": "chatgpt_teacher_k12",
        "bolt": "bolt_teacher"
    }
    
    # Get dynamic cost
    service_key = cost_map.get(service)
    cost = SERVICE_COSTS.get(service_key, VERIFY_COST)
    
    # Define logo paths
    base_path = "/Users/kakada/Documents/GitHub/tgbot-verify/assets/logos"
    logo_map = {
        "google_one": f"{base_path}/google_one.png",
        "spotify": f"{base_path}/spotify.png",
        "youtube": f"{base_path}/youtube.png",
        "chatgpt": f"{base_path}/chatgpt.png",
        "bolt": f"{base_path}/bolt.png",
    }
    
    guides = {
        "google_one": (
            "📘 **Google One (Gemini Advanced) Guide**\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "**🎯 How to Verify:**\n"
            "1. Go to [Google One Student Plan](https://one.google.com/student)\n"
            "2. Click 'Verify student status'\n"
            "3. Fill in your information\n"
            "4. Copy the SheerID verification URL\n"
            f"5. Send to bot: `/verify <url>` ({cost} Gems)\n\n"
            "**✨ What You Get:**\n"
            "• Gemini Advanced AI access\n"
            "• 2TB Google Drive storage\n"
            "• Google Photos premium features\n\n"
            "**💡 Tips:**\n"
            "• Use a .edu email if possible\n"
            "• Verification usually takes 1-2 minutes\n"
            "• Valid for 1 year, renewable"
        ),
        "spotify": (
            "📘 **Spotify Premium Student Guide**\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "**🎯 How to Verify:**\n"
            "1. Go to [Spotify Student](https://www.spotify.com/student)\n"
            "2. Click 'Get Started'\n"
            "3. Fill in your student information\n"
            "4. Copy the SheerID verification URL\n"
            f"5. Send to bot: `/verify3 <url>` ({cost} Gems)\n\n"
            "**✨ What You Get:**\n"
            "• Ad-free music streaming\n"
            "• Offline downloads\n"
            "• 50% student discount\n\n"
            "**💡 Tips:**\n"
            "• Must be enrolled in accredited institution\n"
            "• Renew every 12 months\n"
            "• Up to 4 years of student pricing"
        ),
        "youtube": (
            "📘 **YouTube Premium Student Guide**\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "**🎯 How to Verify:**\n"
            "1. Go to [YouTube Premium Student](https://www.youtube.com/premium/student)\n"
            "2. Click 'Try it free' or 'Learn more'\n"
            "3. Complete student verification\n"
            "4. Copy the SheerID verification URL\n"
            f"5. Send to bot: `/verify5 <url>` ({cost} Gems)\n\n"
            "**✨ What You Get:**\n"
            "• Ad-free YouTube videos\n"
            "• Background playback\n"
            "• YouTube Music Premium\n"
            "• Offline downloads\n\n"
            "**💡 Tips:**\n"
            "• Student discount: ~50% off\n"
            "• Renew annually\n"
            "• Includes YouTube Music"
        ),
        "chatgpt": (
            "📘 **ChatGPT for Teachers Guide**\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "**🎯 How to Verify:**\n"
            "1. Go to [ChatGPT Edu](https://openai.com/chatgpt/education)\n"
            "2. Click teacher verification link\n"
            "3. Fill in your teaching credentials\n"
            "4. Copy the SheerID verification URL\n"
            f"5. Send to bot: `/verify2 <url>` ({cost} Gems)\n\n"
            "**✨ What You Get:**\n"
            "• ChatGPT Plus features\n"
            "• GPT-4 access\n"
            "• Priority access during peak times\n\n"
            "**💡 Helpful Tips:**\n"
            "• School email is **recommended** for faster verification\n"
            "• Personal emails (Gmail, Yahoo, etc.) might take longer or may not work\n"
            "• Using your official school email (.edu or school domain) typically gives instant results\n\n"
            "**📚 Additional Info:**\n"
            "• For K-12 educators\n"
            "• Free for verified teachers\n"
            "• Verification usually completes within minutes"
        ),
        "bolt": (
            "📘 **Bolt.new Teacher Verification Guide**\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "**🎯 How to Verify:**\n"
            "1. Go to [Bolt.new](https://bolt.new)\n"
            "2. Look for teacher/educator discount\n"
            "3. Start verification process\n"
            "4. Copy the SheerID verification URL\n"
            f"5. Send to bot: `/verify4 <url>` ({cost} Gems)\n\n"
            "**✨ What You Get:**\n"
            "• AI-powered coding assistant\n"
            "• Full-stack web development\n"
            "• Teacher discount access\n\n"
            "**⏳ If Code Not Ready:**\n"
            "If verification takes longer than 20 seconds:\n"
            "1. Bot will give you a `verification_id`\n"
            "2. Wait 1-5 minutes for review\n"
            "3. Check status: `/getv4code <verification_id>`\n"
            "4. Retrieve your code when ready\n\n"
            "**💡 Tips:**\n"
            "• For educators in tech/CS\n"
            "• Verification required for discount\n"
            "• No extra charge for code retrieval"
        ),
        "general": (
            "📚 **General Bot Guide**\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "**💎 EARNING GEMS**\n"
            "• `/checkin` - Daily check-in (+1 Gem)\n"
            "• `/invite` - Invite friends (+2 Gems/person)\n"
            "• `/use <key>` - Redeem voucher codes\n"
            "• `/topup` - Buy Gems (ABA Bank)\n"
            "• `/crypto` - Buy Gems (USDT)\n\n"
            "**🔧 USEFUL COMMANDS**\n"
            "• `/me` - View profile & balance\n"
            "• `/myjobs` - Check verification status\n"
            "• `/lsgd` - Transaction history\n"
            "• `/help` - Full command list\n\n"
            "**💳 TOP-UP**\n"
            "🇰🇭 Local: ABA Bank\n"
            "🌐 International: USDT (BEP20)\n"
            "💵 Rate: 1 USD = 10 Gems\n\n"
            "**💬 Support**\n"
            "Contact: [Admin](https://t.me/kakada66)"
        )
    }
    
    guide_text = guides.get(service, "Guide not found.")
    
    # Add back button
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    back_keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="guide_back")]]
    back_markup = InlineKeyboardMarkup(back_keyboard)
    
    # Check if logo exists for this service
    logo_path = logo_map.get(service)
    
    if logo_path and os.path.exists(logo_path):
        # Delete the old message and send new one with photo
        await query.message.delete()
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=open(logo_path, 'rb'),
            caption=guide_text,
            parse_mode="Markdown",
            reply_markup=back_markup
        )
    else:
        # No logo, just edit the message text
        await query.edit_message_text(
            guide_text,
            parse_mode="Markdown",
            reply_markup=back_markup
        )


async def guide_back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back button to return to guide menu"""
    query = update.callback_query
    await query.answer()
    
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [InlineKeyboardButton("🔵 Google One", callback_data="guide_google_one")],
        [InlineKeyboardButton("🟢 Spotify Premium", callback_data="guide_spotify")],
        [InlineKeyboardButton("🔴 YouTube Premium", callback_data="guide_youtube")],
        [InlineKeyboardButton("⚫ ChatGPT Teachers", callback_data="guide_chatgpt")],
        [InlineKeyboardButton("⚡ Bolt.new", callback_data="guide_bolt")],
        [InlineKeyboardButton("💡 General Guide", callback_data="guide_general")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    guide_message = (
        "📚 **Guides for services supported by the bot**\n\n"
        "Choose the service you want to see the detailed guide for:\n\n"
        "👇 **Tap a button below to view the guide**"
    )
    
    # Delete the photo message and send new text message
    await query.message.delete()
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=guide_message,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
