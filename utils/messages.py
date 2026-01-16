"""Message Templates"""
from config import VERIFY_COST, HELP_NOTION_URL


def get_welcome_message(full_name: str, invited_by: bool = False) -> str:
    """Get the welcome message"""
    msg = (
        f"🎉 Welcome, {full_name}!\n"
        "You have successfully registered and received 1 credit.\n"
    )
    if invited_by:
        msg += "Thank you for joining via an invitation link. Your inviter has received 2 credits.\n"

    msg += (
        "\nThis bot can automatically complete SheerID verifications.\n"
        "Quick Start:\n"
        "/about - Learn about bot features\n"
        "/balance - Check your credit balance\n"
        "/help - View full command list\n\n"
        "Get more credits:\n"
        "/qd - Daily check-in\n"
        "/invite - Invite friends\n"
    )
    return msg


def get_about_message() -> str:
    """Get the about message"""
    return (
        "🤖 SheerID Auto-Verification Bot\n"
        "\n"
        "Features:\n"
        "- Automatically complete SheerID student/teacher verification\n"
        "- Supports Gemini One Pro, ChatGPT Teacher K12, Spotify Student, YouTube Student, Bolt.new Teacher certifications\n"
        "\n"
        "Earning Credits:\n"
        "- Registration: +1 credit\n"
        "- Daily check-in: +1 credit\n"
        "- Invite friends: +2 credits/person\n"
        "- Use card keys (according to key rules)\n"
        "\n"
        "How to Use:\n"
        "1. Start the verification on the website and copy the full verification link\n"
        "2. Send /verify, /verify2, /verify3, /verify4, or /verify5 with the link\n"
        "3. Wait for processing and check the results\n"
        "4. Bolt.new verification will automatically fetch the code; use /getV4Code <verification_id> for manual queries\n"
        "\n"
        "For more commands, send /help"
    )


def get_help_message(is_admin: bool = False) -> str:
    """Get the help message"""
    msg = (
        "📖 SheerID Auto-Verification Bot - Help\n"
        "\n"
        "User Commands:\n"
        "/start - Get started (Register)\n"
        "/about - Learn about bot features\n"
        "/balance - Check your credit balance\n"
        "/qd - Daily check-in (+1 credit)\n"
        "/invite - Generate invitation link (+2 credits/person)\n"
        "/use <key> - Use a card key to redeem credits\n"
        f"/verify <link> - Gemini One Pro verification (-{VERIFY_COST} credits)\n"
        f"/verify2 <link> - ChatGPT Teacher K12 verification (-{VERIFY_COST} credits)\n"
        f"/verify3 <link> - Spotify Student verification (-{VERIFY_COST} credits)\n"
        f"/verify4 <link> - Bolt.new Teacher verification (-{VERIFY_COST} credits)\n"
        f"/verify5 <link> - YouTube Student Premium verification (-{VERIFY_COST} credits)\n"
        "/getV4Code <verification_id> - Get Bolt.new verification code\n"
        "/help - View this help message\n"
        f"View troubleshooting: {HELP_NOTION_URL}\n"
    )

    if is_admin:
        msg += (
            "\nAdmin Commands:\n"
            "/addbalance <user_id> <amount> - Add credits to a user\n"
            "/block <user_id> - Blacklist a user\n"
            "/white <user_id> - Remove from blacklist\n"
            "/blacklist - View blacklisted users\n"
            "/genkey <key> <credits> [uses] [days] - Generate card keys\n"
            "/listkeys - View all card keys\n"
            "/broadcast <text> - Send notification to all users\n"
        )

    return msg


def get_insufficient_balance_message(current_balance: int) -> str:
    """Get the insufficient balance message"""
    return (
        f"Insufficient credits! Need {VERIFY_COST} credits, current balance: {current_balance}.\n\n"
        "How to get credits:\n"
        "- Daily check-in /qd\n"
        "- Invite friends /invite\n"
        "- Use a card key /use <key>"
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
