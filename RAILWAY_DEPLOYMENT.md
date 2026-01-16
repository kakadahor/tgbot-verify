# Railway Deployment Guide

## 🚀 Complete Step-by-Step Guide to Deploy Your Bot on Railway

This guide will help you deploy your Telegram bot to Railway in about 10-15 minutes.

---

## 📋 Prerequisites

Before starting, make sure you have:
- ✅ GitHub account
- ✅ Your bot code (this repository)
- ✅ Telegram Bot Token (from @BotFather)
- ✅ Admin User ID (your Telegram user ID)

---

## 🎯 Part 1: Prepare Your Code (5 minutes)

### **Step 1: Initialize Git Repository**

If you haven't already, initialize Git:

```bash
cd /Users/kakada/Documents/GitHub/tgbot-verify

# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Prepare for Railway deployment"
```

### **Step 2: Create GitHub Repository**

1. Go to https://github.com/new
2. Repository name: `tgbot-verify` (or any name you like)
3. Make it **Private** (recommended for bots)
4. **Don't** initialize with README (you already have code)
5. Click "Create repository"

### **Step 3: Push Code to GitHub**

```bash
# Add GitHub as remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/tgbot-verify.git

# Push code
git branch -M main
git push -u origin main
```

**✅ Checkpoint:** Your code is now on GitHub!

---

## 🚂 Part 2: Deploy on Railway (5 minutes)

### **Step 1: Sign Up for Railway**

1. Go to https://railway.app
2. Click "Login" → "Login with GitHub"
3. Authorize Railway to access your GitHub account
4. **No credit card required** for free tier!

### **Step 2: Create New Project**

1. Click "**New Project**"
2. Select "**Deploy from GitHub repo**"
3. If prompted, click "**Configure GitHub App**" and give Railway access to your repository
4. Select your repository: `tgbot-verify`
5. Click "**Deploy Now**"

Railway will automatically:
- ✅ Detect Python
- ✅ Install dependencies from `requirements.txt`
- ✅ Try to start your bot

**Note:** It will fail initially because we haven't set up the database and environment variables yet. That's normal!

### **Step 3: Add MySQL Database**

1. In your Railway project, click "**+ New**"
2. Select "**Database**"
3. Choose "**Add MySQL**"
4. Railway will create a MySQL database automatically

**✅ Checkpoint:** You now have a bot service and a MySQL database!

---

## ⚙️ Part 3: Configure Environment Variables (3 minutes)

### **Step 1: Get Database Connection Details**

1. Click on your **MySQL** service
2. Go to "**Variables**" tab
3. You'll see these variables (Railway creates them automatically):
   - `MYSQL_URL`
   - `MYSQL_HOST`
   - `MYSQL_PORT`
   - `MYSQL_USER`
   - `MYSQL_PASSWORD`
   - `MYSQL_DATABASE`

### **Step 2: Set Bot Environment Variables**

1. Click on your **Bot** service (the Python one)
2. Go to "**Variables**" tab
3. Click "**+ New Variable**"
4. Add these variables one by one:

**Required Variables:**

| Variable Name | Value | Where to Get It |
|--------------|-------|-----------------|
| `BOT_TOKEN` | Your bot token | @BotFather on Telegram |
| `ADMIN_USER_ID` | Your Telegram user ID | @userinfobot on Telegram |
| `CHANNEL_USERNAME` | Your channel username | Your Telegram channel |
| `CHANNEL_URL` | Your channel URL | Your Telegram channel |

**Database Variables (copy from MySQL service):**

| Variable Name | Value | Where to Get It |
|--------------|-------|-----------------|
| `MYSQL_HOST` | `${{MySQL.MYSQL_HOST}}` | Reference from MySQL service |
| `MYSQL_PORT` | `${{MySQL.MYSQL_PORT}}` | Reference from MySQL service |
| `MYSQL_USER` | `${{MySQL.MYSQL_USER}}` | Reference from MySQL service |
| `MYSQL_PASSWORD` | `${{MySQL.MYSQL_PASSWORD}}` | Reference from MySQL service |
| `MYSQL_DATABASE` | `${{MySQL.MYSQL_DATABASE}}` | Reference from MySQL service |

**How to reference MySQL variables:**
- Instead of copying values, use Railway's reference syntax
- Format: `${{MySQL.VARIABLE_NAME}}`
- This automatically links to your MySQL service

**Example:**
```
MYSQL_HOST = ${{MySQL.MYSQL_HOST}}
MYSQL_PORT = ${{MySQL.MYSQL_PORT}}
MYSQL_USER = ${{MySQL.MYSQL_USER}}
MYSQL_PASSWORD = ${{MySQL.MYSQL_PASSWORD}}
MYSQL_DATABASE = ${{MySQL.MYSQL_DATABASE}}
```

### **Step 3: Deploy**

After adding all variables:
1. Railway will automatically redeploy
2. Wait 1-2 minutes for deployment to complete
3. Check the "**Deployments**" tab to see status

**✅ Checkpoint:** Your bot should now be running!

---

## ✅ Part 4: Verify Deployment (2 minutes)

### **Step 1: Check Bot Logs**

1. Click on your Bot service
2. Go to "**Deployments**" tab
3. Click on the latest deployment
4. Check logs for:
   ```
   [INFO] MySQL database tables initialized successfully
   [INFO] Bot starting up...
   [INFO] Application started
   ```

### **Step 2: Test Your Bot**

1. Open Telegram
2. Find your bot
3. Send `/start`
4. You should get a welcome message in English!

### **Step 3: Test Database Access**

1. In Railway, click on your **MySQL** service
2. Go to "**Data**" tab
3. You should see tables: `users`, `verifications`, `card_keys`, etc.
4. Click on `users` table to see registered users

**✅ Success!** Your bot is now live on Railway! 🎉

---

## 💾 Part 5: Access Your Database

### **Method 1: Railway Dashboard (Easiest)**

1. Click on MySQL service
2. Go to "**Data**" tab
3. Browse tables visually
4. Run SQL queries in "**Query**" tab

### **Method 2: External Tool (TablePlus)**

1. In Railway, click MySQL service
2. Go to "**Connect**" tab
3. Copy connection details
4. Open TablePlus
5. Create new connection with Railway's details

---

## 🔧 Common Issues & Solutions

### **Issue 1: Bot Not Starting**

**Symptoms:** Deployment fails, bot doesn't respond

**Solution:**
1. Check logs in Railway dashboard
2. Verify all environment variables are set
3. Make sure `BOT_TOKEN` is correct
4. Check database connection

### **Issue 2: Database Connection Error**

**Symptoms:** Error: "Access denied for user"

**Solution:**
1. Make sure you're using `${{MySQL.VARIABLE_NAME}}` syntax
2. Verify MySQL service is running
3. Check that variables are linked correctly

### **Issue 3: Bot Responds in Chinese**

**Symptoms:** Bot sends Chinese messages

**Solution:**
1. Make sure you pushed the latest code with English translations
2. Redeploy: Settings → Redeploy

### **Issue 4: Out of Free Credits**

**Symptoms:** "Usage limit exceeded"

**Solution:**
1. Check usage in Railway dashboard
2. Optimize bot (reduce logging, etc.)
3. Upgrade to paid plan ($5/month minimum)

---

## 📊 Monitoring Your Bot

### **View Logs:**
1. Bot service → Deployments → Latest → Logs

### **View Metrics:**
1. Bot service → Metrics
2. See CPU, Memory, Network usage

### **View Database:**
1. MySQL service → Data
2. Browse all tables

---

## 🔄 Updating Your Bot

When you make changes to your code:

```bash
# Make changes to your code
git add .
git commit -m "Your update message"
git push origin main
```

Railway will automatically:
1. Detect the push
2. Rebuild your bot
3. Redeploy with new code
4. Restart the bot

**No manual deployment needed!** 🚀

---

## 💰 Cost Estimate

**Railway Free Tier:**
- $5 free credits per month
- Your bot usage: ~$4/month
- **You pay: $0** ✅

**What uses credits:**
- Bot running 24/7: ~$3/month
- MySQL database: ~$1/month
- Data transfer: ~$0.50/month

**If you exceed $5/month:**
- Railway will ask for payment method
- Minimum charge: $5/month
- You can set spending limits

---

## 🎯 Next Steps

After deployment:

1. ✅ **Test all commands** (`/verify`, `/verify2`, etc.)
2. ✅ **Add credits to your account** (use `/addbalance`)
3. ✅ **Generate test card keys** (use `/genkey`)
4. ✅ **Monitor logs** for any errors
5. ✅ **Set up backups** (see below)

---

## 💾 Database Backups

### **Manual Backup:**

1. Railway MySQL service → Data → Export
2. Download SQL file
3. Store securely

### **Automated Backup (Recommended):**

Create a GitHub Action or use Railway's backup feature (paid plans).

---

## 📞 Support

**Railway Issues:**
- Railway Discord: https://discord.gg/railway
- Railway Docs: https://docs.railway.app

**Bot Issues:**
- Check logs in Railway dashboard
- Review error messages
- Test locally first

---

## ✅ Deployment Checklist

Before going live:

- [ ] Code pushed to GitHub
- [ ] Railway project created
- [ ] MySQL database added
- [ ] All environment variables set
- [ ] Bot deployed successfully
- [ ] `/start` command works
- [ ] Database tables created
- [ ] Admin commands work
- [ ] Verification commands tested
- [ ] Database accessible

---

**Congratulations! Your bot is now live on Railway!** 🎉

**Deployment time:** ~10-15 minutes  
**Monthly cost:** $0 (free tier)  
**Uptime:** 24/7

---

## 🔗 Quick Links

- **Railway Dashboard:** https://railway.app/dashboard
- **Your Project:** (will be available after deployment)
- **GitHub Repo:** https://github.com/YOUR_USERNAME/tgbot-verify
- **Bot on Telegram:** @your_bot_username

---

**Need help?** Review this guide or check Railway's documentation!
