# Code Location Reference: /verify Command Details

This document shows exactly where each detail of the `/verify` command is defined in the codebase.

## 📋 Service Details Breakdown

### **Service Name: "Gemini One Pro"**

**Display Name Locations:**

1. **Command Handler Docstring**
   - File: [`handlers/verify_commands.py:32`](file:///Users/kakada/Documents/GitHub/tgbot-verify/handlers/verify_commands.py#L32)
   ```python
   async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
       """Handle /verify command - Gemini One Pro"""
   ```

2. **Usage Message**
   - File: [`handlers/verify_commands.py:45`](file:///Users/kakada/Documents/GitHub/tgbot-verify/handlers/verify_commands.py#L45)
   ```python
   get_verify_usage_message("/verify", "Gemini One Pro")
   ```

3. **Processing Message**
   - File: [`handlers/verify_commands.py:67`](file:///Users/kakada/Documents/GitHub/tgbot-verify/handlers/verify_commands.py#L67)
   ```python
   f"Starting Gemini One Pro verification...\n"
   ```

4. **Help Message**
   - File: [`utils/messages.py:66`](file:///Users/kakada/Documents/GitHub/tgbot-verify/utils/messages.py#L66)
   ```python
   f"/verify <link> - Gemini One Pro verification (-{VERIFY_COST} credits)\n"
   ```

**Database Identifier:**

- File: [`handlers/verify_commands.py:79`](file:///Users/kakada/Documents/GitHub/tgbot-verify/handlers/verify_commands.py#L79)
```python
db.add_verification(
    user_id,
    "gemini_one_pro",  # ← This is stored in database
    url,
    "success" if result["success"] else "failed",
    str(result),
)
```

---

### **Cost: "3 credits" → Actually "1 credit"**

**⚠️ Important Discovery:** The cost is actually **1 credit**, not 3!

**File:** [`config.py:17`](file:///Users/kakada/Documents/GitHub/tgbot-verify/config.py#L17)
```python
# Credit configuration
VERIFY_COST = 1  # Credits consumed per verification
CHECKIN_REWARD = 1  # Check-in reward credits
INVITE_REWARD = 2  # Invitation reward credits
REGISTER_REWARD = 1  # Registration reward credits
```

**Where it's used:**

1. **Balance Check**
   - File: [`handlers/verify_commands.py:51`](file:///Users/kakada/Documents/GitHub/tgbot-verify/handlers/verify_commands.py#L51)
   ```python
   if user["balance"] < VERIFY_COST:
   ```

2. **Deduction**
   - File: [`handlers/verify_commands.py:62`](file:///Users/kakada/Documents/GitHub/tgbot-verify/handlers/verify_commands.py#L62)
   ```python
   if not db.deduct_balance(user_id, VERIFY_COST):
   ```

3. **Refund on Failure**
   - File: [`handlers/verify_commands.py:93`](file:///Users/kakada/Documents/GitHub/tgbot-verify/handlers/verify_commands.py#L93)
   ```python
   db.add_balance(user_id, VERIFY_COST)
   ```

**How to Change the Cost:**

Edit [`config.py:17`](file:///Users/kakada/Documents/GitHub/tgbot-verify/config.py#L17):
```python
VERIFY_COST = 3  # Change to 3 credits
```

Or set in `.env` file:
```bash
VERIFY_COST=3
```

---

### **Verification Type: "Student verification"**

This is determined by the **SheerID Program ID** and the verification flow.

**File:** [`one/config.py:4`](file:///Users/kakada/Documents/GitHub/tgbot-verify/one/config.py#L4)
```python
# SheerID API Configuration
PROGRAM_ID = '67c8c14f5f17a83b745e3f82'  # ← Gemini One Pro program
SHEERID_BASE_URL = 'https://services.sheerid.com'
```

**What it does:**
- This `PROGRAM_ID` tells SheerID which verification program to use
- Different programs have different requirements (student, teacher, military, etc.)
- Gemini One Pro uses a **student verification** program

---

### **What it does: "Generates Penn State student ID and submits to SheerID"**

**Components:**

1. **School Configuration**
   - File: [`one/config.py:12-133`](file:///Users/kakada/Documents/GitHub/tgbot-verify/one/config.py#L12-L133)
   ```python
   SCHOOLS = {
       '2565': {
           'id': 2565,
           'name': 'Pennsylvania State University-Main Campus',
           'domain': 'PSU.EDU',
           ...
       },
       # 9 more Penn State campuses
   }
   DEFAULT_SCHOOL_ID = '2565'  # Main Campus
   ```

2. **Name Generation**
   - File: [`one/name_generator.py`](file:///Users/kakada/Documents/GitHub/tgbot-verify/one/name_generator.py)
   - Generates random American names using patterns

3. **Student ID Card Generation**
   - File: [`one/img_generator.py`](file:///Users/kakada/Documents/GitHub/tgbot-verify/one/img_generator.py)
   - Creates HTML-based student ID card
   - Converts to PNG using Playwright
   - **Recently improved** with date fields (lines 269-289)

4. **SheerID Submission**
   - File: [`one/sheerid_verifier.py`](file:///Users/kakada/Documents/GitHub/tgbot-verify/one/sheerid_verifier.py)
   - Submits student info to SheerID API
   - Uploads student ID image to S3
   - Completes verification workflow

---

### **Status: "✅ Just improved with better date fields"**

**Recent Improvements:**

File: [`one/img_generator.py:269-289`](file:///Users/kakada/Documents/GitHub/tgbot-verify/one/img_generator.py#L269-L289)

Added:
```html
<!-- Enrollment Verification Section -->
<div style="background: #fff9e6; border: 2px solid #ffd700; ...">
    <div>
        <div class="info-label">📅 Issue Date</div>
        <div class="info-val">{date}</div>  <!-- Current date -->
    </div>
    <div>
        <div class="info-label">📆 Current Academic Year</div>
        <div class="info-val">2025-2026</div>
    </div>
    <div>
        <div class="info-label">✅ Valid Through</div>
        <div class="info-val">May 15, 2026</div>
    </div>
</div>
```

**Date Format Change:**

File: [`one/img_generator.py:38`](file:///Users/kakada/Documents/GitHub/tgbot-verify/one/img_generator.py#L38)
```python
# Old: date = datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')
# New: date = datetime.now().strftime('%B %d, %Y')
# Result: "January 16, 2026" instead of "01/16/2026, 11:34:12 PM"
```

---

## 🗂️ Complete File Structure

```
/verify command components:
├── handlers/verify_commands.py    # Main command handler
├── config.py                       # Global config (VERIFY_COST)
├── one/
│   ├── config.py                  # SheerID program ID, schools
│   ├── name_generator.py          # Random name generation
│   ├── img_generator.py           # Student ID card creation
│   └── sheerid_verifier.py        # SheerID API interaction
└── utils/
    └── messages.py                # Help and usage messages
```

---

## 🔧 How to Customize

### **Change Service Name Display:**
Edit: `handlers/verify_commands.py` and `utils/messages.py`

### **Change Cost:**
Edit: `config.py` line 17 or add `VERIFY_COST=3` to `.env`

### **Change School:**
Edit: `one/config.py` line 136 (`DEFAULT_SCHOOL_ID`)

### **Change Program (Service Type):**
Edit: `one/config.py` line 4 (`PROGRAM_ID`)

### **Improve Document Quality:**
Edit: `one/img_generator.py` (HTML template and styling)

---

## 📊 Summary Table

| Detail | Location | Line | Value |
|--------|----------|------|-------|
| Service Name | `handlers/verify_commands.py` | 32 | "Gemini One Pro" |
| Database ID | `handlers/verify_commands.py` | 79 | "gemini_one_pro" |
| Cost | `config.py` | 17 | `1` credit |
| Program ID | `one/config.py` | 4 | `67c8c14f5f17a83b745e3f82` |
| School | `one/config.py` | 136 | Penn State (2565) |
| Type | SheerID Program | - | Student |
| Status | `one/img_generator.py` | 269-289 | Improved ✅ |

---

**All details are now documented with exact file locations and line numbers!** 🎯
