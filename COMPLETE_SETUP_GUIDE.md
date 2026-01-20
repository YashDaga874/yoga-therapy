

## 📋 PREREQUISITES - What You Need to Install First

### Step 1: Install Python

1. **Download Python:**
   - Go to: https://www.python.org/downloads/
   - Click the big yellow "Download Python" button (it will download the latest version)

2. **Install Python:**
   - Double-click the downloaded file (e.g., `python-3.12.x.exe`)
   - **IMPORTANT:** Check the box that says **"Add Python to PATH"** at the bottom of the installer
   - Click "Install Now"
   - Wait for installation to complete
   - Click "Close"

3. **Verify Python is installed:**
   - Press `Windows Key + R`
   - Type `cmd` and press Enter
   - Type: `python --version`
   - You should see something like: `Python 3.12.x`
   - If you see an error, Python is not in PATH - restart your computer and try again

### Step 2: Install Git (Optional - only if you need to clone from GitHub)

**If you already have the code folder, skip this step!**

1. **Download Git:**
   - Go to: https://git-scm.com/download/win
   - Click "Download for Windows"
   - The download will start automatically

2. **Install Git:**
   - Double-click the downloaded file (e.g., `Git-2.x.x-64-bit.exe`)
   - Click "Next" through all the prompts (default options are fine)
   - Click "Install"
   - Wait for installation
   - Click "Finish"

---

## 📥 GETTING THE CODE

### Option A: If you have the code folder already
- Skip to "SETUP AND RUN" section below

### Option B: If you need to download from GitHub

1. **Open Command Prompt or PowerShell:**
   - Press `Windows Key + R`
   - Type `cmd` and press Enter

2. **Navigate to where you want the project:**
   ```cmd
   cd C:\Users\YourName\Desktop
   ```
   (Replace `YourName` with your actual Windows username)

3. **Clone the repository:**
   ```cmd
   git clone https://github.com/your-username/yoga-therapy.git
   ```
   (Replace with your actual GitHub repository URL)

4. **Navigate into the project folder:**
   ```cmd
   cd yoga-therapy
   ```

---

## ⚙️ SETUP AND RUN

### First Time Setup (Do this ONCE)

1. **Open Command Prompt or PowerShell:**
   - Press `Windows Key + R`
   - Type `cmd` and press Enter
   - Or right-click in the project folder and select "Open in Terminal"

2. **Navigate to the project folder:**
   ```cmd
   cd C:\path\to\yoga-therapy
   ```
   (Replace with your actual path, or use `cd` to navigate to where you put the folder)

3. **Run the setup script:**
   ```cmd
   setup.bat
   ```
   
   This will:
   - Create a virtual environment
   - Install all required packages
   - Set up the database
   - Take 2-5 minutes depending on your internet speed

4. **Wait for setup to complete:**
   - You'll see messages like "Installing dependencies..."
   - When you see "Setup completed successfully!", you're done!

### Run the Application (Every time you want to use it)

1. **Open Command Prompt or PowerShell:**
   - Press `Windows Key + R`
   - Type `cmd` and press Enter

2. **Navigate to the project folder:**
   ```cmd
   cd C:\path\to\yoga-therapy
   ```

3. **Run the application:**
   ```cmd
   run.bat
   ```

4. **The app will start:**
   - You'll see messages like "Starting Flask application..."
   - The app will automatically open in your browser at: `http://127.0.0.1:5000`
   - If it doesn't open automatically, manually go to that address in your browser

5. **To stop the app:**
   - Press `Ctrl + C` in the terminal window

---

## 🔄 UPDATING FROM GITHUB (Getting Latest Changes)

**If you want to get the latest updates:**

1. **Open Command Prompt:**
   ```cmd
   cd C:\path\to\yoga-therapy
   ```

2. **Discard local database changes (if you get an error):**
   ```cmd
   git checkout -- yoga_therapy.db
   ```

3. **Pull the latest changes:**
   ```cmd
   git pull origin main
   ```

4. **Run the app:**
   ```cmd
   run.bat
   ```

---

## ❓ TROUBLESHOOTING

### Problem: "Python is not recognized as an internal or external command"

**Solution:**
1. Python is not installed OR not in PATH
2. Reinstall Python and make sure to check "Add Python to PATH"
3. Restart your computer after installing
4. Try again

### Problem: "Virtual environment not found"

**Solution:**
Run the setup first:
```cmd
setup.bat
```

### Problem: "Your local changes to the following files would be overwritten by merge: yoga_therapy.db"

**Solution:**
Run these commands:
```cmd
cd yoga-therapy
git checkout -- yoga_therapy.db
git pull origin main
run.bat
```

### Problem: "Flask is not installed"

**Solution:**
The setup didn't complete properly. Run:
```cmd
cd yoga-therapy
venv\Scripts\activate
pip install -r requirements.txt
```

### Problem: App doesn't open in browser

**Solution:**
1. Wait a few seconds after running `run.bat`
2. Manually open your browser
3. Go to: `http://127.0.0.1:5000`

### Problem: Port 5000 is already in use

**Solution:**
1. Close any other applications using port 5000
2. Or edit `web/app.py` and change `app.run(port=5000)` to `app.run(port=5001)`
3. Then access the app at `http://127.0.0.1:5001`

---

## 📝 QUICK REFERENCE

### First Time Ever:
1. Install Python (with "Add to PATH" checked)
2. Install Git (if cloning from GitHub)
3. Get the code (clone or copy folder)
4. Run `setup.bat`
5. Run `run.bat`

### Every Other Time:
1. Run `run.bat`

### To Update:
1. `cd yoga-therapy`
2. `git checkout -- yoga_therapy.db`
3. `git pull origin main`
4. `run.bat`

---

## 🎯 SUMMARY

**For someone with nothing installed:**

1. **Install Python** from python.org (check "Add to PATH")
2. **Get the code** (clone from GitHub or copy the folder)
3. **Open terminal** in the project folder
4. **Run:** `setup.bat` (first time only)
5. **Run:** `run.bat` (every time you want to use the app)

That's it! The app will be running at `http://127.0.0.1:5000` 🎉
