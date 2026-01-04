#!/bin/bash
# Yoga Therapy Application Setup Script
# This script sets up the virtual environment and installs dependencies

echo "========================================"
echo "Yoga Therapy Application Setup"
echo "========================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "ERROR: Python is not installed or not in PATH!"
    echo "Please install Python 3.10 or higher and try again."
    exit 1
fi

# Use python3 if available, otherwise python
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
else
    PYTHON_CMD=python
fi

echo "Python version:"
$PYTHON_CMD --version
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment!"
        exit 1
    fi
    echo "Virtual environment created successfully."
else
    echo "Virtual environment already exists."
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies!"
    exit 1
fi

echo ""
echo "========================================"
echo "Running database migration..."
echo "========================================"
echo ""
# Run database migration to ensure all columns exist
python add_kosha_field.py
if [ $? -ne 0 ]; then
    echo "WARNING: Database migration had issues, but continuing..."
    echo "You may need to run: python add_kosha_field.py"
fi

echo ""
echo "========================================"
echo "Adding database indexes for performance..."
echo "========================================"
echo ""
# Add database indexes
python add_database_indexes.py
if [ $? -ne 0 ]; then
    echo "WARNING: Index creation had issues, but continuing..."
fi

echo ""
echo "========================================"
echo "Setup completed successfully!"
echo "========================================"
echo ""
echo "To run the application, use:"
echo "  ./run.sh"
echo ""
echo "Or manually activate the venv and run:"
echo "  source venv/bin/activate"
echo "  python web/app.py"
echo ""

