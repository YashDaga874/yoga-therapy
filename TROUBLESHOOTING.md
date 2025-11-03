# Troubleshooting Guide

## Common Issues and Solutions

### Issue 1: "No module named Werkzeug" or "No module named Flask"

**Problem**: When running `python web/app.py`, you get an error saying Werkzeug or Flask is not found, even though you installed it during setup.

**Root Cause**: The virtual environment is not activated. Python is looking for packages in the global Python installation instead of the virtual environment where the packages are installed.

**Solution**:
1. **Always activate the virtual environment before running the app:**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```
   
   You should see `(venv)` appear in your terminal prompt.

2. **Then run the app:**
   ```bash
   cd web
   python app.py
   ```

3. **Alternative - Use the run script (Recommended):**
   ```bash
   # Windows
   run.bat
   
   # macOS/Linux
   ./run.sh
   ```
   This script automatically activates the virtual environment and runs the app.

**Prevention**: Always check for `(venv)` in your terminal prompt before running Python commands.

---

### Issue 2: SQLAlchemy Compatibility Issues with Latest Python

**Problem**: Errors related to SQLAlchemy when using Python 3.12 or 3.13.

**Solution**:
1. Make sure you're using the virtual environment:
   ```bash
   # Activate venv first
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # macOS/Linux
   ```

2. Upgrade SQLAlchemy to the latest compatible version:
   ```bash
   pip install --upgrade SQLAlchemy
   ```

3. If issues persist, reinstall all dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt --force-reinstall
   ```

---

### Issue 3: Dependencies Install Fine But App Still Fails

**Problem**: Setup works, but when you rerun the app later, modules are missing.

**Root Cause**: The virtual environment wasn't activated, so Python is using a different environment or the global Python installation.

**Solution**:
1. Always activate the virtual environment before running any Python commands
2. Verify the venv is active by checking for `(venv)` in your prompt
3. Use the automated run scripts (`run.bat` or `run.sh`) which handle activation automatically

---

### Issue 4: "Cannot activate virtual environment"

**Problem**: Getting errors when trying to activate the venv.

**Solutions**:

**Windows:**
- Try: `venv\Scripts\Activate.ps1` (for PowerShell)
- Or: `venv\Scripts\activate.bat` (for Command Prompt)
- If PowerShell execution policy is blocking, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

**macOS/Linux:**
- Make sure you're using: `source venv/bin/activate` (not just `venv/bin/activate`)
- If permissions are denied: `chmod +x venv/bin/activate`

---

## Best Practices

1. **Always activate venv first**: Check for `(venv)` in your prompt
2. **Use the run scripts**: They handle activation automatically
3. **Reinstall if needed**: If packages seem missing, activate venv and run `pip install -r requirements.txt`
4. **Check Python version**: Ensure you're using Python 3.10 or higher

---

## Quick Reference

### Setup (First Time)
```bash
# Windows
setup.bat

# macOS/Linux
chmod +x setup.sh
./setup.sh
```

### Running the App
```bash
# Windows (automated)
run.bat

# macOS/Linux (automated)
./run.sh

# Manual (always activate venv first!)
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
cd web
python app.py
```

### Verifying Installation
```bash
# Activate venv first!
python -c "import flask; import werkzeug; import sqlalchemy; print('All dependencies installed!')"
```

