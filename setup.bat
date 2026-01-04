@echo off
REM Yoga Therapy Application Setup Script
REM This script sets up the virtual environment and installs dependencies

echo ========================================
echo Yoga Therapy Application Setup
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.10 or higher and try again.
    pause
    exit /b 1
)

echo Python version:
python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
) else (
    echo Virtual environment already exists.
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo.
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Running database migration...
echo ========================================
echo.
REM Run database migration to ensure all columns exist
python add_kosha_field.py
if errorlevel 1 (
    echo WARNING: Database migration had issues, but continuing...
    echo You may need to run: python add_kosha_field.py
)

echo.
echo ========================================
echo Adding database indexes for performance...
echo ========================================
echo.
REM Add database indexes
python add_database_indexes.py
if errorlevel 1 (
    echo WARNING: Index creation had issues, but continuing...
)

echo.
echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo To run the application, use:
echo   run.bat
echo.
echo Or manually activate the venv and run:
echo   venv\Scripts\activate
echo   python web\app.py
echo.
pause

