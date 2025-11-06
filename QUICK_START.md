# Quick Start Guide

## 🚀 First Time Setup (Do This Once)

### Step 1: Navigate to the project folder
```bash
cd yoga-therapy
```

### Step 2: Run the setup script

**Windows:**
```bash
setup.bat
```

**macOS/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

This will:
- ✅ Create a virtual environment
- ✅ Install all required packages (Flask, Werkzeug, SQLAlchemy, etc.)
- ✅ Run database migration (ensures database schema is up-to-date)
- ✅ Set up everything you need

**That's it! Setup is complete.**

---

## ▶️ Running the App (Every Time After Setup)

### Option 1: Use the Run Script (EASIEST - Recommended)

**Windows:**
```bash
run.bat
```

**macOS/Linux:**
```bash
./run.sh
```

**That's it!** The app will:
- ✅ Check and update database schema automatically
- ✅ Start at http://127.0.0.1:5000

### Option 2: Manual Run (If you prefer)

**Windows:**
```bash
venv\Scripts\activate
python web\app.py
```

**macOS/Linux:**
```bash
source venv/bin/activate
python web/app.py
```

**Important:** You MUST see `(venv)` in your terminal prompt before running the app!

---

## 📝 Summary

**First time:**
1. Run `setup.bat` (Windows) or `./setup.sh` (macOS/Linux)

**Every other time:**
1. Run `run.bat` (Windows) or `./run.sh` (macOS/Linux)

**That's all you need to remember!**

---

## ❓ Troubleshooting

**Problem:** "No module named Werkzeug" or "No module named Flask"

**Solution:** You forgot to use the run script or activate the venv.

- **Easiest fix:** Use `run.bat` (Windows) or `./run.sh` (macOS/Linux)
- **Manual fix:** Activate venv first: `venv\Scripts\activate` then run `python web\app.py`

**Problem:** "Virtual environment not found"

**Solution:** Run the setup script again: `setup.bat` (Windows) or `./setup.sh` (macOS/Linux)

