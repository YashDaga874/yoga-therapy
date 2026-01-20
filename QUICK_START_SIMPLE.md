# 🚀 Quick Start Guide - Simple Instructions

**For people who don't know much coding - just copy and paste these commands!**

> **⚠️ If `setup.bat` or `run.bat` don't work, see [UNIVERSAL_SETUP.md](UNIVERSAL_SETUP.md) for manual commands that work on ALL computers!**

---

## 📥 FIRST TIME SETUP (After pulling the latest from GitHub)

### Option A: Using Scripts (Windows - if they work)

**Copy and paste these commands one by one in your terminal (PowerShell/Command Prompt):**

```cmd
# Step 1: Navigate to the project folder
cd yoga-therapy

# Step 2: Run the setup script (this installs everything)
setup.bat

# Step 3: After setup completes, run the application
run.bat
```

### Option B: Manual Commands (Works on Windows, Mac, Linux)

**If scripts don't work, use these commands instead:**

**Windows:**
```cmd
cd yoga-therapy
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python add_kosha_field.py
python add_database_indexes.py
python add_practice_code_field.py
python web/app.py
```

**Mac/Linux:**
```bash
cd yoga-therapy
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python add_kosha_field.py
python add_database_indexes.py
python add_practice_code_field.py
python web/app.py
```

**That's it!** The app should open in your browser at `http://127.0.0.1:5000`

---

## 🔄 SUBSEQUENT RUNS (Every time you want to use the app)

### Option A: Using Script (Windows - if it works)

```cmd
run.bat
```

### Option B: Manual Commands (Works everywhere)

**Windows:**
```cmd
cd yoga-therapy
venv\Scripts\activate
python web/app.py
```

**Mac/Linux:**
```bash
cd yoga-therapy
source venv/bin/activate
python web/app.py
```

**That's all you need!** The app will start and open in your browser.

---

## 🔄 UPDATING FROM GITHUB (To get latest changes)

**If you want to get the latest updates from GitHub, run these commands:**

```powershell
# Step 1: Navigate to project folder
cd yoga-therapy

# Step 2: Discard local database changes (if you get an error)
git checkout -- yoga_therapy.db

# Step 3: Pull the latest changes
git pull origin main

# Step 4: Run the app
run.bat
```

---

## ❓ TROUBLESHOOTING

### ⚠️ **ERROR: "Your local changes to the following files would be overwritten by merge: yoga_therapy.db"**

**This is the most common error! Here's the fix:**

**Copy and paste these commands (one by one):**

```powershell
cd yoga-therapy
git checkout -- yoga_therapy.db
git pull origin main
run.bat
```

**What this does:**
1. Goes to your project folder
2. Discards your local database changes (it's okay, you'll get the latest version from GitHub)
3. Downloads the latest code from GitHub
4. Starts the app

**After running these commands, the error will be gone and your app will work!**

---

### If `setup.bat` gives an error or is not recognized:

**Use these manual commands instead (works on Windows, Mac, Linux):**

**Windows:**
```cmd
cd yoga-therapy
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python add_kosha_field.py
python add_database_indexes.py
python add_practice_code_field.py
python web/app.py
```

**Mac/Linux:**
```bash
cd yoga-therapy
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python add_kosha_field.py
python add_database_indexes.py
python add_practice_code_field.py
python web/app.py
```

**See [UNIVERSAL_SETUP.md](UNIVERSAL_SETUP.md) for complete instructions!**

### If `run.bat` says "Virtual environment not found":

**Run setup first:**
```powershell
setup.bat
```

### If you get "Python not found" error:

1. Make sure Python is installed from https://www.python.org/downloads/
2. During installation, check "Add Python to PATH"
3. Restart your terminal after installing Python

### If the app doesn't open in browser:

1. Wait a few seconds after running `run.bat`
2. Manually open your browser
3. Go to: `http://127.0.0.1:5000`

---

## 📝 SUMMARY

- **First time:** `cd yoga-therapy` → `setup.bat` → `run.bat`
- **Every other time:** Just run `run.bat`
- **To update:** `cd yoga-therapy` → `git checkout -- yoga_therapy.db` → `git pull origin main` → `run.bat`

That's it! 🎉
