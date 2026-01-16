# Firebase Deployment Guide

## 🔥 Deploy Your Bot to Firebase with Firestore

This guide shows you how to deploy your bot using Google Cloud Firebase and Firestore database.

---

## 📊 What You're Getting

**Services:**
- ✅ **Cloud Run** - Runs your bot 24/7
- ✅ **Firestore** - NoSQL database (replaces MySQL)
- ✅ **Free Tier** - $0-2/month for small usage

**Benefits:**
- ✅ No MySQL costs
- ✅ Scalable infrastructure
- ✅ Built-in database viewer
- ✅ Google Cloud reliability

---

## 🎯 Part 1: Prerequisites (5 minutes)

### **Step 1: Install Google Cloud SDK**

**macOS:**
```bash
brew install --cask google-cloud-sdk
```

**Or download from:** https://cloud.google.com/sdk/docs/install

### **Step 2: Install Firebase CLI**

```bash
npm install -g firebase-tools
```

### **Step 3: Install Firestore Library**

```bash
cd /Users/kakada/Documents/GitHub/tgbot-verify
./venv/bin/pip install google-cloud-firestore
```

### **Step 4: Update requirements.txt**

Add Firestore to dependencies:
```bash
echo "google-cloud-firestore>=2.14.0" >> requirements.txt
```

---

## 🔥 Part 2: Firebase Project Setup (10 minutes)

### **Step 1: Create Firebase Project**

1. Go to https://console.firebase.google.com
2. Click "Add project"
3. Project name: `tgbot-verify` (or any name)
4. Disable Google Analytics (optional)
5. Click "Create project"

### **Step 2: Enable Firestore**

1. In Firebase console, click "Firestore Database"
2. Click "Create database"
3. Select "Production mode"
4. Choose location: `us-central1` (or closest to you)
5. Click "Enable"

### **Step 3: Create Service Account**

1. Go to Project Settings → Service Accounts
2. Click "Generate new private key"
3. Download JSON file
4. Save as: `/Users/kakada/Documents/GitHub/tgbot-verify/firebase-credentials.json`

**Important:** Never commit this file to Git!

---

## ⚙️ Part 3: Configure Your Bot (5 minutes)

### **Step 1: Update .env File**

Add this line to your `.env`:

```bash
# Database Configuration
DB_TYPE=firestore  # Change from 'mysql' to 'firestore'

# Firebase Configuration
GOOGLE_APPLICATION_CREDENTIALS=/Users/kakada/Documents/GitHub/tgbot-verify/firebase-credentials.json
```

### **Step 2: Update .gitignore**

Make sure these lines are in `.gitignore`:

```
# Firebase
firebase-credentials.json
*.json  # Service account keys
```

### **Step 3: Test Firestore Locally**

```bash
cd /Users/kakada/Documents/GitHub/tgbot-verify

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS=/Users/kakada/Documents/GitHub/tgbot-verify/firebase-credentials.json
export DB_TYPE=firestore

# Run bot
./venv/bin/python bot.py
```

You should see: `✅ Using Firestore database`

---

## 🚀 Part 4: Deploy to Cloud Run (10 minutes)

### **Step 1: Create Dockerfile**

Already created in your project. Review it to ensure it's correct.

### **Step 2: Enable Required APIs**

```bash
# Login to Google Cloud
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable firestore.googleapis.com
```

### **Step 3: Deploy to Cloud Run**

```bash
cd /Users/kakada/Documents/GitHub/tgbot-verify

# Deploy
gcloud run deploy tgbot-verify \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="BOT_TOKEN=YOUR_BOT_TOKEN,ADMIN_USER_ID=245500749,DB_TYPE=firestore" \
  --min-instances=1 \
  --max-instances=1
```

**Environment Variables to Set:**
- `BOT_TOKEN` - Your bot token
- `ADMIN_USER_ID` - Your Telegram user ID
- `CHANNEL_USERNAME` - Your channel
- `CHANNEL_URL` - Your channel URL
- `DB_TYPE` - Set to `firestore`

---

## 💾 Part 5: Access Firestore Data

### **Method 1: Firebase Console (Easiest)**

1. Go to https://console.firebase.google.com
2. Select your project
3. Click "Firestore Database"
4. Browse collections:
   - `users` - All registered users
   - `verifications` - Verification history
   - `card_keys` - Generated card keys
   - `card_key_usage` - Card key usage
   - `invitations` - User invitations

### **Method 2: Firebase CLI**

```bash
# Export data
firebase firestore:export ./firestore-backup

# Import data
firebase firestore:import ./firestore-backup
```

---

## 🔄 Switching Between MySQL and Firestore

### **Use MySQL (Local Development):**

```bash
# In .env file
DB_TYPE=mysql

# Restart bot
./venv/bin/python bot.py
```

You'll see: `✅ Using MySQL database`

### **Use Firestore (Production):**

```bash
# In .env file
DB_TYPE=firestore

# Set credentials
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-credentials.json

# Restart bot
./venv/bin/python bot.py
```

You'll see: `✅ Using Firestore database`

---

## 📊 Cost Estimate

**Firebase Free Tier:**
- Firestore: 1GB storage, 50K reads/day, 20K writes/day
- Cloud Run: 2M requests/month, 360K GB-seconds

**Your Bot Usage:**
- Firestore: ~100MB storage, ~10K reads/day, ~2K writes/day
- Cloud Run: ~1M requests/month, ~200K GB-seconds

**Expected Cost:** $0-2/month ✅

**Compared to:**
- Railway: $5/month
- Render + MySQL: $0/month (but complex setup)

---

## 🔧 Troubleshooting

### **Issue: "Firestore not available"**

**Solution:**
```bash
./venv/bin/pip install google-cloud-firestore
```

### **Issue: "Could not load credentials"**

**Solution:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-credentials.json
```

### **Issue: "Permission denied"**

**Solution:**
1. Check service account has Firestore permissions
2. Verify JSON file path is correct

---

## 📋 Deployment Checklist

- [ ] Firebase project created
- [ ] Firestore database enabled
- [ ] Service account JSON downloaded
- [ ] Firestore library installed
- [ ] .env file updated with `DB_TYPE=firestore`
- [ ] Tested locally with Firestore
- [ ] Cloud Run deployed
- [ ] Environment variables set
- [ ] Bot responds on Telegram
- [ ] Firestore data visible in console

---

## 🎉 Success!

Your bot is now running on Firebase with Firestore!

**Next Steps:**
1. Test all commands (`/start`, `/verify`, etc.)
2. Check Firestore console for data
3. Monitor costs in Firebase console
4. Set up alerts for usage limits

---

**Estimated Time:** 30 minutes  
**Cost:** $0-2/month  
**Difficulty:** Medium

---

**Need help?** Check Firebase documentation or review this guide.
