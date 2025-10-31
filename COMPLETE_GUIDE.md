# Yoga Therapy Recommendation System - Complete Guide

## Understanding the System Architecture

Let me walk you through how this entire system works, starting from the foundational concepts and building up to how you'll use it in practice.

### The Core Philosophy: Practice Segments Framework

Your system organizes yoga practices across nine practice segments that represent different aspects of a comprehensive yoga therapy program. Each disease or condition you're treating requires practices from various segments to create a well-rounded therapeutic approach. Think of it like treating a patient holistically rather than just addressing symptoms in isolation.

When a patient presents with multiple conditions like Depression and Generalized Anxiety Disorder (GAD), traditional approaches might treat them separately. However, your system takes a more sophisticated approach by combining the therapeutic practices from both conditions while being smart about removing redundancies and contraindications. This is where the real power of your system lies.

### The Three-Layer Architecture

Your system is designed with three distinct layers, each serving a specific purpose. Let me explain each one and how they work together.

**Layer 1: The Database Foundation**

At the bottom, we have a relational database that stores all your research data. I chose a relational database structure (using SQLAlchemy ORM with SQLite) for several important reasons. First, it allows researchers who don't know how to code to understand the data structure intuitively because it mirrors how research data is naturally organized in tables. Second, it makes it incredibly easy to maintain data integrity, meaning you won't accidentally create inconsistent or conflicting data entries. Third, and most importantly for your future needs, it scales elegantly when you add more complex features like the CVR (Capacity-Variability-Responsiveness) logic you mentioned wanting to implement later.

The database has five main tables that work together:

The **Diseases** table stores each condition you're treating. This is straightforward, but the power comes from how it connects to other tables. Each disease can have many practices associated with it, and this relationship is managed through what's called a many-to-many association table. This means one practice can be used for multiple diseases, and one disease uses multiple practices.

The **Practices** table is where the real yoga therapy knowledge lives. Each practice has all its details like the Sanskrit name, English translation, which practice segment it belongs to, how many rounds to perform, duration, and so on. Notice that we store the practice_segment and sub_category as simple text fields right now. This design decision is intentional because when you add CVR logic later, you'll simply add additional filtering logic based on these categories rather than restructuring the entire database.

The **Citations** table maintains academic rigor. Every practice can reference a research paper or book, which is crucial for your BTP project since you need to cite sources. Multiple practices can share the same citation, which prevents data duplication and makes it easy to update a citation reference in one place.

The **Contraindications** table is safety-critical. When combining practices from multiple diseases, certain practices might be contraindicated for specific conditions. The system automatically filters these out, ensuring patient safety.

The **Modules** table stores metadata about each disease's therapy module, particularly the "Developed by" information that credits the researchers who created that particular treatment protocol.

**Layer 2: The Core Logic Engine**

The middle layer contains the YogaTherapyRecommendationEngine class, which is the brain of your system. This is where the intelligent combination of practices happens. Let me walk you through exactly what happens when someone requests practices for multiple diseases.

Imagine a doctor inputs that their patient has both Depression and GAD. The engine first retrieves all practices associated with each disease from the database. At this point, you might have duplicate practices because both conditions might recommend "Neck sideward movement" or "Surya namaskar."

The engine then organizes these practices by practice segment and removes duplicates. The duplicate detection is quite sophisticated - it doesn't just match exact strings, but rather it normalizes the practice names by converting them to lowercase and stripping whitespace, then compares them along with their practice_segment and sub_category. This means even if someone types "Neck Sideward Movement" in one place and "neck sideward movement" in another, the system recognizes them as the same practice.

After removing duplicates, the engine applies contraindications. This is crucial for patient safety. If Depression has "Bhastrika" as a practice but GAD has it listed as a contraindication, the system will remove it from the final recommendations. The rule is conservative: if ANY disease in the combination has a practice as a contraindication, that practice is excluded from the final output.

Finally, the engine formats everything nicely, organizing practices by practice segment in a specific order (Preparatory Practice, Breathing Practice, Suryanamaskara, Yogasana, Pranayama, Meditation, Additional Practices, Kriya, Yogic Counselling) and including all the citation information so you maintain academic standards.

**Layer 3: The Interface Layer**

The top layer is the Flask web application that provides a user-friendly interface for researchers to manage data without touching code. This addresses your specific requirement that "anyone with no code knowledge can input the requirements."

The web interface has several pages. The home page gives you an overview dashboard showing how many diseases, practices, citations, and contraindications are in your database. The diseases page lists all conditions and lets you view details about each one, seeing which practices are associated with it and what contraindications exist. The practices page has filtering and search capabilities so you can find specific practices by practice segment or search by name. The contraindications and citations pages help you manage these critical elements of your research data.

Each page has forms designed to be intuitive. For example, when adding a new practice, you see fields for all the relevant information with helpful placeholder text. The variations field accepts one variation per line, making it easy to input multiple variations without worrying about JSON syntax. Behind the scenes, the system converts this into proper JSON format for storage.

### Future-Proofing for CVR Integration

You mentioned wanting to add CVR logic in the future without major code restructuring. I designed the system specifically with this in mind. When you're ready to add CVR, here's how it will work seamlessly with the current structure.

The CVR logic will essentially be an additional filtering step within each practice segment's practice selection. Right now, the engine fetches all practices for a disease within each practice segment. When you add CVR, you'll extend the Practice model to include CVR-related fields like capacity_level, variability_score, and responsiveness_category. Then, in the recommendation engine, you'll add a method like `_apply_cvr_filtering()` that takes the patient's assessed CVR scores and filters practices accordingly.

The beauty of this design is that all your existing data remains valid. You simply add new columns to the Practice table for CVR attributes, and older practices that don't have CVR scores yet will still work perfectly. The filtering logic becomes: "Get practices for this practice segment → Remove duplicates → Apply contraindications → Apply CVR filtering." That fourth step just slots in naturally without requiring you to rebuild the entire system.

### Integration with RAG Chatbot

You mentioned this system will work alongside a RAG (Retrieval-Augmented Generation) chatbot where doctors interact. Let me explain how these two systems will communicate and why the API endpoints are designed the way they are.

The RAG chatbot serves as the conversational interface where doctors input natural language like "My patient has Depression and GAD, what practices should they do?" The chatbot's job is to extract the disease names from that natural language, then call your recommendation system's API to get the structured data.

I've included two API endpoints in the Flask application specifically for this integration. The first endpoint, `/api/recommendations`, accepts a POST request with JSON containing a list of diseases and returns the full structured data with all practices organized by practice segment. This is useful when the chatbot needs to process the data further or present it in a custom format.

The second endpoint, `/api/summary`, returns a human-readable text summary that's perfect for the chatbot to present directly to the doctor. This summary includes all the practices organized by practice segment with proper formatting and citations, ready to be shown in the chat interface.

Here's a concrete example of how the integration works. The doctor types into the chatbot: "I need practices for a patient with Depression and Generalized Anxiety Disorder." The RAG system processes this, extracts ["Depression", "GAD"], and makes a POST request to your recommendation API with that list. Your system returns the combined practices with duplicates removed and contraindications applied. The RAG system then presents this information back to the doctor in a conversational way, perhaps adding context like "Based on the research by Dr. Naveen GH et al., 2013, here are the recommended practices..."

### Setting Up and Running Your System

Let me guide you through getting everything running. I've organized the code into a clear directory structure that separates concerns. You have a `database` folder containing the data models, a `core` folder with the recommendation engine logic, a `utils` folder with helper scripts like the data importer, and a `web` folder containing the Flask application.

To get started, you'll first need to install the required Python packages. The main dependencies are SQLAlchemy for database operations and Flask for the web interface. You can install these using pip.

Once dependencies are installed, run the data import script to populate your database with the sample data you provided. This creates the yoga_therapy.db file and fills it with all the practices from your JSON. The script is intelligent enough to handle the nested structure of your data and properly link everything together.

After the database is populated, you can start the Flask web server. When it's running, open your web browser and navigate to localhost:5000 to see the management interface. From here, you can browse the imported data, add new diseases and practices, set up contraindications, and manage citations.

To test the recommendation engine independently of the web interface, you can use the Python interactive shell. Import the recommendation engine and call the `get_summary_for_diseases()` function with a list of diseases. This will show you exactly what a patient with those combined conditions should practice, with duplicates removed and contraindications applied.

### Data Entry Workflow for Research Teams

Since your team members aren't coders, I've designed an intuitive workflow for entering research data. When you discover a new therapy protocol from research literature, here's the step-by-step process.

First, add the disease or condition if it's not already in the system. Use the "Add Disease" form where you enter the condition name and the citation for the module developer. This establishes the foundation for that condition in your database.

Next, add the citation for any research papers or books you're using. This is separate from the disease creation because multiple practices might reference the same source. By creating citations separately, you avoid duplicating reference information.

Then, for each practice in the therapy protocol, use the "Add Practice" form. This is where you'll spend most of your time. Enter all the details like Sanskrit and English names, which practice segment it belongs to, the sub-category, and all the technical details like rounds, duration, and so on. Select which diseases this practice is used for and link it to the appropriate citation.

If your research indicates that certain practices are contraindicated for the disease, add those using the contraindications form. This is crucial for patient safety when combining therapies.

The web interface validates your input as you go, ensuring you don't miss required fields and helping maintain data quality without requiring technical knowledge.

### Understanding the Output Format

When you request recommendations, the system provides output in two formats depending on your needs. The JSON format gives you structured data that's easy for programs to process, perfect for the RAG integration. The text summary format gives you human-readable output suitable for direct presentation.

The JSON output has a clear structure. At the top level, you see which diseases were combined. Then you have a modules section showing the attribution for each therapy module. The main section is practices_by_segment, which organizes everything by the nine practice segments in the proper order. Within each segment, practices are further organized by sub-category, and each practice includes all its details plus the citation information.

The text summary format is narrative rather than structured data. It reads like a report that a clinician could follow directly, with clear headings for each practice segment and human-readable descriptions of each practice including citations.

### Best Practices for Research Data Management

As you build up your database with more diseases and practices, keep a few important principles in mind. Consistency in naming is crucial - always use the same spelling and capitalization for practice names. If one researcher enters "Shavasana" and another enters "Savasana," the duplicate detection might fail.

Document everything thoroughly in the description fields. Future researchers reviewing your work will benefit from understanding why certain practices were chosen or why specific contraindications were established. This is especially important for academic work where methodology transparency is critical.

Keep citations complete and properly formatted. Include the full bibliographic reference in the citation table, not just an abbreviated version. This maintains academic standards and makes it easy for others to verify and build upon your work.

Regularly back up your database file (yoga_therapy.db). Since all your research data lives in this single file, backing it up protects months or years of data entry work.

### Extending the System in the Future

The architecture I've built is designed to grow with your research needs. When you're ready to add CVR logic, you'll add new fields to the Practice model and new methods to the recommendation engine for filtering. The core structure remains unchanged.

If you need to add more koshas or subdivide existing ones into more granular categories, the flexible structure accommodates this easily. Just add the new category names in the data and update the ordering in the recommendation engine.

As your RAG chatbot evolves, you might want additional API endpoints that provide data in different formats or with different filtering options. The Flask application structure makes it straightforward to add new endpoints without disrupting existing functionality.

### Troubleshooting Common Issues

If practices aren't showing up in combined recommendations when you expect them to, check first that the practices are actually linked to both diseases in the database. Use the web interface to view each disease and confirm the practice appears in its practice list.

If duplicate practices aren't being removed correctly, verify that the practice names are spelled identically in both disease entries. Remember that the system is case-insensitive for matching, but spelling must be exact.

If contraindications aren't being applied, ensure the contraindication entry exactly matches the practice name and practice segment. Even small discrepancies will prevent the matching from working.

### Preparing for RAG Integration

When you're ready to connect your RAG chatbot, you'll need to set up the communication between the two systems. The chatbot will need to be configured to make HTTP requests to your Flask server. I recommend keeping the Flask application running on a dedicated server or port that the RAG system can access reliably.

The RAG system should handle the natural language processing to extract disease names, then format them into the JSON structure your API expects. Error handling is important here - if the RAG extracts a disease name that doesn't exist in your database, your API returns an error message that the chatbot should present helpfully to the user.

Consider adding logging to track which disease combinations doctors are requesting most frequently. This research data could be valuable for understanding clinical patterns and prioritizing future data entry efforts.

## Next Steps for Your BTP Project

Now that you understand the architecture, start by running the data import script with your sample data to see everything working. Then practice using the web interface to add a new disease and a few practices. This hands-on experience will help you understand the data flow.

Once comfortable with the basics, work with your team to decide which diseases you'll prioritize for data entry. Create a spreadsheet listing all the practices you need to enter for each disease, then systematically work through them using the web interface.

As you accumulate more data, regularly test the recommendation engine with different disease combinations to ensure the duplicate removal and contraindication logic are working correctly. This testing validates that your system is producing clinically appropriate recommendations.

When your chatbot team is ready for integration, provide them with the API documentation (which is embedded in the Flask routes) and work together to handle the data flow smoothly. Start with simple test cases and gradually increase complexity.

Remember that this system is a living research tool. As you discover new practices, techniques, or contraindications in your literature review, continuously update the database. The value of your system grows with the comprehensiveness and accuracy of the data it contains.