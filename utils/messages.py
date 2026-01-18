"""Message Templates"""
from config import (
    VERIFY_COST, ADMIN_SUPPORT_LINK,
    ABA_PAYMENT_LINK
)


def get_welcome_message(full_name: str, invited_by: bool = False, is_new_user: bool = True) -> str:
    """Get the overhaul welcome message"""
    greeting = f"👋 **Hi {full_name}!**" if is_new_user else f"✨ **Welcome back, {full_name}!**"
    
    msg = (
        f"{greeting}\n"
        "Welcome to the **SheerID Auto-Verification Bot**. 🚀\n\n"
        
        "**🤖 WHAT IS THIS BOT?**\n"
        "We help you automate student/teacher verifications (Gemini, Spotify, YouTube, etc.) in seconds. No more manual waiting! 🪄\n\n"
        
        "**💎 WHAT ARE GEMS?**\n"
        "Gems are the 'energy' used to power verifications. Each verification costs **5 Gems**.\n\n"
        
        "**💰 HOW TO EARN GEMS?**\n"
        "1. 👥 **Invite Friends (BEST)**: Send /invite and get **+2 Gems** for every person who joins! (Plus **milestone bonuses** 🎁)\n"
        "2. ✅ **Daily Check-in**: Use /checkin to get **+1 Gem** every single day.\n"
        "3. 💳 **Top-up**: Need Gems instantly? Use /topup to buy via ABA or USDT.\n"
        "4. 📋 **See our Services**: Send /services to see all supported services and pricing.\n\n"
    )
    
    if is_new_user:
        if invited_by:
            msg += "✨ **Bonus**: Since you joined via invitation, you've received your first Gem! Keep going! 💎\n\n"
        else:
            msg += "🎁 **Gift**: I've given you **1 Gem** to get started! 💎\n\n"

    msg += (
        "━━━━━━━━━━━━━━━━━━\n"
        "👉 **Ready?** Copy your SheerID link and send it with `/verify <link>`!\n\n"
        "💡 For more info, send /help to see all commands."
    )
    return msg


def get_about_message() -> str:
    """Get the about message"""
    return (
        "🛡️ **SheerID Auto-Verification Bot**\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "**🚀 KEY FEATURES:**\n"
        "• Automate SheerID Student/Teacher verifications.\n"
        "• Instant results for Gemini, Spotify, YouTube, Bolt, etc.\n"
        "• 24/7 reliability with automatic processing.\n\n"
        
        "**💎 GEM SYSTEM:**\n"
        "• Registration: `+1 Gem` (Gift)\n"
        "• Daily check-in: `+1 Gem`\n"
        "• Invite friends: `+2 Gems` / person\n\n"
        
        "**📖 QUICK GUIDE:**\n"
        "1. Start verification on the service website.\n"
        "2. Send /verify with the link\n"
        "3. Wait for processing and check the results\n"
        "\n"
        "For more commands, send /help"
    )


def get_help_message(is_admin: bool = False) -> str:
    """Get the help message"""
    msg = (
        "📖 **SHEERID AUTO-VERIFICATION BOT**\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        
        "**🎯 VERIFICATION**\n"
        f"• /verify `<link>` - Start verification ({VERIFY_COST} Gems)\n"
        "• /services - View all services & pricing\n"
        "• /myjobs - Check verification status\n"
        "💡 *Tip: ChatGPT works best with school email*\n\n"
        
        "**💎 GEMS & BALANCE**\n"
        "• /me - View profile & balance\n"
        "• /checkin - Daily check-in (+1 Gem)\n"
        "• /invite - Invite friends (+2 Gems + Milestone Bonuses! 🎁)\n"
        "• /use `<key>` - Redeem voucher code\n"
        "• /lsgd - Transaction history\n\n"
        
        "**💳 TOP-UP**\n"
        "• /topup - ABA Bank (Cambodia)\n"
        "• /crypto - USDT (International)\n\n"
        
        "**📚 INFORMATION**\n"
        "• /start - Register & get started\n"
        "• /about - Learn about features\n"
        "• /guide - Interactive service guides\n"
        "• /help - Show this message\n"
    )

    if is_admin:
        msg += (
            "\n**⚙️ ADMIN COMMANDS**\n"
            "• /addgems `<user_id>` `<amount>` - Add Gems\n"
            "• /block `<user_id>` - Blacklist user\n"
            "• /white `<user_id>` - Remove from blacklist\n"
            "• /blacklist - View blacklisted users\n"
            "• /genkey `<key>` `<gems>` `[uses]` `[days]` - Generate keys\n"
            "• /listkeys - View all card keys\n"
            "• /broadcast `<text>` - Send notification\n"
        )
    
    msg += f"\n━━━━━━━━━━━━━━━━━━\n💬 **Need help?** 👉 [Contact Admin Support]({ADMIN_SUPPORT_LINK})"

    return msg


def get_insufficient_balance_message(current_balance: int, required_cost: int) -> str:
    """Get the insufficient balance message"""
    return (
        f"❌ **Insufficient Gems!**\n\n"
        f"This service requires `{required_cost}` Gems.\n"
        f"Your current balance: `{current_balance}` Gems.\n\n"
        "**How to get Gems:**\n"
        "• Daily check-in: `/checkin`\n"
        "• Invite friends: `/invite`\n"
        "• Top-up: `/topup`"
    )


def get_verify_usage_message(command: str, service_name: str) -> str:
    """Get usage instructions for verification commands"""
    return (
        f"Usage: {command} <SheerID Link>\n\n"
        "Example:\n"
        f"{command} https://services.sheerid.com/verify/xxx/?verificationId=xxx\n\n"
        "How to get the link:\n"
        f"1. Visit the {service_name} verification page\n"
        "2. Start the verification process\n"
        "3. Copy the full URL from the browser address bar\n"
        f"4. Submit using the {command} command"
    )


def get_profile_message(user_data: dict, inviter_name: str = "Direct", invited_count: int = 0) -> str:
    """Get the user profile message"""
    user_id = user_data.get('user_id', 'Unknown')
    full_name = user_data.get('full_name', 'Unknown')
    username = user_data.get('username', 'N/A')
    balance = user_data.get('balance', 0)
    created_at = user_data.get('created_at', 'N/A')
    
    if isinstance(created_at, str) and 'T' in created_at:
        created_at = created_at.split('T')[0]
        
    return (
        "👤 **USER PROFILE**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🆔 **ID:** `{user_id}`\n"
        f"👤 **Name:** {full_name}\n"
        f"🔗 **Username:** @{username}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"💎 **Balance:** `{balance} Gems`\n"
        f"📅 **Joined:** `{created_at}`\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🔗 **Invited By:** {inviter_name}\n"
        f"👥 **Invited Users:** `{invited_count}` people\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "💡 *Use /topup to add more Gems!*"
    )


def get_topup_message(user_id: int) -> str:
    """Get the local (ABA) top-up message"""
    return (
        "🇰🇭 **LOCAL TOP-UP (ABA BANK)**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🏦 **Bank:** ABA Bank\n"
        "👤 **Name:** `HOR KAKADA`\n"
        "🔢 **Account:** `092 811 102`\n"
        f"⚡ **Quick Payment:** [Tappable Link]({ABA_PAYMENT_LINK})\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📝 **REMARK (FOR INSTANT TOP-UP):**\n"
        f"`{user_id}`\n"
        "*(Tap the ID above to copy)*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📈 **Rate:** `$1.00 = 10 Gems`\n"
        "💎 **Minimum:** `$1.00 (10 Gems)`\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "ℹ️ **Processing Time:**\n"
        "• **ABA to ABA:** Instant (with User ID in Remark)\n"
        "• **Other Banks/Manual:** Contact Team\n\n"
        "🤳 **Instruction:** If Gems are not received automatically, please type `/proof` and send your transaction screenshot to this bot."
    )


def get_crypto_message() -> str:
    """Get the international (USDT) top-up message"""
    return (
        "🌐 **INTERNATIONAL TOP-UP (USDT)**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "💰 **Currency:** USDT\n"
        "⛓️ **Network:** `BNB Smart Chain (BEP20)`\n"
        "📥 **Wallet Address:**\n"
        "`0x251E99d12898D3456D6b789858051aEc0493B885`\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📈 **Rate:** `1 USDT = 10 Gems`\n"
        "💎 **Minimum:** `1 USDT (10 Gems)`\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "ℹ️ **Processing Time:** 5 - 10 Minutes\n\n"
        "🤳 **Instruction:** After payment, please type `/proof` and send your transaction screenshot to this bot for verification."
    )


def get_pricing_menu(balance: int) -> str:
    """Get the pricing and services menu message"""
    from config import SERVICE_COSTS
    return (
        "💎 **GEM PRICING & SERVICES**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"💰 **Your Balance:** `{balance} Gems`\n\n"
        "✨ **Available Services:**\n"
        f"1️⃣ Gemini One Pro: `{SERVICE_COSTS.get('gemini_one_pro', 5)} Gems` (`/verify`)\n"
        f"2️⃣ ChatGPT Teacher: `{SERVICE_COSTS.get('chatgpt_teacher_k12', 5)} Gems` (`/verify2`)\n"
        f"3️⃣ Spotify Student: `{SERVICE_COSTS.get('spotify_student', 4)} Gems` (`/verify3`)\n"
        f"4️⃣ Bolt.new Teacher: `{SERVICE_COSTS.get('bolt_teacher', 5)} Gems` (`/verify4`)\n"
        f"5️⃣ YouTube Student: `{SERVICE_COSTS.get('youtube_student', 4)} Gems` (`/verify5`)\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "💡 **Tip:** ChatGPT works best with school email addresses\n\n"
        "📖 **How to verify:**\n"
        "Use the specific command followed by your SheerID link.\n"
        "Example: `/verify2 https://services.sheerid.com/verify/...`"
    )


def get_jobs_message(verifications: list) -> str:
    """Get the jobs/verification history message"""
    if not verifications:
        return (
            "⏳ **ACTIVE JOBS**\n\n"
            "You currently have no active or queued jobs.\n\n"
            "💡 *Use /verify to start a new verification!*"
        )
    
    msg = "📋 **YOUR VERIFICATION JOBS**\n"
    msg += "━━━━━━━━━━━━━━━━━━\n\n"
    
    for idx, job in enumerate(verifications, 1):
        status = job.get('status', 'unknown')
        verification_type = job.get('verification_type', 'Unknown').replace('_', ' ').title()
        result = job.get('result', 'N/A')
        created_at = job.get('created_at', 'N/A')
        
        # Format timestamp
        if isinstance(created_at, str) and 'T' in created_at:
            created_at = created_at.split('T')[0] + ' ' + created_at.split('T')[1][:8]
        
        # Status emoji
        if status == 'success':
            status_emoji = "✅"
        elif status == 'failed':
            status_emoji = "❌"
        elif status == 'pending':
            status_emoji = "⏳"
        else:
            status_emoji = "❓"
        
        msg += f"**{idx}. {verification_type}**\n"
        msg += f"{status_emoji} Status: `{status.upper()}`\n"
        msg += f"📅 Time: `{created_at}`\n"
        
        if result and result != 'N/A':
            # Truncate long results
            display_result = result[:50] + "..." if len(result) > 50 else result
            msg += f"📝 Result: `{display_result}`\n"
        
        msg += "━━━━━━━━━━━━━━━━━━\n\n"
    
    msg += "💡 *Showing last 10 verifications*"
    return msg


def get_transaction_history_message(transactions: list, current_balance: int) -> str:
    """Get the transaction history message"""
    if not transactions:
        return (
            "📋 **TRANSACTION HISTORY**\n\n"
            f"💎 **Current Balance:** `{current_balance} Gems`\n\n"
            "You have no transaction history yet.\n\n"
            "💡 *Transactions will appear here when you earn or spend Gems!*"
        )
    
    msg = "📋 **TRANSACTION HISTORY**\n"
    msg += f"💎 **Current Balance:** `{current_balance} Gems`\n"
    msg += "━━━━━━━━━━━━━━━━━━\n\n"
    
    for idx, txn in enumerate(transactions, 1):
        amount = txn.get('amount', 0)
        txn_type = txn.get('type', 'unknown')
        description = txn.get('description', 'N/A')
        created_at = txn.get('created_at', 'N/A')
        
        # Format timestamp
        if isinstance(created_at, str) and 'T' in created_at:
            created_at = created_at.split('T')[0] + ' ' + created_at.split('T')[1][:8]
        
        # Type emoji and sign
        if amount > 0:
            emoji = "➕"
            sign = "+"
            color = "🟢"
        else:
            emoji = "➖"
            sign = ""
            color = "🔴"
        
        # Type label inference for backward compatibility
        if txn_type == 'reward':
            lower_desc = description.lower()
            if 'refund' in lower_desc:
                txn_type = 'refund'
            elif 'manual approval' in lower_desc or 'payway' in lower_desc:
                txn_type = 'topup'
            elif 'addgems' in lower_desc or 'reward' in lower_desc:
                txn_type = 'reward'
        
        type_labels = {
            'topup': '💳 Top-up',
            'spend': '🛒 Spend',
            'reward': '🎁 Reward',
            'refund': '↩️ Refund',
            'checkin': '✅ Check-in',
            'invite': '👥 Invite',
            'register': '🆕 Register',
            'card_key': '🎫 Card Key'
        }
        type_label = type_labels.get(txn_type.lower(), f'❓ {txn_type.title()}')
        
        # Clean description for users
        clean_desc = description
        if "/approve" in clean_desc:
            clean_desc = clean_desc.replace("Manual Approval (/approve)", "Manual Top-up")
        if "Manual Approval (PayWay)" in clean_desc:
            clean_desc = clean_desc.replace("Manual Approval (PayWay)", "Top-up")
        if "Admin AddGems" in clean_desc:
            clean_desc = clean_desc.replace("Admin AddGems", "Reward")
        if "Admin Reward" in clean_desc:
            clean_desc = clean_desc.replace("Admin Reward", "Reward")
            
        # Hide internal IDs from descriptions if they are too technical
        clean_desc = clean_desc.split(" | Bank:")[0].split(" | ID:")[0]

        msg += f"**{idx}. {type_label}**\n"
        # Fix sign: sign variable is already set above, but amount is negative for spend.
        # Let's use absolute value for spend displays to avoid double minus.
        display_amount = abs(amount)
        msg += f"{color} Amount: `{sign}{display_amount} Gems`\n"
        msg += f"📅 Time: `{created_at}`\n"
        
        # NOTE: proof links (chat_link) and trx_id are HIDDEN for users per request.
        # But we can keep Bank ID if you want users to see it for support? 
        # User said "user should not see this 2 fields", pointing at proof link and note with /approve.
        
        if clean_desc and clean_desc != 'N/A' and clean_desc != 'Balance added':
            msg += f"📝 Note: {clean_desc}\n"
        
        msg += "━━━━━━━━━━━━━━━━━━\n\n"
    
    msg += "💡 *Showing last 10 transactions*"
    return msg


def get_deposit_notification(amount_usd: float, gems_added: int, trx_id: str) -> str:
    """Standard success message for all types of deposits"""
    return (
        "✅ **DEPOSIT RECEIVED!**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"💰 **Amount:** `${amount_usd:.2f}`\n"
        f"💎 **Gems Added:** `+{gems_added}`\n"
        f"🆔 **Trx ID:** `{trx_id}`\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Thank you for your support! 🙏"
    )


def get_rejection_notification(reason: str = None) -> str:
    """Standard rejection message for invalid payments"""
    msg = (
        "❌ **PAYMENT REJECTED**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "We could not verify your payment proof.\n"
    )
    if reason:
        msg += f"📝 **Reason:** `{reason}`\n"
    else:
        msg += "📝 **Reason:** `Invalid or unclear screenshot`\n"
    
    msg += (
        "━━━━━━━━━━━━━━━━━━\n"
        "**What should you do?**\n"
        "1. Check if the amount and ID are visible.\n"
        "2. Send a new screenshot using `/proof`.\n"
        "3. If you need help, contact our support team below.\n\n"
        f"👉 [Contact Admin Support]({ADMIN_SUPPORT_LINK})"
    )
    return msg
