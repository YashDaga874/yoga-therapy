#!/bin/bash
# Yoga Therapy Application Runner
# This script automatically activates the virtual environment and runs the Flask app

echo "========================================"
echo "Yoga Therapy Application Launcher"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -f "venv/bin/activate" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please run the setup first:"
    echo "  python -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo ""
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
python -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "ERROR: Flask is not installed!"
    echo "Installing dependencies..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies!"
        exit 1
    fi
fi

# Check if Werkzeug is installed
python -c "import werkzeug" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "WARNING: Werkzeug not found. Installing..."
    pip install Werkzeug
fi

# Run the app from the web directory
echo ""
echo "Starting Flask application..."
echo "Access the app at: http://127.0.0.1:5000"
echo "Press Ctrl+C to stop the server"
echo ""
python web/app.py

