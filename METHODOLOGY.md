# Methodology: Personalized Yoga Therapy Management System
## Evidence-Based Database Based on IAYT Modules

---

## 1. Introduction and System Overview

### 1.1 Purpose and Scope

The Personalized Yoga Therapy Management System is a comprehensive, evidence-based database and recommendation engine designed to manage, organize, and generate personalized yoga therapy protocols based on research modules following the International Association of Yoga Therapists (IAYT) framework. The system serves as a research-grade platform for managing yoga therapy practices, tracking supporting evidence through Randomized Controlled Trials (RCTs), and generating evidence-based recommendations for clinical applications.

The system addresses a critical challenge in yoga therapy: when patients present with multiple co-morbid conditions, clinicians must combine therapeutic practices from different treatment protocols. Simply merging protocols can lead to duplicate practices, contraindicated combinations, and loss of traceability to original research sources. This system automates the intelligent combination of practices while maintaining academic rigor, safety, and evidence-based prioritization.



### 1.3 System Architecture

The system is built using a three-tier architecture:

1. **Data Layer**: SQLite database with SQLAlchemy ORM for data persistence
2. **Business Logic Layer**: Python-based recommendation engine and data processing modules
3. **Presentation Layer**: Flask-based web application with HTML/CSS/JavaScript frontend

---

## 2. Database Schema and Data Models

### 2.1 Core Entities

#### 2.1.1 Disease Model

The `Disease` model represents medical conditions or health issues for which yoga therapy protocols exist.

**Attributes:**
- `id`: Primary key (Integer)
- `name`: Disease name (String, unique, required)
- `description`: Detailed description of the disease (Text, optional)

**Relationships:**
- Many-to-many with `Practice` (a disease can have multiple practices, a practice can treat multiple diseases)
- Many-to-many with `Contraindication` (a disease can have multiple contraindications)
- One-to-many with `Module` (a disease can have multiple research modules)

**Purpose**: Serves as the primary organizational unit for therapy protocols. Diseases are the entry point for generating recommendations.

#### 2.1.2 Module Model

The `Module` model represents a research paper or clinical study that contains a set of practices for a specific disease.

**Attributes:**
- `id`: Primary key (Integer)
- `disease_id`: Foreign key to Disease (Integer, required)
- `developed_by`: Citation string (e.g., "Naveen et al., 2013")
- `paper_link`: URL to the research paper (String, optional)
- `module_description`: Description of the module and its approach (Text, optional)

**Relationships:**
- Many-to-one with `Disease` (each module belongs to one disease, but a disease can have multiple modules)
- One-to-many with `Practice` (a module contains multiple practices)

**Purpose**: Maintains academic integrity by linking practices to their source research. Allows multiple research perspectives on the same disease to coexist in the system.

#### 2.1.3 Practice Model

The `Practice` model represents an individual yoga practice with comprehensive details.

**Attributes:**

*Practice Identification:*
- `id`: Primary key (Integer)
- `practice_sanskrit`: Sanskrit name of the practice (String, optional)
- `practice_english`: English name of the practice (String, required)

*Classification:*
- `practice_segment`: Category/segment classification (String, required)
  - Options: Preparatory Practice, Breathing Practice, Sequential Yogic Practice, Yogasana, Pranayama, Meditation, Chanting, Additional Practices, Kriya (Cleansing Techniques), Yogic Counselling
- `sub_category`: Subcategory within the segment (String, optional)
- `kosha`: Pancha Kosha classification (String, optional)
  - Options: Annamaya Kosha, Pranamaya Kosha, Manomaya Kosha, Vijnanamaya Kosha, Anandamaya Kosha

*Practice Details:*
- `rounds`: Number of rounds/repetitions (Integer, optional)
- `time_minutes`: Duration in minutes (Float, optional)
- `strokes_per_min`: Strokes per minute (Integer, optional)
- `strokes_per_cycle`: Strokes per cycle (Integer, optional)
- `rest_between_cycles_sec`: Rest duration between cycles in seconds (Integer, optional)
- `variations`: JSON string containing practice variations with references (Text, optional)
- `steps`: JSON string containing step-by-step instructions (Text, optional)
- `description`: Brief description of the practice (Text, optional)
- `how_to_do`: Detailed instructions (Text, optional)
- `cvr_score`: Capacity-Variability-Responsiveness score (Float, optional)

*Media Attachments:*
- `photo_path`: Path to practice photo (String, optional)
- `video_path`: Path to practice video (String, optional)

*Relationships and Evidence:*
- `citation_id`: Foreign key to Citation (Integer, optional)
- `module_id`: Foreign key to Module (Integer, optional)
- `rct_count`: Number of RCTs supporting this practice (Integer, default=0, automatically calculated)

**Relationships:**
- Many-to-many with `Disease` (a practice can treat multiple diseases)
- Many-to-one with `Module` (a practice belongs to one module, but can be associated with multiple diseases)
- Many-to-one with `Citation` (a practice can have one citation)

**Purpose**: Central entity storing all practice information. The system groups practices that are identical except for their module association, allowing the same practice to appear in multiple modules while maintaining a single source of truth for practice details.

#### 2.1.4 Citation Model

The `Citation` model stores bibliographic references for practices.

**Attributes:**
- `id`: Primary key (Integer)
- `citation_text`: Citation text (Text, required, e.g., "Dr Naveen GH et al., 2013")
- `citation_type`: Type of citation (String, optional: 'research_paper', 'book', 'study')
- `full_reference`: Complete bibliographic reference (Text, optional)
- `url`: URL to the source (String, optional)

**Relationships:**
- One-to-many with `Practice` (a citation can be used by multiple practices)

**Purpose**: Centralized citation management. When multiple practices reference the same source, they share a single citation entry, ensuring consistency and ease of updates.

#### 2.1.5 Contraindication Model

The `Contraindication` model stores practices that should be avoided for specific diseases.

**Attributes:**
- `id`: Primary key (Integer)
- `practice_sanskrit`: Sanskrit name of contraindicated practice (String, optional)
- `practice_english`: English name of contraindicated practice (String, required)
- `practice_segment`: Practice segment/category (String, required)
- `sub_category`: Subcategory (String, optional)
- `reason`: Reason for contraindication (Text, optional)
- `source_type`: Source type (String, optional: 'book', 'paper', 'ancient_text')
- `source_name`: Source name or link (String, optional)
- `page_number`: Page number/range (String, optional)
- `apa_citation`: Full APA citation (Text, optional)

**Relationships:**
- Many-to-many with `Disease` (a contraindication can apply to multiple diseases)

**Purpose**: Safety mechanism ensuring that contraindicated practices are automatically excluded from recommendations.

#### 2.1.6 RCT (Randomized Controlled Trial) Model

The `RCT` model stores comprehensive data about clinical studies supporting practices.

**Attributes:**

*Study Identification:*
- `id`: Primary key (Integer)
- `doi`: Digital Object Identifier (String, optional)
- `pmic_nmic`: PMIC/NMIC identifier (String, optional)
- `title`: Study title (Text, optional)
- `parenthetical_citation`: Citation text stored for reference (Text, optional)
- `citation_full`: Full citation (Text, optional)
- `citation_link`: URL to the paper (String, optional)
- `study_type`: Type of study (String, optional: 'RCT', 'Clinical Trial', 'Others')

*Database and Search Information:*
- `database_journal`: Database or journal name (String, optional, e.g., "PubMed")
- `keywords`: Search keywords used (Text, optional)
- `data_enrolled_date`: Date data was enrolled (String, optional)

*Demographics:*
- `participant_type`: Type of participants (String, optional, e.g., "teacher", "army", "nurse", "elderly")
- `age_mean`: Mean age (Float, optional)
- `age_std_dev`: Standard deviation of age (Float, optional)
- `age_range_calculated`: Calculated age range (String, optional)
- `gender_male`: Number of male participants (Integer, optional)
- `gender_female`: Number of female participants (Integer, optional)
- `gender_not_mentioned`: Number of participants with unspecified gender (Integer, optional)

*Intervention Details:*
- `intervention_practices`: JSON string containing list of practices with categories (Text, optional)
- `duration_type`: Duration type (String, optional: 'days', 'weeks', 'months')
- `duration_value`: Duration value (Integer, optional, e.g., 12)
- `frequency_per_duration`: Frequency description (String, optional, e.g., "3 times per week")

*Results:*
- `scales`: Assessment scales used (Text, optional, comma-separated)
- `results`: Study results (Text, optional)
- `conclusion`: Study conclusion (Text, optional)
- `remarks`: Additional remarks, including contraindications or special cases (Text, optional)

**Relationships:**
- Many-to-many with `Disease` (an RCT can study multiple diseases)
- Many-to-many with `RCTSymptom` (an RCT can measure multiple symptoms)

**Purpose**: Provides evidence base for practice recommendations. RCT count is calculated for each practice-disease combination, with higher counts indicating stronger evidence.

#### 2.1.7 RCTSymptom Model

The `RCTSymptom` model stores symptom-level data from RCTs with statistical significance.

**Attributes:**
- `id`: Primary key (Integer)
- `symptom_name`: Name of the symptom (String, required)
- `p_value_operator`: Statistical operator (String, optional: '<', '>', '<=', '>=', '=')
- `p_value`: P-value (Float, optional)
- `is_significant`: Significance indicator (Integer, optional: 1 if p ≤ 0.05, 0 otherwise)
- `scale`: Assessment scale used (String, optional)

**Relationships:**
- Many-to-many with `RCT` (a symptom can be measured in multiple RCTs)

**Purpose**: Enables detailed analysis of treatment effects on specific symptoms, supporting evidence-based practice selection.

### 2.2 Association Tables

The system uses several association tables to manage many-to-many relationships:

1. **disease_practice_association**: Links diseases to practices
2. **disease_contraindication_association**: Links diseases to contraindications
3. **rct_symptom_association**: Links RCTs to symptoms
4. **rct_disease_association**: Links RCTs to diseases

---

## 3. Module-Based Organization System

### 3.1 Module Concept

A **Module** represents a research paper or clinical study that contains a structured set of yoga therapy practices for a specific disease. The module-based organization ensures:

1. **Academic Traceability**: Every practice can be traced to its source research
2. **Multiple Perspectives**: Different research approaches to the same disease can coexist
3. **Evidence Hierarchy**: Practices can be prioritized based on module quality and RCT support
4. **Citation Management**: Direct links to research papers for verification

### 3.2 Module Creation Workflow

#### 3.2.1 Creating a New Module

1. **Disease Selection/Creation**:
   - User enters disease name with autocomplete functionality
   - System searches existing diseases and suggests matches
   - If disease doesn't exist, user can create it by pressing Enter
   - This ensures diseases are created only through modules, maintaining data integrity

2. **Module Information Entry**:
   - **Developed By**: Citation (e.g., "Naveen et al., 2013")
   - **Paper Link**: URL to the research paper (optional but recommended)
   - **Module Description**: Description of the module's approach and methodology

3. **Practice Addition**:
   - Practices are added within the module context
   - Disease association is automatic (inherited from module)
   - All practice details are entered (Sanskrit name, English name, Category, Kosha, etc.)
   - Variations are entered in the "How to do!" section
   - Media attachments (photos/videos) can be added

4. **Module Completion**:
   - User can add multiple practices to a module
   - After each practice, option to "Add another practice" or "End the module"
   - Module is saved and can be viewed, edited, or deleted

### 3.3 Module Display and Navigation

#### 3.3.1 Module List View

The modules page displays:
- **Module Name**: "Developed By" citation (hyperlinked to paper if link exists)
- **Disease**: Associated disease name (hyperlinked to disease view)
- **Number of Practices**: Count of practices in the module
- **Actions**: View, Edit, Delete options

#### 3.3.2 Module Detail View

Clicking on a module displays:
- Module title (hyperlinked to paper)
- Associated disease (hyperlinked to disease view)
- Module description
- Practices organized by Category (practice segment)
- Within each category, practices listed with all details

### 3.4 Practice Grouping Logic

The system implements intelligent practice grouping:

- **Grouping Key**: Practices are grouped based on all attributes EXCEPT `module_id`
- **Same Practice, Multiple Modules**: If the same practice appears in multiple modules, the system maintains separate practice entries (one per module) but groups them for display
- **Editing Behavior**: When editing a practice, all related practices (same attributes, different modules) are updated simultaneously
- **Module Assignment**: Each practice entry maintains its module association for traceability

This approach ensures:
- Practices maintain their module associations for academic integrity
- Users can edit practice details once and have changes apply to all module instances
- The system can display which modules contain which practices
- Recommendations can prioritize practices based on module quality and RCT support

---

## 4. Practice Management System

### 4.1 Practice Categories and Kosha Mapping

#### 4.1.1 Practice Categories

The system uses the following practice categories (formerly called "Practice Segments"):

1. **Preparatory Practice**: Warm-up and preparatory exercises
2. **Breathing Practice**: Basic breathing exercises
3. **Sequential Yogic Practice**: Sequential movement practices (formerly "Suryanamaskara")
4. **Yogasana**: Yoga postures and asanas
5. **Pranayama**: Advanced breath control techniques
6. **Meditation**: Meditation practices
7. **Chanting**: Chanting and mantra practices
8. **Additional Practices**: Context-dependent practices
9. **Kriya (Cleansing Techniques)**: Cleansing and purification practices
10. **Yogic Counselling**: Counseling and guidance practices

#### 4.1.2 Automatic Kosha Mapping

The system automatically maps practice categories to Pancha Kosha:

| Category | Kosha |
|----------|-------|
| Preparatory Practice | Annamaya Kosha |
| Yogasana | Annamaya Kosha |
| Kriya (Cleansing Techniques) | Annamaya Kosha |
| Sequential Yogic Practice | Annamaya Kosha |
| Breathing Practice | Pranamaya Kosha |
| Pranayama | Pranamaya Kosha |
| Meditation | Manomaya Kosha |
| Chanting | Manomaya Kosha |
| Yogic Counselling | Vijnanamaya Kosha |
| Additional Practices | (User-determined or empty) |

This mapping is applied automatically when a category is selected, but users can override it if needed.

### 4.2 Practice Addition Workflows

#### 4.2.1 Adding Practices from Module Context

When adding practices within a module:

1. **Disease Association**: Automatically inherited from module (no manual selection needed)
2. **Required Fields**:
   - English Name (required)
   - Category (required)
   - Kosha (required, auto-filled based on category)
3. **Optional Fields**:
   - Sanskrit Name (with autocomplete from existing practices)
   - Sub-category
   - Rounds, Duration, Strokes
   - Description
   - Variations (in "How to do!" section)
   - CVR Score (optional)
   - Media attachments (photos and videos)
4. **File Uploads**:
   - Photo upload: Supported formats (png, jpg, jpeg, gif), max 16MB
   - Video upload: Supported formats (mp4, avi, mov, wmv), max 16MB
   - Files are stored in `web/static/uploads/photos/` and `web/static/uploads/videos/`
   - Files are named with practice ID prefix for uniqueness
5. **No "How to Do" Field**: The detailed instruction field is removed in module-based addition
6. **Variations**: Entered directly in the "How to do!" section with reference sources

#### 4.2.2 Adding Practices from Practices Tab

When adding practices from the main Practices tab:

1. **Disease Association**: User selects diseases from checkboxes
2. **Module Selection**: For each selected disease, user can specify the module the practice is referred from
   - Autocomplete functionality searches modules for that specific disease
   - User can select from existing modules or leave blank
3. **All Fields Available**: Including "How to Do" detailed instructions, CVR score, and media uploads
4. **Multiple Module Support**: A practice can be associated with different modules for different diseases
5. **File Uploads**: Same photo and video upload support as module-based addition

### 4.3 Practice Editing System

#### 4.3.1 Intelligent Practice Grouping

When editing a practice:

1. **Related Practice Detection**: System finds all practices with identical attributes (except module_id)
2. **Synchronized Updates**: Changes to practice details update all related practices
3. **Module Management**: 
   - User can see all modules associated with the practice (grouped by disease)
   - User can add/remove modules for each disease
   - Multiple modules per disease are supported
4. **Disease Association**: User can add/remove disease associations
5. **Module Assignment**: For each disease, user can specify which modules the practice belongs to

#### 4.3.2 Module Selection Interface

- **Dynamic Module Fields**: When a disease is checked, module selection fields appear
- **Add Module Button**: Users can add multiple modules per disease
- **Remove Module Button**: Users can remove modules
- **Autocomplete**: Module names are searchable with autocomplete
- **Module Display**: Shows module name (e.g., "Naveen et al., 2013") with link to paper

### 4.4 Practice Variations System

#### 4.4.1 "How to do!" Section

The "How to do!" section (formerly "Variations") allows users to:

1. **Add Variations**: Click "Add Variation" to add a new variation
2. **Variation Details**:
   - Variation description (text field)
   - Reference source (where the variation is mentioned: paper/book)
3. **Remove Variations**: Each variation has a "Remove" button
4. **Storage**: Variations are stored as JSON with structure:
   ```json
   [
     {
       "text": "Variation description",
       "referred_in": "Source reference"
     }
   ]
   ```

---

## 5. RCT Database and Evidence Scoring

### 5.1 RCT Data Collection

The RCT database stores comprehensive information about clinical studies:

1. **Study Identification**: DOI, PMIC/NMIC, title, citations, links
2. **Search Methodology**: Database/journal, keywords, search filters
3. **Demographics**: Participant type, age (mean, std dev, range), gender distribution
4. **Intervention Details**: 
   - Practices used (stored as JSON with categories)
   - Duration (type: days/weeks/months, value, frequency)
5. **Results**: 
   - Assessment scales used
   - Results description
   - Conclusion
   - Remarks (including contraindications)

### 5.2 RCT-Practice Matching

The system matches RCTs to practices through:

1. **Disease Association**: RCT must be associated with at least one disease that the practice treats
2. **Practice Matching**:
   - **Specific Match**: RCT mentions the practice by name (Sanskrit or English) - exact match required
   - **Category Match**: RCT mentions the practice category (e.g., "Pranayama") - all practices in that category for the associated disease are counted
3. **RCT Count Calculation**: 
   - For each practice-disease combination, count all matching RCTs
   - Higher count = stronger evidence
   - Count is automatically recalculated when:
     - A new RCT is added with matching practices
     - An RCT is deleted or modified
     - Practice category or disease associations change
   - The system uses `recalculate_practice_rct_count()` function to maintain accuracy
4. **Automatic Increment/Decrement**: When RCTs are added or removed, practice RCT counts are automatically updated

### 5.3 Evidence-Based Prioritization

The RCT count serves as an evidence score:

- **Higher RCT Count**: Practices with more supporting RCTs are prioritized in recommendations
- **Evidence Hierarchy**: System can rank practices by evidence strength
- **Transparency**: RCT count is displayed in practice lists and recommendations
- **Traceability**: Users can view which RCTs support each practice

### 5.4 Symptom-Level Analysis

The RCTSymptom model enables detailed analysis:

- **Symptom Tracking**: Each symptom measured in an RCT is stored separately
- **Statistical Significance**: 
  - P-values with operators (<, >, <=, >=, =) are tracked
  - Automatic significance calculation (p ≤ 0.05 = significant)
  - Significance indicator stored as integer (1 = significant, 0 = not significant)
- **Scale Information**: Assessment scales are recorded per symptom
- **RCT Association**: Symptoms are linked to RCTs through many-to-many relationship
- **Future Enhancement**: Can support symptom-specific practice recommendations

---

## 6. Recommendation Engine Logic

### 6.1 Recommendation Generation Process

The recommendation engine follows a systematic process:

#### Step 1: Disease Fetching
- Input: List of disease names
- Process: Query database for matching diseases (case-insensitive, partial matching)
- Output: List of Disease objects

#### Step 2: Practice Collection
- Process: Collect all practices associated with the fetched diseases
- Source: Practices linked to diseases through many-to-many relationship
- Module Information: Include module details (developed_by, paper_link) for each practice

#### Step 3: Practice Organization
- Process: Organize practices by Category (practice segment)
- Order: Maintains predefined segment order for logical flow
- Deduplication: Remove exact duplicates (same name, same category)

#### Step 4: Contraindication Application
- Process: For each disease combination, check contraindications
- Filtering: Remove practices that are contraindicated for any of the diseases
- Safety: Ensures no contraindicated practices appear in recommendations

#### Step 5: Output Formatting
- Structure: Organize by Category, then by Kosha
- Citations: Include module information and citations
- Evidence: Display RCT counts for evidence-based prioritization
- Media: Include links to photos/videos if available

### 6.2 Deduplication Logic

The system removes duplicate practices by:

1. **Name Matching**: Compare practice names (case-insensitive)
2. **Category Matching**: Ensure practices are in the same category
3. **Preservation**: Keep the practice with the highest RCT count
4. **Citation Preservation**: Maintain citation information from the preserved practice

### 6.3 Contraindication Logic

Contraindications are applied as follows:

1. **Disease-Based Filtering**: For each disease in the combination, get all contraindications
2. **Practice Matching**: Match contraindicated practices by:
   - Practice name (case-insensitive)
   - Practice category (exact match required)
3. **Exclusion**: Remove matched practices from recommendations
4. **Reporting**: Optionally report which practices were excluded and why

### 6.4 Evidence-Based Prioritization

Practices are prioritized based on:

1. **RCT Count**: Higher count = higher priority
2. **Module Quality**: Can be enhanced with module quality scores
3. **Category Order**: Maintains logical flow (Preparatory → Breathing → Asana → Pranayama → Meditation)
4. **Kosha Organization**: Groups practices by Pancha Kosha for holistic approach

---

## 7. Disease Management System

### 7.1 Disease Creation

Diseases are created through the module creation process:

1. **Module-First Approach**: Diseases are created when creating modules
2. **Autocomplete**: System suggests existing diseases as user types
3. **New Disease Creation**: User can create new disease by pressing Enter
4. **Data Integrity**: Ensures all diseases have at least one associated module

### 7.2 Disease Display

#### 7.2.1 Disease List View

The diseases page displays:
- **Disease Name**: Hyperlinked to disease detail view
- **Modules**: List of all modules associated with the disease
  - Module name (hyperlinked to paper if link exists)
  - Practice count for each module
  - Format: "Module Name (X practices), Module Name (Y practices)"

#### 7.2.2 Disease Detail View

Clicking on a disease displays:
- Disease name and description
- **Module-Wise Organization**: Practices organized by module
- **Segment-Wise Organization**: Within each module, practices organized by Category
- **Practice Details**: All practice information with citations and RCT counts

### 7.3 Disease-Practice Relationships

- **Many-to-Many**: A disease can have multiple practices, a practice can treat multiple diseases
- **Module Context**: Practices are associated with diseases through modules
- **Direct Association**: Practices can also be directly associated with diseases (for practices added from Practices tab)

---

## 8. Web Interface and User Management

### 8.1 Interface Structure

The web interface provides:

1. **Home Page**: 
   - System title: "Personalized Yoga Therapy Management System"
   - Subtitle: "Evidence Based Database Based on IAYT Module"
   - Statistics dashboard (diseases, practices, RCTs, contraindications)
   - Purpose statement
   - Confidentiality disclaimer
   - System logic explanation

2. **Navigation Tabs**:
   - Home
   - Modules
   - Diseases
   - Practices
   - Contraindications
   - RCT Database
   - Recommendations

3. **Module Management**:
   - List all modules (with filtering by disease)
   - Add new module
   - View module details
   - Edit module (including paper link and description)
   - Delete module
   - Add practices to module
   - Module-wise practice organization

4. **Practice Management**:
   - List all practices (grouped by attributes, showing all modules)
   - Add new practice (with file upload support)
   - Edit practice (with synchronized updates to related practices)
   - Delete practice
   - Search and filter practices
   - Upload photos and videos for practices
   - CVR score entry and editing

5. **Disease Management**:
   - List all diseases with modules
   - View disease details
   - Module-wise and segment-wise practice display
   - Disease filtering in module list

6. **Contraindication Management**:
   - List all contraindications
   - Add new contraindication
   - Edit contraindication
   - Delete contraindication
   - Link contraindications to multiple diseases

7. **RCT Database**:
   - List all RCTs (with comprehensive study information)
   - Add new RCT (with intervention practices, symptoms, demographics)
   - Edit RCT
   - Delete RCT (with automatic RCT count updates)
   - View RCT details
   - Automatic RCT count calculation for practices
   - Symptom-level data with p-values and significance indicators

8. **Recommendations**:
   - Generate recommendations for multiple diseases
   - Module-based practice selection
   - RCT count display
   - Contraindication filtering
   - Organized by Kosha and Category

9. **Export Functionality**:
   - Export diseases to CSV
   - Export practices to CSV (excluding media files)
   - Export contraindications to CSV
   - Export RCTs to CSV (with all study details)

### 8.2 Autocomplete Functionality

The system provides autocomplete for:

1. **Disease Names**: When creating modules, suggests existing diseases
2. **Sanskrit Practice Names**: When adding practices, suggests existing Sanskrit names
3. **Module Names**: When associating practices with modules, suggests modules for the selected disease

### 8.3 Data Validation

- **Required Fields**: Enforced at form level and database level
- **Data Types**: Validated before database insertion
- **Relationships**: Foreign key constraints ensure referential integrity
- **Uniqueness**: Disease names must be unique

---

## 9. Data Entry Workflows

### 9.1 Complete Module Creation Workflow

1. **Navigate to Modules** → Click "Add New Module"
2. **Enter Disease**: Type disease name, select from suggestions or create new
3. **Enter Module Information**:
   - Developed By (e.g., "Naveen et al., 2013")
   - Paper Link (URL)
   - Module Description
4. **Save Module** → Redirected to module view
5. **Add Practices**:
   - Click "Add Practice to Module"
   - Enter practice details:
     - Sanskrit Name (optional, with autocomplete)
     - English Name (required)
     - Category (required, auto-fills Kosha)
     - Kosha (required, auto-filled)
     - Sub-category, Rounds, Duration, Strokes (optional)
     - Description (optional)
     - Variations in "How to do!" section
     - Media attachments
   - Save practice
   - Choose: "Add another practice" or "End module"

### 9.2 Practice Addition from Practices Tab

1. **Navigate to Practices** → Click "Add New Practice"
2. **Enter Practice Details**: All standard practice fields
3. **Associate with Diseases**:
   - Check diseases that use this practice
   - For each checked disease, enter module name (with autocomplete)
4. **Save Practice** → Practice is created and linked to specified modules

### 9.3 RCT Entry Workflow

1. **Navigate to RCT Database** → Click "Add New RCT"
2. **Enter Study Information**: DOI, title, citations, links
3. **Enter Search Information**: Database/journal, keywords
4. **Enter Demographics**: Participant type, age, gender
5. **Enter Intervention**: Practices (JSON format), duration, frequency
6. **Enter Results**: Scales, results, conclusion, remarks
7. **Associate with Diseases**: Select diseases studied
8. **Add Symptoms**: Enter symptom-level data with p-values
9. **Save RCT** → System automatically updates RCT counts for matching practices

---

## 10. Quality Assurance and Validation

### 10.1 Data Quality Measures

1. **Consistency Checks**:
   - Practice name standardization
   - Category name consistency
   - Disease name uniqueness

2. **Completeness Checks**:
   - Required fields validation
   - Relationship integrity (practices must have diseases, modules must have diseases)

3. **Accuracy Checks**:
   - Citation format validation
   - URL validation for paper links
   - Date format validation for RCTs

### 10.2 Recommendation Quality

1. **Deduplication Verification**: Ensure no duplicate practices in recommendations
2. **Contraindication Verification**: Ensure no contraindicated practices appear
3. **Citation Verification**: Ensure all practices have proper citations/module information
4. **Evidence Verification**: Verify RCT counts are accurate

### 10.3 Testing Procedures

1. **Unit Tests**: Test individual functions (deduplication, contraindication filtering)
2. **Integration Tests**: Test complete recommendation generation
3. **Data Validation Tests**: Test data entry and validation
4. **User Acceptance Tests**: Test workflows from user perspective

---

## 11. API Endpoints

### 11.1 Recommendation API

**Endpoint**: `/api/recommendations`
**Method**: POST
**Request Body**:
```json
{
  "diseases": ["Depression", "GAD"]
}
```
**Response**: JSON object with practices organized by category and kosha

### 11.2 Summary API

**Endpoint**: `/api/summary`
**Method**: POST
**Request Body**:
```json
{
  "diseases": ["Depression", "GAD"]
}
```
**Response**: Human-readable text summary of recommendations

### 11.3 Search APIs

- `/api/practice/search?q=<query>`: Search practices by Sanskrit name
- `/api/disease/search?q=<query>`: Search diseases by name
- `/api/module/search?q=<query>&disease_id=<id>`: Search modules by name for a specific disease
- `/api/module/search/all?q=<query>`: Search all modules by name
- `/api/practices`: Get all practices (for RCT form)
- `/api/practices/by-disease/<disease_id>`: Get practices belonging to modules for a specific disease
- `/api/rct-count?disease=<name>&practice=<name>`: Get RCT count for a disease-practice combination

### 11.4 Export APIs

- `/export/diseases/csv`: Export all diseases to CSV format
- `/export/practices/csv`: Export all practices to CSV format (excluding media files)
- `/export/contraindications/csv`: Export all contraindications to CSV format
- `/export/rcts/csv`: Export all RCTs to CSV format with comprehensive study details

---

## 12. Future Enhancements

### 12.1 CVR (Capacity-Variability-Responsiveness) Score

The system now includes CVR score support:

1. **Database Implementation**: 
   - `cvr_score` field added to Practice model (Float, optional)
   - Migration script (`add_cvr_score_field.py`) ensures database compatibility
   - Backward compatible - existing data remains valid (CVR fields optional)

2. **User Interface**: 
   - CVR score field available in practice addition forms
   - CVR score editing in practice edit forms
   - Displayed in practice lists and detail views

3. **Future Enhancement**: 
   - CVR-based filtering in recommendation engine (architecture ready)
   - Patient assessment integration for personalized practice selection
   - Practice prioritization based on CVR scores

### 12.2 Advanced Evidence Scoring

- **Quality Scores**: Rate RCTs by quality (e.g., JADAD score)
- **Weighted RCT Count**: Weight RCTs by quality in count calculation
- **Meta-Analysis Integration**: Support for meta-analysis results

### 12.3 Symptom-Specific Recommendations

- **Symptom Matching**: Match practices to specific symptoms
- **Symptom Prioritization**: Prioritize practices based on symptom improvement
- **Personalized Protocols**: Generate protocols targeting specific symptoms

### 12.4 Data Export and Backup

The system now includes comprehensive export functionality:

- **CSV Export**: Export all major entities to CSV format
  - Diseases export includes module information
  - Practices export includes all details except media files
  - Contraindications export includes disease associations
  - RCTs export includes comprehensive study details, symptoms, and demographics
- **Data Portability**: CSV exports enable data analysis in external tools
- **Backup Strategy**: Regular CSV exports serve as data backups
- **Future Enhancement**: Additional export formats (JSON, Excel) can be added

---

## 13. Conclusion

The Personalized Yoga Therapy Management System provides a comprehensive, evidence-based platform for managing yoga therapy protocols. Its module-based organization ensures academic integrity and traceability, while its intelligent recommendation engine combines practices safely and efficiently. The system's architecture supports future enhancements while maintaining backward compatibility, making it a robust foundation for ongoing research and clinical applications.

The integration of Pancha Kosha framework, IAYT module structure, and evidence-based prioritization creates a unique system that bridges traditional yoga therapy knowledge with modern research methodologies. This system serves as a valuable tool for researchers, clinicians, and yoga therapists working in evidence-based practice.

---

## 14. References and Citations

This methodology document describes the system architecture and implementation. For specific research papers and modules referenced in the system, please refer to:

- Individual module pages in the web interface (with paper links)
- RCT database entries (with full citations)
- Citation management system (with complete bibliographic references)

---

**Document Version**: 2.1  
**Last Updated**: 2024  
**System Version**: Based on IAYT Module Framework with Pancha Kosha Integration, RCT Database, CVR Scores, and Export Functionality

### Version 2.1 Updates

- **CVR Score Implementation**: Added CVR score field to practices with migration support
- **RCT Database Enhancement**: Complete RCT management with automatic practice matching and count calculation
- **File Upload Support**: Photo and video uploads for practices with file management
- **Export Functionality**: CSV export for diseases, practices, contraindications, and RCTs
- **Enhanced RCT-Practice Matching**: Automatic increment/decrement of RCT counts when RCTs are added/removed
- **Symptom-Level Data**: Detailed symptom tracking with p-values and significance indicators
- **Module Enhancements**: Paper link and description fields added to modules
- **Recommendation System**: Integration of RCT counts and evidence-based prioritization in recommendations

