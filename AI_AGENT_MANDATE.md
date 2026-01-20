# AI AGENT MANDATE - Deployment & Development Guidelines

## Critical Deployment Workflow

### ⚠️ MANDATORY: Always Commit to Main First

**NEVER push directly to production branch (without user's confirmation)!**

The correct deployment workflow is:

```bash
# 1. Commit changes to main branch with descriptive message
git add <modified-files>
git commit -m "feat: descriptive message about changes

- Detail 1
- Detail 2
- Detail 3"

# 2. Push to main
git push origin main

# 3. Switch to production branch
git checkout production

# 4. Merge main into production
git merge main -m "Merge main into production: brief summary"

# 5. Push to production (triggers auto-deployment)
git push origin production

# 6. Switch back to main
git checkout main
```

### Deployment Architecture

**Platform**: Google Cloud Run (NOT Railway)

**Trigger**: GitHub Actions workflow (`.github/workflows/deploy.yml`)
- Automatically deploys when code is pushed to `production` branch
- Builds Docker image and deploys to Cloud Run
- Region: `asia-southeast1`
- Service: `tgbot-verify`
- Resources: 4Gi Memory, 2 CPU (Required for Chromium)

### Required GitHub Secrets

The following secrets MUST be configured in GitHub repository settings:

1. **GCP_PROJECT_ID** - Google Cloud project ID
2. **GCP_SA_KEY** - Service account JSON key (full credentials)
3. **BOT_TOKEN** - Telegram bot token from @BotFather
4. **ADMIN_USER_ID** - Telegram user ID of admin
5. **WEBHOOK_URL** - Cloud Run service URL (e.g., `https://tgbot-verify-xxxxx-uc.a.run.app`)

### Bot Runtime Modes

The bot has two modes based on environment detection:

#### Cloud Run (Webhook Mode)
- Detected by `K_SERVICE` environment variable
- Requires `WEBHOOK_URL` to be set
- If `WEBHOOK_URL` is missing → Starts safety health-check server (bot won't work!)
- Port: 8080 (from `PORT` env var)

#### Local Development (Polling Mode)
- No `K_SERVICE` environment variable
- Uses polling to get updates from Telegram
- Run with: `python bot.py`

### Common Deployment Issues

#### Issue: Bot Not Responding After Deployment
**Cause**: Missing or incorrect `WEBHOOK_URL` secret
**Solution**: 
1. Get Cloud Run service URL from GCP Console
2. Set as `WEBHOOK_URL` secret in GitHub
3. Redeploy

#### Issue: Playwright Timeout Errors
**Cause**: Missing container-safe browser launch arguments
**Solution**: Ensure all `img_generator.py` files have:
```python
browser = p.chromium.launch(
    headless=True,
    timeout=60000,
    args=[
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--disable-software-rasterizer',
        '--disable-extensions',
    ]
)
```

### Code Quality Standards

#### Commit Message Format
```
<type>: <short summary>

<detailed description>
- Point 1
- Point 2

<optional footer>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

#### Python Code Standards
- All Chinese comments MUST be translated to English
- Use descriptive variable names
- Add docstrings to all functions
- Handle exceptions gracefully

### Testing Before Deployment

1. **Syntax Check**: Run `python3 -m py_compile <file>` on modified files
2. **Local Test**: Test bot locally with `python bot.py`
3. **Code Review**: Review all changes before committing

### Monitoring & Debugging

#### View Cloud Run Logs
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=tgbot-verify" --limit 50
```

#### Check Webhook Status
```
https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo
```

#### Local Restart Script
```bash
./restart.sh  # Kills and restarts bot locally
```

### File Structure Reference

**Image Generators** (Playwright-based):
- `one/img_generator.py` - Gemini Pro verification
- `k12/img_generator.py` - ChatGPT Teachers verification
- `youtube/img_generator.py` - YouTube Premium verification
- `spotify/img_generator.py` - Spotify Premium verification
- `Boltnew/img_generator.py` - Bolt.new verification

**Core Files**:
- `bot.py` - Main bot entry point
- `config.py` - Configuration and constants
- `database/` - Database abstraction (MySQL/Firestore)
- `handlers/` - Command handlers

**Deployment**:
- `.github/workflows/deploy.yml` - GitHub Actions workflow
- `Dockerfile` - Container image definition
- `requirements.txt` - Python dependencies

### Emergency Rollback

If deployment fails:

```bash
# 1. Revert production branch to previous commit
git checkout production
git reset --hard HEAD~1
git push origin production --force

# 2. Or revert specific commit
git revert <commit-hash>
git push origin production
```

### Best Practices

1. ✅ Always test locally before committing
2. ✅ Write descriptive commit messages
3. ✅ Commit to main first, then merge to production
4. ✅ Verify GitHub secrets are configured
5. ✅ Monitor deployment logs after pushing
6. ✅ Test bot immediately after deployment
7. ✅ Keep Chinese translations to English
8. ✅ Use proper error handling in all code

### Quick Reference Commands

```bash
# Check current branch
git branch

# View recent commits
git log --oneline -5

# Check file syntax
python3 -m py_compile <file.py>

# View deployment status
# Go to: https://github.com/kakadahor/tgbot-verify/actions

# Local bot restart
./restart.sh
```

---

**Last Updated**: 2026-01-20
**Maintained By**: AI Agent (Antigravity)
