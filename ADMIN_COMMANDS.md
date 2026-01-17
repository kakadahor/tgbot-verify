# Admin Commands Reference

This document provides a complete reference for all administrator commands available in the Telegram bot.

## Prerequisites

To use admin commands, your Telegram user ID must be set as `ADMIN_USER_ID` in the `.env` file.

## Available Commands

### 1. Add Gems to User

**Command:** `/addgems <user_id> <amount>`

**Description:** Add Gems to a specific user's account.

**Parameters:**
- `user_id` - The Telegram user ID of the target user
- `amount` - Number of Gems to add (positive integer)

**Examples:**
```
/addgems 123456789 100
/addgems 987654321 50
```

**Response:**
- Success: "✅ Successfully added {amount} Gems for user {user_id}. Current balance: {balance}"
- Error: "User does not exist." or "Invalid parameter format."

---

### 2. Block User (Blacklist)

**Command:** `/block <user_id>`

**Description:** Add a user to the blacklist, preventing them from using the bot.

**Parameters:**
- `user_id` - The Telegram user ID to block

**Example:**
```
/block 123456789
```

**Response:**
- Success: "✅ User {user_id} has been blacklisted."
- Error: "User does not exist." or "Operation failed."

---

### 3. Unblock User (Whitelist)

**Command:** `/white <user_id>`

**Description:** Remove a user from the blacklist, allowing them to use the bot again.

**Parameters:**
- `user_id` - The Telegram user ID to unblock

**Example:**
```
/white 123456789
```

**Response:**
- Success: "✅ User {user_id} has been removed from the blacklist."
- Error: "User does not exist." or "Operation failed."

---

### 4. View Blacklist

**Command:** `/blacklist`

**Description:** Display all users currently on the blacklist.

**Example:**
```
/blacklist
```

**Response:**
- Shows list of blacklisted users with their User ID, Username, and Full Name
- If empty: "Blacklist is empty."

---

### 5. Generate Card Key

**Command:** `/genkey <key_code> <amount> [uses] [expire_days]`

**Description:** Generate a redeemable card key that users can redeem for Gems.

**Parameters:**
- `key_code` - Unique identifier for the card key (string)
- `amount` - Number of Gems the key provides (positive integer)
- `uses` - (Optional) Maximum number of times the key can be used (default: 1)
- `expire_days` - (Optional) Number of days until expiration (default: never expires)

**Examples:**
```
/genkey test123 20
/genkey vip100 50 10
/genkey temp 30 1 7
```

**Response:**
- Success: Shows key details including code, Gems, uses, and expiry
- Error: "Key already exists or generation failed."

**Notes:**
- Each user can only use a specific card key once
- Keys track current uses vs maximum uses
- Expired keys cannot be redeemed

---

### 6. List Card Keys

**Command:** `/listkeys`

**Description:** Display all generated card keys and their status.

**Example:**
```
/listkeys
```

**Response:**
- Shows up to 20 most recent keys with:
  - Key code
  - Gems value
  - Uses (current/maximum)
  - Status (Valid, Expired, or Permanent)
  - Days remaining (if applicable)

---

### 7. Broadcast Message

**Command:** `/broadcast <message>`

**Description:** Send a message to all registered users.

**Parameters:**
- `message` - The text message to broadcast

**Alternative Usage:**
Reply to any message with `/broadcast` to send that message to all users.

**Examples:**
```
/broadcast Hello everyone! The bot is now in English!
/broadcast Maintenance scheduled for tomorrow at 10 AM.
```

**Response:**
- Shows progress: "📢 Starting broadcast to {count} users..."
- Final result: "✅ Broadcast complete! Success: {success} Failed: {failed}"

**Notes:**
- Messages are sent with a 0.05 second delay between each user to avoid rate limiting
- Failed sends are logged but don't stop the broadcast
- Only registered users receive the broadcast

---

## Finding User IDs

To use commands that require a user ID, you can:

### Method 1: Using @userinfobot
1. Open Telegram
2. Search for `@userinfobot`
3. Send any message to get your user ID

### Method 2: Check Database
If using Firestore, you can view the `users` collection in the Firebase Console.

### Method 3: Check Bot Logs
When users interact with the bot, their user IDs appear in the logs.

---

## Security Notes

1. **Admin-Only Access:** All these commands are restricted to the user ID specified in `ADMIN_USER_ID` in the `.env` file.

2. **No Confirmation:** Most commands execute immediately without confirmation. Be careful when using destructive commands like `/block`.

3. **Database Changes:** All commands directly modify the Firestore database.

4. **Broadcast Limits:** Telegram has rate limits. Broadcasting to thousands of users may take time and could trigger temporary restrictions.

---

## Common Use Cases

### Give Welcome Bonus
```
/genkey welcome2024 100
```
Share this key with new users for a welcome bonus.

### Reward Active Users
```
/addgems 123456789 50
```
Manually reward users for participation or feedback.

### Handle Abuse
```
/block 987654321
```
Block users who abuse the bot or violate terms.

### Announce Updates
```
/broadcast The bot now supports English! Try /help to see all commands.
```
Inform all users about new features or changes.

---

## Error Handling

If a command fails, check:
1. **Correct Format:** Ensure you're using the right syntax
2. **User Exists:** Verify the user ID is registered in the database
3. **Valid Parameters:** Check that numbers are positive integers
4. **Database Connection:** Ensure Firestore is working and accessible
5. **Bot Permissions:** Verify your user ID matches `ADMIN_USER_ID` in `.env`

---

## Support

For issues or questions about admin commands:
1. Check the bot logs in the terminal
2. Review the database using Firebase Console
3. Refer to the main documentation in `README.md`
