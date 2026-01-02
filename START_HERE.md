# 🚀 START HERE - How to Run This Project

## For ANYONE Setting Up This Project (First Time)

### Step-by-Step Instructions:

1. **Open your terminal/command prompt**

2. **Navigate to the project folder:**
   ```bash
   cd yoga-therapy
   ```

3. **Run the setup script:**

   **If you're on Windows:**
   ```bash
   setup.bat
   ```
   *(Just double-click `setup.bat` or run it from command prompt)*

   **If you're on macOS or Linux:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

4. **Wait for setup to complete** (takes 1-2 minutes)
   - The setup script will automatically:
     - Create virtual environment
     - Install dependencies
     - Run database migration (ensures database schema is up-to-date)

**✅ Setup Complete!** The database file (`yoga_therapy.db`) is already included in the repository with sample data, so you're ready to go!

---

## Running the App (Every Time You Want to Use It)

### The EASIEST Way (Recommended):

**Windows:**
```bash
run.bat
```
*(Just double-click `run.bat` or run it from command prompt)*

**macOS/Linux:**
```bash
./run.sh
```

**That's it!** The app will:
- ✅ Automatically check and update database schema
- ✅ Start at http://127.0.0.1:5000

---

### Alternative Way (If You Prefer Manual Control):

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

**Important:** Make sure you see `(venv)` in your terminal prompt before running the app!

---

## 🎯 Quick Reference

| Action | Command (Windows) | Command (macOS/Linux) |
|--------|-------------------|----------------------|
| **First time setup** | `setup.bat` | `./setup.sh` |
| **Run the app** | `run.bat` | `./run.sh` |
| **Stop the app** | Press `Ctrl+C` | Press `Ctrl+C` |

---

## ❓ Troubleshooting

**Q: I get "No module named Werkzeug" or "No module named Flask"**  
**A:** You forgot to use `run.bat`/`run.sh`. Use the run script - it handles everything automatically!

**Q: "Virtual environment not found"**  
**A:** Run `setup.bat` (Windows) or `./setup.sh` (macOS/Linux) first.

**Q: Setup worked, but now it doesn't?**  
**A:** Make sure you're using `run.bat`/`run.sh` - it automatically activates the virtual environment.

**Q: Do I need to run setup every time?**  
**A:** No! Only run `setup.bat`/`setup.sh` once. After that, just use `run.bat`/`run.sh` every time you want to use the app.

---

## 📝 Summary

**First time:** Run `setup.bat` (Windows) or `./setup.sh` (macOS/Linux)  
**Every other time:** Run `run.bat` (Windows) or `./run.sh` (macOS/Linux)

**It's that simple!**

