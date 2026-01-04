@echo off
REM Yoga Therapy Application Runner
REM This script automatically activates the virtual environment and runs the Flask app

echo ========================================
echo Yoga Therapy Application Launcher
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run the setup first:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import flask" 2>nul
if errorlevel 1 (
    echo ERROR: Flask is not installed!
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies!
        pause
        exit /b 1
    )
)

REM Check if Werkzeug is installed
python -c "import werkzeug" 2>nul
if errorlevel 1 (
    echo WARNING: Werkzeug not found. Installing...
    pip install Werkzeug
)

REM Run database migration to ensure all columns exist
echo.
echo Checking database schema...
python add_kosha_field.py
if errorlevel 1 (
    echo WARNING: Database migration had issues, but continuing...
    echo If you encounter database errors, run: python add_kosha_field.py
)

REM Add database indexes for performance
echo.
echo Optimizing database indexes...
python add_database_indexes.py
if errorlevel 1 (
    echo WARNING: Index creation had issues, but continuing...
)

REM Run the app from the web directory
echo.
echo Starting Flask application...
echo Access the app at: http://127.0.0.1:5000
echo Press Ctrl+C to stop the server
echo.
python web/app.py

