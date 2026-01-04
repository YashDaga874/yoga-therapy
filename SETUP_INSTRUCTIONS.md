# 📋 Complete Setup Instructions for New Users

**For anyone who has just cloned this repository from GitHub**

---

## Prerequisites Check

Before you begin, make sure you have:

1. **Python 3.10 or higher** installed
   - Check by running: `python --version` (Windows) or `python3 --version` (macOS/Linux)
   - If not installed, download from: https://www.python.org/downloads/

2. **Git** installed (you already have this if you cloned the repo)
   - Check by running: `git --version`

3. **Git LFS** (optional, but recommended if database file is large)
   - Check by running: `git lfs version`
   - If not installed, see [Git LFS Setup](#git-lfs-setup-optional) section below

---

## Step-by-Step Setup Instructions

### Step 1: Open Terminal/Command Prompt

- **Windows:** Press `Win + R`, type `cmd` or `powershell`, press Enter
- **macOS:** Press `Cmd + Space`, type `Terminal`, press Enter
- **Linux:** Press `Ctrl + Alt + T` or open Terminal from applications

---

### Step 2: Navigate to the Project Directory

```bash
cd "D:\BTP YOGA CHECKING\yoga-therapy"
```

**Note:** Replace the path above with the actual path where you cloned the repository.

**Tip:** You can also:
- Navigate to the folder in File Explorer (Windows) or Finder (macOS)
- Right-click in the folder and select "Open in Terminal" or "Open PowerShell window here"

---

### Step 3: Verify You're in the Correct Directory

```bash
# Windows
dir

# macOS/Linux
ls
```

You should see files like:
- `setup.bat` or `setup.sh`
- `requirements.txt`
- `README.md`
- `web/` folder
- `core/` folder
- etc.

---

### Step 4: (Optional) Set Up Git LFS for Database File

**Skip this step if:**
- The database file (`yoga_therapy.db`) is already present and not a pointer file
- You don't see any Git LFS-related errors

**Do this step if:**
- The `yoga_therapy.db` file appears very small (less than 1KB) or shows as a text file
- You see Git LFS pointer files

#### Install Git LFS:

**Windows:**
```bash
# Option 1: Download installer from https://git-lfs.github.com/
# Option 2: Using winget (if available)
winget install Git.GitLFS
```

**macOS:**
```bash
brew install git-lfs
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install git-lfs
```

**Linux (Fedora):**
```bash
sudo dnf install git-lfs
```

#### Initialize Git LFS and Pull Database:

```bash
# Initialize Git LFS
git lfs install

# Pull the actual database file
git lfs pull
```

**Verify the database file:**
```bash
# Windows
dir yoga_therapy.db

# macOS/Linux
ls -lh yoga_therapy.db
```

The file should be around 100KB or larger (not just a few bytes).

---

### Step 5: Run the Setup Script

This is the **main setup step** that installs everything you need.

#### For Windows Users:

```bash
setup.bat
```

**What this does:**
- Creates a virtual environment (`venv` folder)
- Installs all Python dependencies (Flask, SQLAlchemy, etc.)
- Runs database migration scripts
- Sets up database indexes

**Expected output:**
- You'll see messages about creating virtual environment
- Installing packages from requirements.txt
- Running database migrations
- Setup completion message

**Time:** Takes 1-3 minutes depending on your internet speed

#### For macOS/Linux Users:

```bash
# First, make the script executable (only needed once)
chmod +x setup.sh

# Then run it
./setup.sh
```

**What this does:**
- Same as Windows version (creates venv, installs dependencies, runs migrations)

**Expected output:**
- Similar messages as Windows version

**Time:** Takes 1-3 minutes depending on your internet speed

---

### Step 6: Verify Setup Completed Successfully

After the setup script finishes, verify everything is ready:

```bash
# Check if virtual environment exists
# Windows
dir venv

# macOS/Linux
ls venv
```

You should see a `venv` folder with subdirectories.

**Check if dependencies are installed:**

```bash
# Windows
venv\Scripts\activate
python -c "import flask; print('Flask installed successfully!')"

# macOS/Linux
source venv/bin/activate
python -c "import flask; print('Flask installed successfully!')"
```

If you see "Flask installed successfully!", you're good to go!

**Deactivate the virtual environment:**
```bash
# Just type this (works on all platforms)
deactivate
```

---

## Running the Application

Now that setup is complete, you can run the application!

### Method 1: Using the Run Script (EASIEST - Recommended)

#### For Windows:

```bash
run.bat
```

#### For macOS/Linux:

```bash
./run.sh
```

**What happens:**
- Automatically activates the virtual environment
- Checks database schema
- Starts the Flask web server
- Shows you the URL: `http://127.0.0.1:5000`

**To access the app:**
1. Open your web browser
2. Go to: `http://127.0.0.1:5000`
3. You should see the Yoga Therapy application homepage!

**To stop the server:**
- Press `Ctrl + C` in the terminal

---

### Method 2: Manual Run (Alternative)

If you prefer to run manually:

#### For Windows:

```bash
# Step 1: Activate virtual environment
venv\Scripts\activate

# You should see (venv) in your prompt now

# Step 2: Run the application
python web\app.py
```

#### For macOS/Linux:

```bash
# Step 1: Activate virtual environment
source venv/bin/activate

# You should see (venv) in your prompt now

# Step 2: Run the application
python web/app.py
```

**To stop the server:**
- Press `Ctrl + C` in the terminal

**To deactivate virtual environment:**
```bash
deactivate
```

---

## Quick Reference

| Action | Windows Command | macOS/Linux Command |
|--------|----------------|---------------------|
| **First-time setup** | `setup.bat` | `chmod +x setup.sh && ./setup.sh` |
| **Run the app** | `run.bat` | `./run.sh` |
| **Stop the app** | Press `Ctrl+C` | Press `Ctrl+C` |
| **Manual activation** | `venv\Scripts\activate` | `source venv/bin/activate` |
| **Manual run** | `python web\app.py` | `python web/app.py` |

---

## Troubleshooting

### Problem: "Python is not recognized" or "python: command not found"

**Solution:**
1. Python is not installed or not in PATH
2. Install Python 3.10+ from https://www.python.org/downloads/
3. During installation, check "Add Python to PATH"
4. Restart your terminal after installation

---

### Problem: "No module named Flask" or "No module named Werkzeug"

**Solution:**
1. You forgot to activate the virtual environment
2. **Easiest fix:** Use `run.bat` (Windows) or `./run.sh` (macOS/Linux) - it handles this automatically
3. **Manual fix:** Activate venv first, then run the app:
   - Windows: `venv\Scripts\activate` then `python web\app.py`
   - macOS/Linux: `source venv/bin/activate` then `python web/app.py`

---

### Problem: "Virtual environment not found"

**Solution:**
1. You haven't run the setup script yet
2. Run `setup.bat` (Windows) or `./setup.sh` (macOS/Linux) first
3. Wait for it to complete before running the app

---

### Problem: Database file is very small or shows as text

**Solution:**
1. Git LFS is not installed or not initialized
2. Install Git LFS (see Step 4 above)
3. Run: `git lfs install` then `git lfs pull`
4. Verify the database file size increased

---

### Problem: Port 5000 is already in use

**Solution:**
1. Another application is using port 5000
2. Flask will automatically use a different port (check the terminal output)
3. Use the URL shown in the terminal (e.g., `http://127.0.0.1:5001`)
4. Or stop the other application using port 5000

---

### Problem: Setup script fails during dependency installation

**Solution:**
1. Check your internet connection
2. Try upgrading pip first:
   ```bash
   python -m pip install --upgrade pip
   ```
3. Then manually install dependencies:
   ```bash
   # Activate venv first
   # Windows: venv\Scripts\activate
   # macOS/Linux: source venv/bin/activate
   
   pip install -r requirements.txt
   ```

---

### Problem: Database migration errors

**Solution:**
1. The migration scripts should run automatically
2. If they fail, manually run:
   ```bash
   # Activate venv first
   python add_kosha_field.py
   python add_database_indexes.py
   ```

---

## What's Next?

Once the application is running:

1. **Explore the Web Interface:**
   - Open `http://127.0.0.1:5000` in your browser
   - Browse diseases, practices, and citations
   - Try generating recommendations

2. **Read the Documentation:**
   - `README.md` - Overview and features
   - `METHODOLOGY.md` - Research methodology
   - `DATABASE_CONFIG.md` - Database configuration details

3. **Test the API:**
   - The app includes REST API endpoints
   - See README.md for API usage examples

---

## Summary Checklist

- [ ] Python 3.10+ installed
- [ ] Cloned repository to local machine
- [ ] Navigated to project directory
- [ ] (Optional) Installed Git LFS and pulled database file
- [ ] Ran `setup.bat` (Windows) or `./setup.sh` (macOS/Linux)
- [ ] Verified setup completed successfully
- [ ] Ran `run.bat` (Windows) or `./run.sh` (macOS/Linux)
- [ ] Opened `http://127.0.0.1:5000` in browser
- [ ] Application is working! ✅

---

## Need More Help?

- Check `TROUBLESHOOTING.md` for more detailed solutions
- Review `START_HERE.md` for a simpler quick start guide
- See `QUICK_START.md` for condensed instructions

---

**Congratulations! You're all set up and ready to use the Yoga Therapy Recommendation System! 🎉**

