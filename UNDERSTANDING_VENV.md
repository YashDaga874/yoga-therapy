# Understanding the Virtual Environment Issue

## The Problem You Experienced

You installed packages with `pip install -r requirements.txt`, but then every time you run the app, you get:
- "No module named Werkzeug"
- "No module named Flask"
- "No module named SQLAlchemy"

**Why this happens:**
1. When you ran `pip install`, you (probably) had the virtual environment activated
2. Packages were installed into `venv/Lib/site-packages/`
3. BUT when you ran `python web/app.py`, you didn't activate the venv first
4. So Python used the **global/system Python**, which doesn't have those packages
5. That's why you had to "reinstall" - you were either:
   - Installing to global Python (wrong place)
   - Or installing to venv again (right place, but app still couldn't find them because venv wasn't active when running)

## Visual Explanation

```
Your System Has TWO Python Installations:

1. Global Python (system-wide)
   Location: C:\Users\YourName\AppData\Local\Programs\Python\...
   Packages: None (or very few)
   
2. Virtual Environment Python (project-specific)
   Location: D:\BTP YOGA CHECKING\yoga-therapy\venv\...
   Packages: Flask, Werkzeug, SQLAlchemy (installed here!)

When you run:
  python web/app.py  ❌ (uses global Python, no packages found!)

You need:
  venv\Scripts\activate
  python web/app.py  ✅ (uses venv Python, packages found!)
```

## The Solution

### Option 1: Use the Run Script (EASIEST - Recommended)
```bash
# Just double-click or run:
run.bat
```

This automatically:
1. Activates the venv
2. Checks if packages are installed
3. Runs the app with the correct Python

### Option 2: Always Activate Venv Manually
```bash
# Every single time before running the app:
venv\Scripts\activate    # Activate venv (you'll see (venv) appear)
python web/app.py        # Now it uses venv's Python
```

## How to Know if Venv is Active

**Before activation:**
```
D:\BTP YOGA CHECKING\yoga-therapy>
```

**After activation:**
```
(venv) D:\BTP YOGA CHECKING\yoga-therapy>
                    ↑
            You should see this!
```

If you DON'T see `(venv)`, the virtual environment is NOT active!

## Common Mistakes

### Mistake 1: Installing without venv active
```bash
# WRONG - installs to global Python
python -m pip install -r requirements.txt

# RIGHT - activates venv first
venv\Scripts\activate
pip install -r requirements.txt
```

### Mistake 2: Running app without venv active
```bash
# WRONG - uses global Python (no packages!)
python web/app.py

# RIGHT - activates venv first
venv\Scripts\activate
python web/app.py
```

### Mistake 3: Opening new terminal window
Every time you open a NEW terminal/command prompt, the venv is NOT activated automatically. You must activate it again:
```bash
cd D:\BTP YOGA CHECKING\yoga-therapy
venv\Scripts\activate    # Always do this in new terminals!
```

## Why This Happens

Virtual environments are **isolated** by design:
- They prevent one project's packages from conflicting with another
- But this means you MUST activate them each time
- Each new terminal starts "fresh" (no venv active)

## The Fix I Created

The `run.bat` script solves this by:
1. **Always activating venv** before running
2. **Checking if packages exist** in the venv
3. **Running with the correct Python** automatically

You never have to think about it - just run `run.bat` and it works!

