"""
QUICK START GUIDE - Yoga Therapy Recommendation System

Follow these steps to get your system up and running.
"""

print("""
╔═══════════════════════════════════════════════════════════════╗
║     YOGA THERAPY RECOMMENDATION SYSTEM - QUICK START          ║
╚═══════════════════════════════════════════════════════════════╝

Step 1: Install Dependencies
----------------------------
Run this command from the main directory:

    pip install -r requirements.txt

This installs Flask, SQLAlchemy, and other necessary packages.


Step 2: Import Sample Data
--------------------------
Populate your database with the sample therapy data:

    python utils/import_data.py

You should see output showing each disease being imported.
This creates the 'yoga_therapy.db' file with all your data.


Step 3: Test the Recommendation Engine
--------------------------------------
Verify everything is working correctly:

    python test_system.py

This runs several tests to ensure practices are being combined
correctly, duplicates are removed, and contraindications work.


Step 4: Start the Web Interface
-------------------------------
Launch the Flask application:

    python web/app.py

Then open your web browser and go to:

    http://127.0.0.1:5000

You'll see the dashboard and can start managing your data!


WHAT TO DO NEXT:
---------------

1. Browse the web interface to see the imported sample data
2. Try adding a new disease or practice to get familiar with data entry
3. Use the recommendation engine to generate practice protocols:

   >>> from core.recommendation_engine import get_summary_for_diseases
   >>> print(get_summary_for_diseases(['Depression', 'Anxiety_Module']))

4. Read the COMPLETE_GUIDE.md file for detailed explanations
5. Review the README.md for comprehensive documentation


TROUBLESHOOTING:
---------------

If you see import errors:
  → Make sure you're in the correct directory
  → Activate your virtual environment if you're using one

If the database seems empty:
  → Run the import script: python utils/import_data.py

If the web interface won't start:
  → Check that port 5000 isn't already in use
  → Look at the console output for error messages


For detailed help, see README.md and COMPLETE_GUIDE.md
""")