# Database Migration Guide

## 🎯 Overview

Your bot now supports **both MySQL and Firestore** databases! You can easily switch between them.

---

## 📁 Project Structure

```
database/
├── __init__.py          # Database factory (switch between MySQL/Firestore)
├── base.py              # Abstract interface
├── mysql/
│   ├── __init__.py      # MySQL wrapper
│   └── mysql_db.py      # Your original MySQL code (preserved)
└── firestore/
    ├── __init__.py      # Firestore implementation
    └── (implementation in__init__.py)
```

---

## 🔄 How to Switch Databases

### **Option 1: Environment Variable (Recommended)**

Edit your `.env` file:

**Use MySQL:**
```bash
DB_TYPE=mysql
```

**Use Firestore:**
```bash
DB_TYPE=firestore
GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-credentials.json
```

Then restart the bot:
```bash
./venv/bin/python bot.py
```

### **Option 2: Programmatically**

In your code:

```python
from database import get_database

# Use MySQL
db = get_database('mysql')

# Use Firestore
db = get_database('firestore')
```

---

## 📊 Database Comparison

| Feature | MySQL | Firestore |
|---------|-------|-----------|
| **Cost** | $0 (local) or $10-15/month (cloud) | $0-2/month |
| **Setup** | Medium | Medium |
| **Scalability** | Good | Excellent |
| **Query Language** | SQL | NoSQL |
| **Viewer** | TablePlus, MySQL Workbench | Firebase Console |
| **Backups** | Manual mysqldump | Auto-backup available |

---

## 🗄️ Data Migration

### **MySQL to Firestore**

Coming soon - migration script will be created if needed.

### **Firestore to MySQL**

Coming soon - migration script will be created if needed.

---

## ✅ Testing

### **Test MySQL:**

```bash
cd /Users/kakada/Documents/GitHub/tgbot-verify

# Set environment
export DB_TYPE=mysql

# Run bot
./venv/bin/python bot.py
```

Expected output: `✅ Using MySQL database`

### **Test Firestore:**

```bash
cd /Users/kakada/Documents/GitHub/tgbot-verify

# Set environment
export DB_TYPE=firestore
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-credentials.json

# Install Firestore library (if not installed)
./venv/bin/pip install google-cloud-firestore

# Run bot
./venv/bin/python bot.py
```

Expected output: `✅ Using Firestore database`

---

## 🎯 Deployment Options

### **MySQL Deployment:**
- **Local:** Your Mac
- **Cloud:** Railway ($5/month), DigitalOcean ($6/month)
- **Database:** MySQL (local or cloud)

### **Firestore Deployment:**
- **Cloud:** Firebase Cloud Run
- **Database:** Firestore (NoSQL)
- **Cost:** $0-2/month

---

## 📝 Notes

1. **Original MySQL code preserved:** Your original `database_mysql.py` is copied to `database/mysql/mysql_db.py`
2. **No code changes needed:** Just change `DB_TYPE` in `.env`
3. **Same interface:** Both databases have the same methods
4. **Easy switching:** Change one environment variable

---

## 🚀 Recommended Setup

**Development (Local):**
- Use MySQL (what you have now)
- Easy to inspect data with TablePlus
- No cloud dependencies

**Production (Cloud):**
- Use Firestore
- Free tier ($0-2/month)
- Scalable
- Built-in Firebase Console

---

**Your original MySQL code is safe and preserved!** ✅
