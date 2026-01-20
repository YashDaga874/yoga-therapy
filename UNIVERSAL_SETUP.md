# 🚀 Universal Setup Guide - Works on Windows, Mac, and Linux

**Copy and paste these commands - they work on ANY computer!**

---

## 📋 STEP 1: Install Python (If Not Already Installed)

### Windows:
1. Go to: https://www.python.org/downloads/
2. Download and install Python
3. **IMPORTANT:** Check "Add Python to PATH" during installation
4. Restart your computer after installation

### Mac:
1. Python usually comes pre-installed
2. Or install from: https://www.python.org/downloads/
3. Or use Homebrew: `brew install python3`

### Linux:
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv
```

---

## ⚙️ STEP 2: First Time Setup (Copy and Paste These Commands)

**Open Terminal/Command Prompt and navigate to the project folder, then run:**

### Windows (Command Prompt or PowerShell):
```cmd
cd yoga-therapy
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python add_kosha_field.py
python add_database_indexes.py
python add_practice_code_field.py
```

### Mac/Linux (Terminal):
```bash
cd yoga-therapy
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python add_kosha_field.py
python add_database_indexes.py
python add_practice_code_field.py
```

**That's it! Setup is complete.**

---

## ▶️ STEP 3: Run the Application (Every Time)

### Windows:
```cmd
cd yoga-therapy
venv\Scripts\activate
python web/app.py
```

### Mac/Linux:
```bash
cd yoga-therapy
source venv/bin/activate
python web/app.py
```

**The app will start at: http://127.0.0.1:5000**

**To stop:** Press `Ctrl + C` in the terminal

---

## 🔄 Alternative: Using Scripts (If They Work)

### Windows:
```cmd
setup.bat
run.bat
```

### Mac/Linux:
```bash
chmod +x setup.sh run.sh
./setup.sh
./run.sh
```

**If scripts don't work, use the manual commands above!**

---

## ❓ Troubleshooting

### "python: command not found" or "python is not recognized"

**Windows:**
- Reinstall Python and check "Add Python to PATH"
- Restart computer
- Try `py` instead of `python`:
  ```cmd
  py -m venv venv
  venv\Scripts\activate
  ```

**Mac/Linux:**
- Try `python3` instead of `python`:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### "venv: command not found"

**Solution:**
```bash
# Windows
python -m pip install --upgrade pip
python -m venv venv

# Mac/Linux
python3 -m pip install --upgrade pip
python3 -m venv venv
```

### "pip: command not found"

**Solution:**
```bash
# Windows
python -m pip install -r requirements.txt

# Mac/Linux
python3 -m pip install -r requirements.txt
```

### "No module named 'flask'"

**Solution:**
Make sure virtual environment is activated, then:
```bash
pip install -r requirements.txt
```

### Port 5000 already in use

**Solution:**
Edit `web/app.py` and change the last line from:
```python
app.run(port=5000)
```
to:
```python
app.run(port=5001)
```
Then access at: http://127.0.0.1:5001

---

## 📝 Quick Reference Card

### First Time Setup:
```bash
# Windows
cd yoga-therapy
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python add_kosha_field.py
python add_database_indexes.py
python add_practice_code_field.py

# Mac/Linux
cd yoga-therapy
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python add_kosha_field.py
python add_database_indexes.py
python add_practice_code_field.py
```

### Every Time After Setup:
```bash
# Windows
cd yoga-therapy
venv\Scripts\activate
python web/app.py

# Mac/Linux
cd yoga-therapy
source venv/bin/activate
python web/app.py
```

---

## 🎯 Summary

**The universal approach (works everywhere):**

1. **Install Python** (if not installed)
2. **Navigate to project folder**
3. **Create virtual environment:** `python -m venv venv` (or `python3` on Mac/Linux)
4. **Activate it:**
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
5. **Install packages:** `pip install -r requirements.txt`
6. **Run migrations:** `python add_kosha_field.py` etc.
7. **Run app:** `python web/app.py`

**No scripts needed - just copy and paste these commands!** ✅
