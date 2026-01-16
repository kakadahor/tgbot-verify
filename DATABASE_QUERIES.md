# Useful Database Queries

## Connection Info
```bash
mysql -u tgbot_user -ptgbot_password_123 tgbot_verify
```

## Common Queries

### View All Users
```sql
SELECT user_id, username, full_name, balance, is_blocked 
FROM users 
ORDER BY created_at DESC;
```

### View Your Account
```sql
SELECT * FROM users WHERE user_id = 245500749;
```

### View Recent Verifications
```sql
SELECT 
    v.created_at,
    u.full_name,
    v.verification_type,
    v.status,
    v.verification_id
FROM verifications v
JOIN users u ON v.user_id = u.user_id
ORDER BY v.created_at DESC
LIMIT 10;
```

### View All Card Keys
```sql
SELECT 
    key_code,
    credits,
    max_uses,
    current_uses,
    expire_at,
    created_at
FROM card_keys
ORDER BY created_at DESC;
```

### View Card Key Usage
```sql
SELECT 
    u.full_name,
    ck.key_code,
    ck.credits,
    cku.used_at
FROM card_key_usage cku
JOIN users u ON cku.user_id = u.user_id
JOIN card_keys ck ON cku.key_id = ck.id
ORDER BY cku.used_at DESC;
```

### View User Invitations
```sql
SELECT 
    u1.full_name as inviter,
    u2.full_name as invited,
    i.created_at
FROM invitations i
JOIN users u1 ON i.inviter_id = u1.user_id
JOIN users u2 ON i.invited_id = u2.user_id
ORDER BY i.created_at DESC;
```

### Check Total Users
```sql
SELECT COUNT(*) as total_users FROM users;
```

### Check Total Verifications
```sql
SELECT 
    verification_type,
    status,
    COUNT(*) as count
FROM verifications
GROUP BY verification_type, status;
```

### View Blacklisted Users
```sql
SELECT user_id, username, full_name, created_at
FROM users
WHERE is_blocked = 1;
```

### View Top Users by Balance
```sql
SELECT user_id, username, full_name, balance
FROM users
ORDER BY balance DESC
LIMIT 10;
```

## Database Structure

### Tables
- `users` - User accounts and balances
- `verifications` - Verification history
- `card_keys` - Generated card keys
- `card_key_usage` - Card key redemption history
- `invitations` - User invitation tracking

### Users Table Schema
```sql
DESCRIBE users;
```

### Verifications Table Schema
```sql
DESCRIBE verifications;
```

## Backup Database
```bash
mysqldump -u tgbot_user -ptgbot_password_123 tgbot_verify > backup_$(date +%Y%m%d).sql
```

## Restore Database
```bash
mysql -u tgbot_user -ptgbot_password_123 tgbot_verify < backup_20260116.sql
```
