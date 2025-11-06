# Yoga Therapy Recommendation System

> **📌 NEW USERS: Start with [START_HERE.md](START_HERE.md) for the simplest setup instructions!**

> Quick start for new users is below. A detailed, research-focused guide follows after that.

## Quick Start

> **For detailed step-by-step instructions, see [QUICK_START.md](QUICK_START.md) or [START_HERE.md](START_HERE.md)**

### 🚀 First Time Setup (Do This Once)

1. Navigate to project folder:
   ```bash
   cd yoga-therapy
   ```

2. Run setup script:
   - **Windows:** `setup.bat`
   - **macOS/Linux:** `chmod +x setup.sh && ./setup.sh`

   This installs everything you need automatically, including:
   - Creating virtual environment
   - Installing dependencies
   - Running database migration (ensures database schema is up-to-date)

3. (Optional) Initialize database with sample data:
   ```bash
   python utils/import_data.py
   ```

### ▶️ Running the App (Every Time After Setup)

**Easiest Way - Use the Run Script:**

- **Windows:** `run.bat`
- **macOS/Linux:** `./run.sh`

The app will:
- Automatically check and update database schema
- Start at http://127.0.0.1:5000

**Alternative - Manual Run:**
```bash
# Windows
venv\Scripts\activate
python web\app.py

# macOS/Linux
source venv/bin/activate
python web/app.py
```

> ⚠️ **Important:** Always activate the virtual environment first, or use the `run.bat`/`run.sh` scripts which do this automatically!

---

### 📋 Prerequisites
- Python 3.10 or higher
- Git (for cloning, if applicable)

Run tests/demo (optional):
```bash
python test_system.py
```

Use the API (optional, with server running):
```bash
# JSON recommendations
curl -X POST http://127.0.0.1:5000/api/recommendations \
  -H "Content-Type: application/json" \
  -d '{"diseases":["Depression","GAD"]}'

# Text summary
curl -X POST http://127.0.0.1:5000/api/summary \
  -H "Content-Type: application/json" \
  -d '{"diseases":["Depression","GAD"]}'
```

Troubleshooting:

**Common Issue: "No module named Werkzeug" or "No module named Flask"**
- **Solution**: This happens when the virtual environment is not activated. Always activate the venv before running the app:
  - Windows: `venv\Scripts\activate` (you should see `(venv)` in your prompt)
  - macOS/Linux: `source venv/bin/activate` (you should see `(venv)` in your prompt)
- **Alternative**: Use the `run.bat` (Windows) or `run.sh` (macOS/Linux) script, which automatically activates the venv
- **If still failing**: Reinstall dependencies: `pip install -r requirements.txt`

**SQLAlchemy Compatibility Issues with Latest Python**
- If you're using Python 3.12+ and facing SQLAlchemy issues, ensure you have the latest compatible version by running: `pip install --upgrade SQLAlchemy`
- The requirements.txt uses version ranges that should work with Python 3.10-3.13

**Database Schema Issues**:
- If you see errors about missing columns (like `kosha`, `module_id`, `paper_link`), the migration script should run automatically when you use `run.bat`/`run.sh`.
- If migration doesn't run automatically, manually run: `python add_kosha_field.py` (make sure venv is activated).
- The migration script will automatically add any missing columns to your database.

**Other Issues**:
- Activate the venv and run from the repo root if you see import errors.
- If port 5000 is busy, Flask prints the actual port—use that.
- If the database is missing/empty, re-run `python utils/import_data.py` (make sure venv is activated).
- If dependencies fail to install, try: `pip install --upgrade pip` then `pip install -r requirements.txt`.

---

## Understanding What This System Does

Welcome to your Yoga Therapy Recommendation System. This is a research-grade database and recommendation engine designed specifically for managing yoga therapy protocols based on the Pancha Kosha (Five Sheaths) framework. Let me explain what this system accomplishes and why it's architected the way it is.

At its core, this system solves a sophisticated clinical problem. When a patient presents with multiple co-morbid conditions such as Depression and Generalized Anxiety Disorder, clinicians need to combine therapeutic practices from different treatment protocols. However, simply merging two treatment plans can create problems. Some practices might be duplicated across protocols, and certain practices might be contraindicated when conditions are combined. Your system handles this complexity automatically.

The system intelligently combines practices from multiple diseases, removes duplicate practices so patients aren't asked to repeat the same exercise unnecessarily, and filters out any practices that are contraindicated for the specific combination of conditions. All of this happens while maintaining proper academic citations so your research remains traceable and scientifically rigorous.

## How the System is Organized

The codebase is structured into distinct folders, each serving a specific purpose in the overall architecture. This separation makes the system easier to understand, maintain, and extend as your research grows.

The **database folder** contains the data models that define the structure of your research database. Think of these models as blueprints that describe what information you're storing and how different pieces of information relate to each other. For instance, the Disease model defines what information you store about each condition, while the Practice model defines the structure for storing yoga practices. The relationships between these models mirror the real-world relationships in your research, such as how one practice can be used for multiple diseases, or how multiple practices might reference the same research citation.

The **core folder** houses the recommendation engine, which is the intelligent heart of your system. This engine takes a list of diseases as input and produces a comprehensive treatment protocol as output. The magic happens through a series of carefully designed steps. First, it retrieves all practices associated with the requested diseases from the database. Then it organizes these practices by practice segment and methodically removes duplicates by comparing practice names while ignoring differences in capitalization or spacing. After deduplication, it applies safety filters by removing any practices that are contraindicated for the combination of diseases. Finally, it formats everything into a structured output that includes proper citations and organization by the nine practice segments.

The **utils folder** contains helper scripts that make your life easier. The most important is the data import utility, which transforms your JSON research data into a properly structured database. This script understands the nested structure of your therapy modules and correctly links practices to diseases, manages citations, and handles all the complex relationships automatically. You won't need to manually enter database records one by one.

The **web folder** contains the Flask application that provides a graphical interface for managing your data. This is crucial because it means researchers who don't know how to code can still contribute to the database. They can add new diseases, enter practices, set up contraindications, and manage citations all through a web browser with intuitive forms.

## Getting Started: Installation and Setup

Before you can start using the system, you need to set up your Python environment and install the necessary dependencies. The system requires Python 3.7 or higher, which you likely already have installed if you're working on a research project.

First, navigate to the system directory in your terminal. You'll want to create what's called a virtual environment, which is an isolated Python environment for this project. This prevents conflicts with other Python projects you might have. You can create a virtual environment by running `python -m venv venv` and then activate it. On Windows, you activate it with `venv\Scripts\activate`, while on Mac or Linux you use `source venv/bin/activate`. When the virtual environment is active, you'll typically see `(venv)` appear at the beginning of your terminal prompt.

Next, install the required Python packages by running `pip install -r requirements.txt`. This command reads the requirements file and installs Flask for the web interface, SQLAlchemy for database operations, and other necessary dependencies. The installation should complete within a minute or two depending on your internet connection.

## Populating Your Database with Sample Data

Now that dependencies are installed, you need to populate your database with the sample therapy data. I've created an import script that automatically processes your JSON data and creates a properly structured database. Run this script by executing `python utils/import_data.py` from the main directory.

Watch the output as the script runs. You'll see it processing each disease and its associated practices. The script is intelligent about handling the nested structure of your therapy modules, correctly identifying which practices belong to which practice segment, and properly linking everything together through the database relationships. When the script completes successfully, you'll see a success message and you'll have a new file called `yoga_therapy.db` in your directory. This file contains your entire research database in a portable format.

If you encounter any errors during import, they typically stem from issues in the JSON structure. The script will tell you exactly where the problem occurred so you can fix it. Common issues include missing required fields or inconsistent data types, but the sample data I've provided should import cleanly.

## Using the Web Interface

The web interface is designed to be intuitive enough for researchers without coding experience to use comfortably. Start the Flask application by running `python web/app.py`. The server will start and you'll see output telling you it's running on `http://127.0.0.1:5000`. Open this address in your web browser to access the interface.

The home page gives you an overview dashboard showing statistics about your database. You'll see how many diseases, practices, citations, and contraindications are currently stored. This gives you a quick sense of the scope of your research data at a glance.

The diseases page is where you'll spend time when adding new conditions to your research. When you add a disease, you're not just entering a name. You're establishing a complete therapy module with attribution to the researchers who developed it. This maintains academic integrity throughout your project. After adding a disease, you can view its detail page to see all associated practices organized by practice segment.

The practices page is the workhorse of your data entry process. Here you can add individual yoga practices with all their details. The form is comprehensive but straightforward. You enter the Sanskrit and English names, specify which practice segment and sub-category the practice belongs to, add technical details like rounds and duration, and crucially, link the practice to relevant diseases and cite your sources. The beauty of this approach is that you enter each practice once, but it can be associated with multiple diseases. If both Depression and Anxiety modules use "Shavasana," you only need to enter the practice details once and then link it to both diseases.

The contraindications page is essential for patient safety. When your research indicates that a particular practice should be avoided for a specific disease, you add that contraindication here. The system will then automatically exclude that practice when generating recommendations for that disease or any combination including that disease. This automated safety checking is one of the key advantages of using a database system over manual protocol combination.

The citations page helps you manage your research references centrally. When multiple practices come from the same research paper, you create one citation entry and link multiple practices to it. This avoids duplication and makes it easy to update citation details in one place if needed.

## Testing the Recommendation Engine

Before integrating with your RAG chatbot, you should thoroughly test the recommendation engine to ensure it's working correctly. I've created a comprehensive test script that demonstrates all the key functionality. Run this test suite by executing `python test_system.py`.

The test script runs several important checks. First, it tests getting recommendations for a single disease to verify basic functionality. Then it tests combining multiple diseases to demonstrate the deduplication and contraindication logic. It shows you both the JSON format (which your API will use) and the text summary format (which the RAG chatbot will present to doctors). By examining the test output, you can verify that practices are being combined correctly, duplicates are being removed, and the output includes proper citations.

Pay close attention to the test results. If all tests pass, your system is working correctly and ready for integration with your RAG chatbot. If any tests fail, the script will show you detailed error messages that help identify the problem. The most common issue is running the tests before importing the sample data, so make sure you've run the import script first.

## How RAG Integration Will Work

Understanding how your recommendation system will integrate with the RAG chatbot is important for planning your overall workflow. The RAG system and your recommendation engine are complementary components that work together to provide a complete solution.

The RAG chatbot serves as the conversational interface where doctors interact naturally. When a doctor types something like "I have a patient with depression and anxiety, what practices should they do?", the RAG system processes this natural language to extract the key information, which in this case is the list of diseases: Depression and Anxiety. The RAG system then needs to call your recommendation engine to get the actual therapy protocols.

I've included API endpoints in the Flask application specifically for this integration. The `/api/recommendations` endpoint accepts a POST request with JSON containing a disease list and returns the complete structured data. The `/api/summary` endpoint returns a human-readable text summary that's ready to be presented in the chat interface. These endpoints form the bridge between the conversational RAG interface and your evidence-based recommendation engine.

When you're ready to connect the systems, the RAG team will need to configure their system to make HTTP requests to your Flask server. You might run the Flask application on a dedicated server or port that remains consistently accessible. The RAG system should be designed to handle cases where disease names don't match exactly, perhaps by trying variations or asking the doctor for clarification. Error handling is crucial because if the RAG extracts a disease name that doesn't exist in your database, you want the system to fail gracefully and help the doctor identify what went wrong.

Consider testing the integration incrementally. Start by having the RAG system call your API with hardcoded disease names to verify the communication works. Then gradually add the natural language processing to extract diseases from doctor input. Finally, add sophisticated features like suggesting similar disease names if an exact match isn't found in your database.

## Preparing for Future CVR Enhancement

You mentioned wanting to add CVR (Capacity-Variability-Responsiveness) logic in the future without requiring major code restructuring. The system's architecture specifically supports this enhancement path. Let me explain how you'll add CVR when you're ready.

The CVR enhancement will essentially add an additional dimension to practice selection. Right now, the system selects all practices for a disease within each practice segment. With CVR, you'll assess the patient's capacity, variability, and responsiveness levels, and then filter practices based on whether they're appropriate for those levels. For instance, a patient with low capacity might receive gentler practices, while a high-capacity patient might receive more intensive practices within the same practice segment.

To implement this, you'll first extend the Practice model by adding CVR-related fields such as `capacity_level`, `variability_category`, and `responsiveness_score`. These fields will initially be null for existing practices, allowing your current data to remain valid while you gradually add CVR ratings to practices.

In the recommendation engine, you'll add a new filtering method that applies after contraindications are handled. This method will receive the patient's assessed CVR scores and filter the practice list to include only those practices appropriate for those scores. The method slots naturally into the existing recommendation pipeline without requiring you to rewrite the foundational logic.

The web interface will need a few additions to support CVR data entry. You'll add fields to the practice entry form for specifying CVR levels, and you might add a new page for managing CVR assessment criteria. But the core structure remains the same because I've designed the database schema to be extensible through adding columns rather than restructuring tables.

This approach means you can continue using the system exactly as it is now while planning for CVR integration. When you're ready to enhance it, you'll be adding features rather than rebuilding, which is much more efficient for an ongoing research project.

## Data Management Best Practices

As you build your database over the course of your research project, following certain best practices will ensure your data remains high quality and usable. Let me share some principles that will serve you well.

Consistency in terminology is crucial for the duplicate detection to work properly. When entering practice names, establish conventions and stick to them. For example, decide whether you'll use "Shavasana" or "Savasana" and use that spelling consistently. The system is case-insensitive, so "SHAVASANA" and "shavasana" will be recognized as duplicates, but "Shavasana" and "Savasana" will be treated as different practices because the spelling differs.

Documentation thoroughness makes a huge difference for research quality. Use the description fields liberally to record context about why practices were chosen, what research supports them, and any special considerations. Years from now, when someone else reviews your work or when you're writing up your research for publication, this documentation will be invaluable.

Citation completeness maintains academic integrity. Don't just enter abbreviated citations like "Smith 2020" in the citation text field. Use the full reference field to store complete bibliographic information including title, journal, volume, pages, and DOI if available. This makes it easy for others to locate and verify your sources.

Regular backups protect your research investment. The entire database is stored in a single file, `yoga_therapy.db`, which makes backing up simple. Regularly copy this file to a backup location such as cloud storage or an external drive. Consider using version control systems like Git to track changes over time, which also serves as a backup mechanism while providing the ability to review the history of your database evolution.

Validation and testing should happen continuously as you add data. Don't wait until you have hundreds of practices entered to test the recommendation engine. Instead, after adding each new disease or set of practices, generate some test recommendations to verify everything is working as expected. This catches errors early when they're easy to fix rather than after they've compounded.

## Troubleshooting Common Issues

Even with well-designed systems, you'll occasionally encounter issues. Let me walk you through the most common problems and how to resolve them.

If practices aren't appearing in recommendations when you expect them to, the first thing to check is whether the practice is actually linked to the disease in question. Go to the disease detail page in the web interface and look at the list of practices associated with that disease. If the practice you're looking for isn't listed, you need to either edit the practice to add that disease association or add the practice fresh with the correct disease links.

When duplicate practices aren't being removed correctly in combined recommendations, this almost always indicates slight spelling differences between the practice entries. Even a single character difference will prevent the duplicate detection from matching them. Go to the practices page and use the search function to find variations of the practice name. Edit them to use identical spelling, and the deduplication will work correctly.

If contraindications aren't being applied, verify that the contraindication entry exactly matches the practice name and practice segment. The system uses string matching to identify contraindicated practices, so even small differences like extra spaces or different capitalization in the practice segment name will prevent matching. The practice name matching is case-insensitive, but the practice segment name must match exactly.

Database errors typically occur during the import process if the JSON structure doesn't match what the script expects. Read the error message carefully because it will tell you which disease and which section of the data caused the problem. Often it's a matter of missing required fields or incorrectly nested structures. Compare the problematic section to the working examples in the sample data to identify the difference.

Web interface issues often stem from the Flask server not running or running on a different port than expected. Make sure you see the "Running on http://127.0.0.1:5000" message before trying to access the web interface. If the port is already in use, Flask will assign a different port, so check the console output to see which address to use.

