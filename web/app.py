"""
Web Interface for Yoga Therapy Data Management

This Flask application provides a simple web interface where researchers
and practitioners can manage the yoga therapy database without writing code.

Features:
- Add/edit/view diseases
- Add/edit/view practices for each disease
- Manage contraindications
- Add citations and research references
- Search and filter practices
"""

import sys
import os
import json
import csv
import io
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response, session as flask_session
from sqlalchemy import text
from sqlalchemy.orm import joinedload, selectinload
from database.models import (
    Disease, Practice, Citation, Contraindication, DiseaseCombination, Module,
    RCT, RCTSymptom,
    create_database, get_engine, get_session, disease_contraindication_association,
    disease_practice_association, rct_disease_association
)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

# Add custom Jinja2 filters
@app.template_filter('from_json')
def from_json_filter(value):
    """Convert JSON string to Python object"""
    if not value:
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []

# Enumerations enforced across the app
ALLOWED_CATEGORIES = [
    # Canonical names
    'Preparatory practices',
    'Breathing practices',
    'Sequential yogic practices',
    'Yogasana',
    'Pranayama',
    'Meditation',
    'Chanting',
    'Additional practices',
    'Kriya (cleansing)',
    'Yogic counselling',
    'Lifestyle modifications (Anna)',
    'Yogic diet (Anna)',
    'Chair Yoga (Anna)',
    # Backward-compatible legacy spellings
    'Preparatory Practice',
    'Breathing Practice',
    'Sequential Yogic Practice',
    'Additional Practices',
    'Kriya (Cleansing Techniques)',
    'Yogic Counselling',
    'Suryanamaskara',
]

ALLOWED_KOSHAS = [
    'Annamaya',
    'Pranamaya',
    'Manomaya',
    'Vijnanamaya',
    'Anandamaya',
]

# Database path
DB_PATH = 'sqlite:///yoga_therapy.db'


def _is_valid_category(category: str) -> bool:
    return category in ALLOWED_CATEGORIES


def _is_valid_kosha(kosha: str) -> bool:
    return kosha in ALLOWED_KOSHAS


def _ensure_category_and_kosha(practice_segment: str, kosha: str):
    """Validate enums early and raise ValueError if invalid."""
    if not _is_valid_category(practice_segment):
        raise ValueError(f'Invalid category "{practice_segment}". Must be one of: {", ".join(ALLOWED_CATEGORIES)}')
    if kosha and not _is_valid_kosha(kosha):
        raise ValueError(f'Invalid kosha "{kosha}". Must be one of: {", ".join(ALLOWED_KOSHAS)}')

# Configuration for file uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov', 'wmv'}
ALLOWED_MIME_TYPES = {
    'image/png',
    'image/jpeg',
    'image/gif',
    'video/mp4',
    'video/quicktime',
    'video/x-msvideo',
    'video/x-ms-wmv'
}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# Create upload directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'photos'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'videos'), exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_mimetype(file: FileStorage):
    """Strict MIME validation to avoid unexpected uploads."""
    mimetype = getattr(file, 'mimetype', '') or ''
    mimetype = mimetype.lower()
    return mimetype in ALLOWED_MIME_TYPES or mimetype.startswith('image/') or mimetype.startswith('video/')

# Enforce request body size limit for uploads (must be after MAX_FILE_SIZE is defined)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

def generate_practice_code(sanskrit_name, session=None, existing_codes=None):
    """
    Generate a practice code based on Sanskrit name.
    
    Methodology:
    - Take first letter of each word in Sanskrit name (capitalized)
    - If single word, take first 2-3 letters
    - Add a 2-digit number suffix if needed for uniqueness
    
    Examples:
    - Kapalabhati -> KAP01
    - Shavasana -> SHA01
    - Bhujangasana -> BHU01
    - Padmasana -> PAD01
    - Anulom Vilom -> AV01
    
    Args:
        sanskrit_name: The Sanskrit name of the practice
        session: Database session to check existing codes
        existing_codes: Set of existing codes to avoid duplicates
        
    Returns:
        A unique code string
    """
    import re
    
    if not sanskrit_name or not sanskrit_name.strip():
        return None
    
    # Get existing codes from database if session provided
    if session and existing_codes is None:
        existing_codes = set()
        all_practices = session.query(Practice).filter(Practice.code.isnot(None)).all()
        existing_codes = {p.code for p in all_practices}
    elif existing_codes is None:
        existing_codes = set()
    
    # Clean the Sanskrit name
    name = sanskrit_name.strip()
    
    # Split by spaces and get first letters
    words = name.split()
    
    if len(words) == 1:
        # Single word: take first 3 letters, capitalize
        base_code = name[:3].upper()
    else:
        # Multiple words: take first letter of each word
        base_code = ''.join([word[0].upper() for word in words if word])
    
    # Remove any non-alphabetic characters
    base_code = re.sub(r'[^A-Z]', '', base_code)
    
    if not base_code:
        # Fallback: use first 3 characters of name
        base_code = name[:3].upper()
        base_code = re.sub(r'[^A-Z]', '', base_code)
        if not base_code:
            base_code = 'PRC'  # Practice
    
    # Generate code with number suffix
    code = base_code
    counter = 1
    
    while code in existing_codes:
        # Add 2-digit suffix
        code = f"{base_code}{counter:02d}"
        counter += 1
        
        # Prevent infinite loop
        if counter > 99:
            # Use hash as fallback
            import hashlib
            hash_suffix = hashlib.md5(name.encode()).hexdigest()[:2].upper()
            code = f"{base_code}{hash_suffix}"
            break
    
    return code

def ensure_practice_code_column():
    """Ensure practices.code column exists for older databases."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(practices)"))
            columns = [row[1] for row in result]
            if 'code' not in columns:
                conn.execute(text("ALTER TABLE practices ADD COLUMN code VARCHAR(50)"))
                conn.commit()
    except Exception as exc:
        # Avoid crashing startup for non-SQLite or locked DB; surface in logs.
        print(f"Warning: failed to ensure practices.code column: {exc}")

# Initialize database on startup
create_database(DB_PATH)
ensure_practice_code_column()


def get_db_session():
    """Helper function to get database session"""
    return get_session(DB_PATH)


class Pagination:
    """Simple pagination class to mimic Flask-SQLAlchemy's pagination object"""
    def __init__(self, query, page, per_page, total, items):
        self.query = query
        self.page = page
        self.per_page = per_page
        self.total = total
        self.items = items
        self.pages = (total + per_page - 1) // per_page if per_page > 0 else 0
        self.has_prev = page > 1
        self.has_next = page < self.pages
        self.prev_num = page - 1 if self.has_prev else None
        self.next_num = page + 1 if self.has_next else None


def paginate_query(query, page, per_page, error_out=False):
    """Manually paginate a SQLAlchemy query"""
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 20
    
    # Get total count
    total = query.count()
    
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Get items for current page
    items = query.offset(offset).limit(per_page).all()
    
    return Pagination(query, page, per_page, total, items)


@app.route('/')
def index():
    """Home page showing overview of the system"""
    session = get_db_session()
    
    # Get statistics
    disease_count = session.query(Disease).count()
    practice_count = session.query(Practice).count()
    rct_count = session.query(RCT).count()
    contraindication_count = session.query(Contraindication).count()
    
    session.close()
    
    return render_template('index.html',
                         disease_count=disease_count,
                         practice_count=practice_count,
                         rct_count=rct_count,
                         contraindication_count=contraindication_count)


@app.route('/diseases')
def list_diseases():
    """List all diseases with pagination and eager loading"""
    session = get_db_session()
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        per_page = min(per_page, 100)  # Cap at 100 per page
        
        # Use eager loading to prevent N+1 queries
        query = session.query(Disease).options(
            selectinload(Disease.practices),
            selectinload(Disease.modules)
        )
        
        # Paginate results
        pagination = paginate_query(query, page, per_page)
        
        diseases = pagination.items
        
        return render_template('diseases.html', 
                             diseases=diseases,
                             pagination=pagination)
    finally:
        session.close()


@app.route('/disease/add', methods=['GET', 'POST'])
def add_disease():
    """Add a new disease"""
    if request.method == 'POST':
        session = get_db_session()
        
        try:
            # Check if disease already exists
            existing_disease = session.query(Disease).filter_by(name=request.form['name']).first()
            if existing_disease:
                flash(f'Disease "{request.form["name"]}" already exists!', 'error')
                session.close()
                return render_template('add_disease.html')
            
            disease = Disease(
                name=request.form['name'],
                description=request.form.get('description', '')
            )
            
            session.add(disease)
            
            # Add module information if provided
            if request.form.get('developed_by'):
                module = Module(
                    disease=disease,
                    developed_by=request.form['developed_by'],
                    module_description=request.form.get('module_description', '')
                )
                session.add(module)
            
            # Store the disease name before closing the session
            disease_name = disease.name
            
            session.commit()
            session.close()
            
            flash(f'Disease "{disease_name}" added successfully!', 'success')
            return redirect(url_for('list_diseases'))
        except Exception as e:
            session.rollback()
            session.close()
            flash(f'Error adding disease: {str(e)}', 'error')
            return render_template('add_disease.html')
    
    return render_template('add_disease.html')


@app.route('/disease/<int:disease_id>')
def view_disease(disease_id):
    """View a specific disease and its practices organized by module then segment"""
    session = get_db_session()
    
    try:
        disease = session.query(Disease).get(disease_id)
        
        if not disease:
            flash('Disease not found', 'error')
            return redirect(url_for('list_diseases'))
        
        # Get all modules for this disease
        modules = session.query(Module).filter_by(disease_id=disease_id).all()
        
        # Organize practices by module, then by segment
        # Structure: {module_id: {module_obj, practices_by_segment: {segment: [practices]}}}
        practices_by_module = {}
        
        for module in modules:
            practices_by_module[module.id] = {
                'module': module,
                'practices_by_segment': {}
            }
            # Force load practices relationship
            if module.practices:
                # Get practices for this module
                for practice in module.practices:
                    segment = practice.practice_segment
                    if segment not in practices_by_module[module.id]['practices_by_segment']:
                        practices_by_module[module.id]['practices_by_segment'][segment] = []
                    practices_by_module[module.id]['practices_by_segment'][segment].append(practice)
            # Force load citation
            if practice.citation:
                _ = practice.citation.citation_text
        
        # Get contraindications for this disease
        contraindications = disease.contraindications
        
        return render_template('view_disease.html',
                             disease=disease,
                             modules=modules,
                             practices_by_module=practices_by_module,
                             contraindications=contraindications)
    finally:
        session.close()


@app.route('/disease/<int:disease_id>/edit', methods=['GET', 'POST'])
def edit_disease(disease_id):
    """Edit an existing disease"""
    session = get_db_session()
    
    try:
        disease = session.query(Disease).get(disease_id)
        
        if not disease:
            flash('Disease not found', 'error')
            return redirect(url_for('list_diseases'))
        
        module = session.query(Module).filter_by(disease_id=disease_id).first()
        
        if request.method == 'POST':
            disease.name = request.form['name']
            disease.description = request.form.get('description', '')
            
            # Update module information
            if request.form.get('developed_by'):
                if module:
                    module.developed_by = request.form['developed_by']
                    module.module_description = request.form.get('module_description', '')
                else:
                    # Create new module
                    module = Module(
                        disease_id=disease.id,
                        developed_by=request.form['developed_by'],
                        module_description=request.form.get('module_description', '')
                    )
                    session.add(module)
            # Store name before commit
            disease_name = disease.name
            session.commit()
            session.close()
            
            flash(f'Disease "{disease_name}" updated successfully!', 'success')
            return redirect(url_for('view_disease', disease_id=disease_id))
        
        return render_template('edit_disease.html', disease=disease, module=module)
    finally:
        session.close()


@app.route('/disease/<int:disease_id>/delete', methods=['POST'])
def delete_disease(disease_id):
    """Delete a disease"""
    session = get_db_session()
    
    try:
        disease = session.query(Disease).get(disease_id)
        
        if not disease:
            flash('Disease not found', 'error')
            return redirect(url_for('list_diseases'))
        
        disease_name = disease.name
        
        # Delete all modules associated with this disease FIRST
        # This is critical because modules.disease_id is NOT NULL
        # and SQLAlchemy will try to set it to NULL when deleting the disease
        modules = session.query(Module).filter_by(disease_id=disease_id).all()
        for module in modules:
            # Practices will be deleted via cascade (delete-orphan)
            session.delete(module)
        
        # Clear many-to-many associations
        # These are handled automatically when deleting the disease,
        # but we clear them explicitly to prevent autoflush issues
        disease.practices = []
        disease.contraindications = []
        
        # Clear RCT associations if they exist
        if hasattr(disease, 'rcts'):
            disease.rcts = []
        
        # Now delete the disease itself
        session.delete(disease)
        
        session.commit()
        session.close()
        
        flash(f'Disease "{disease_name}" deleted successfully!', 'success')
        return redirect(url_for('list_diseases'))
    except Exception as e:
        session.rollback()
        session.close()
        flash(f'Error deleting disease: {str(e)}', 'error')
        return redirect(url_for('list_diseases'))


@app.route('/practices')
def list_practices():
    """List all practices, grouped by all fields except module, with pagination"""
    session = get_db_session()
    
    try:
        # Get filter parameters
        segment_filter = request.args.get('segment', '')
        search_term = request.args.get('search', '')
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        per_page = min(per_page, 100)  # Cap at 100 per page
        
        # Use eager loading to prevent N+1 queries
        query = session.query(Practice).options(
            selectinload(Practice.diseases),
            joinedload(Practice.module).joinedload(Module.disease),
            joinedload(Practice.citation)
        )
        
        if segment_filter:
            query = query.filter(Practice.practice_segment == segment_filter)
        
        if search_term:
            query = query.filter(
                (Practice.practice_english.ilike(f'%{search_term}%')) |
                (Practice.practice_sanskrit.ilike(f'%{search_term}%'))
            )
        
        # Paginate before grouping (more efficient)
        pagination = paginate_query(query, page, per_page)
        
        practices = pagination.items
        
        # Group practices by CODE - practices with same code should be shown as one row
        grouped_practices = {}
        for practice in practices:
            # Use code as the grouping key - if no code, use Sanskrit name as fallback
            if practice.code:
                key = practice.code
            elif practice.practice_sanskrit:
                key = f"NO_CODE_{practice.practice_sanskrit}"
            else:
                key = f"NO_CODE_{practice.practice_english}"
            
            if key not in grouped_practices:
                grouped_practices[key] = {
                    'practice': practice,  # Use first practice as representative
                    'modules': [],  # List of (module_id, developed_by) tuples
                    'practice_ids': [],  # All practice IDs in this group
                    'diseases': set()  # Disease names aggregated across modules
                }
            
            # Add module information if it exists
            if practice.module and practice.module.developed_by:
                module_info = (practice.module.id, practice.module.developed_by)
                if module_info not in grouped_practices[key]['modules']:
                    grouped_practices[key]['modules'].append(module_info)

            # Collect all diseases from all practices with this code
            if practice.diseases:
                for disease in practice.diseases:
                    grouped_practices[key]['diseases'].add(disease.name)
            
            # Also get diseases from the module if practice is linked to a module
            if practice.module and practice.module.disease:
                grouped_practices[key]['diseases'].add(practice.module.disease.name)
            
            # Track all practice IDs in this group
            if practice.id not in grouped_practices[key]['practice_ids']:
                grouped_practices[key]['practice_ids'].append(practice.id)
        
        # Convert to list for template
        grouped_list = []
        for data in grouped_practices.values():
            data['diseases'] = sorted(data['diseases'])
            grouped_list.append(data)
        
        # Get all unique segments for filter dropdown
        all_segments = session.query(Practice.practice_segment).distinct().all()
        segments = [s[0] for s in all_segments]
        
        return render_template('practices.html',
                             practices=grouped_list,
                             pagination=pagination,
                             segments=segments,
                             current_segment=segment_filter,
                             search_term=search_term)
    finally:
        session.close()


@app.route('/practice/add', methods=['GET', 'POST'])
def add_practice():
    """Add a new practice"""
    session = get_db_session()
    
    if request.method == 'POST':
        # Handle practice code
        practice_sanskrit = request.form.get('practice_sanskrit', '').strip()
        user_provided_code = request.form.get('code', '').strip()
        
        # DATA INTEGRITY RULE 1: Same Sanskrit name MUST have same code
        # Check if a practice with the same Sanskrit name exists
        existing_practice_with_sanskrit = None
        if practice_sanskrit:
            existing_practice_with_sanskrit = session.query(Practice).filter(
                Practice.practice_sanskrit.ilike(practice_sanskrit)
            ).first()
        
        # DATA INTEGRITY RULE 2: Same code MUST have same Sanskrit name
        # Check if user-provided code already exists
        existing_practice_with_code = None
        if user_provided_code:
            existing_practice_with_code = session.query(Practice).filter(
                Practice.code == user_provided_code
            ).first()
        
        # Determine the code to use (enforcing data integrity)
        practice_code = None
        
        # PRIORITY 1: If Sanskrit name exists, MUST use its code (ignore user code if different)
        if existing_practice_with_sanskrit and existing_practice_with_sanskrit.code:
            practice_code = existing_practice_with_sanskrit.code
            # If user provided a different code, warn but use the correct one
            if user_provided_code and user_provided_code != practice_code:
                flash(f'Warning: Practice with Sanskrit name "{practice_sanskrit}" already exists with code "{practice_code}". Using existing code for consistency.', 'warning')
        # PRIORITY 2: If user provided a code that exists, MUST match Sanskrit name
        elif user_provided_code and existing_practice_with_code:
            existing_sanskrit = (existing_practice_with_code.practice_sanskrit or '').strip()
            if practice_sanskrit and practice_sanskrit.lower() != existing_sanskrit.lower():
                flash(f'Error: Code "{user_provided_code}" already exists for practice "{existing_sanskrit}". Practices with the same code must have the same Sanskrit name.', 'error')
                session.close()
                return render_template('add_practice.html')
            practice_code = user_provided_code
        # PRIORITY 3: User provided a new code (doesn't exist yet)
        elif user_provided_code:
            practice_code = user_provided_code
        # PRIORITY 4: Generate new code based on Sanskrit name
        elif practice_sanskrit:
            practice_code = generate_practice_code(practice_sanskrit, session)
        # PRIORITY 5: Fallback to English name if no Sanskrit name
        elif request.form['practice_english']:
            practice_code = generate_practice_code(request.form['practice_english'], session)
        
        # Require a unique, non-empty code
        if not practice_code:
            flash('Error: A unique practice code is required for every practice.', 'error')
            session.close()
            return render_template('add_practice.html')
        existing_code_conflict = session.query(Practice).filter(Practice.code == practice_code).first()
        if existing_code_conflict:
            flash(f'Error: Practice code "{practice_code}" already exists. Please reuse or choose another code.', 'error')
            session.close()
            return render_template('add_practice.html')
        
        # Create practice
        try:
            _ensure_category_and_kosha(request.form['practice_segment'], request.form.get('kosha', ''))
        except ValueError as ve:
            flash(str(ve), 'error')
            session.close()
            return render_template('add_practice.html')
        
        practice = Practice(
            practice_sanskrit=practice_sanskrit,
            practice_english=request.form['practice_english'],
            practice_segment=request.form['practice_segment'],
            sub_category=request.form.get('sub_category', ''),
            kosha=request.form.get('kosha', ''),
            rounds=int(request.form['rounds']) if request.form.get('rounds') else None,
            time_minutes=float(request.form['time_minutes']) if request.form.get('time_minutes') else None,
            description=request.form.get('description', ''),
            how_to_do=request.form.get('how_to_do', ''),
            code=practice_code
        )
        
        # Add optional fields
        if request.form.get('strokes_per_min'):
            practice.strokes_per_min = int(request.form['strokes_per_min'])
        
        if request.form.get('strokes_per_cycle'):
            practice.strokes_per_cycle = int(request.form['strokes_per_cycle'])
        
        if request.form.get('rest_between_cycles_sec'):
            practice.rest_between_cycles_sec = int(request.form['rest_between_cycles_sec'])
        
        # Handle variations (dynamic fields with referred_in)
        variations = []
        variation_keys = [key for key in request.form.keys() if key.startswith('variation_')]
        for i in range(1, len(variation_keys) + 1):
            variation_text = request.form.get(f'variation_{i}', '').strip()
            variation_ref = request.form.get(f'variation_ref_{i}', '').strip()
            if variation_text:
                variations.append({
                    'text': variation_text,
                    'referred_in': variation_ref
                })
        
        if variations:
            practice.variations = json.dumps(variations)
        
        session.add(practice)
        session.flush()  # Flush to get the ID
        
        # Handle file uploads after we have the ID
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and photo.filename:
                if not allowed_file(photo.filename):
                    session.rollback()
                    flash('Unsupported photo file type. Allowed: png, jpg, jpeg, gif.', 'error')
                    session.close()
                    return render_template('add_practice.html')
                if not allowed_mimetype(photo):
                    session.rollback()
                    flash('Invalid photo MIME type.', 'error')
                    session.close()
                    return render_template('add_practice.html')
                filename = secure_filename(photo.filename)
                photo_path = os.path.join(UPLOAD_FOLDER, 'photos', f'{practice.id}_{filename}')
                photo.save(photo_path)
                practice.photo_path = f'/static/uploads/photos/{practice.id}_{filename}'
        
        if 'video' in request.files:
            video = request.files['video']
            if video and video.filename:
                if not allowed_file(video.filename):
                    session.rollback()
                    flash('Unsupported video file type. Allowed: mp4, avi, mov, wmv.', 'error')
                    session.close()
                    return render_template('add_practice.html')
                if not allowed_mimetype(video):
                    session.rollback()
                    flash('Invalid video MIME type.', 'error')
                    session.close()
                    return render_template('add_practice.html')
                filename = secure_filename(video.filename)
                video_path = os.path.join(UPLOAD_FOLDER, 'videos', f'{practice.id}_{filename}')
                video.save(video_path)
                practice.video_path = f'/static/uploads/videos/{practice.id}_{filename}'
        
        session.commit()
        
        flash(f'Practice "{practice.practice_english}" added successfully!', 'success')
        session.close()
        return redirect(url_for('list_practices'))
    
    # GET request - show form
    session.close()
    return render_template('add_practice.html')


@app.route('/practice/<int:practice_id>/edit', methods=['GET', 'POST'])
def edit_practice(practice_id):
    """Edit an existing practice"""
    session = get_db_session()
    
    try:
        practice = session.query(Practice).get(practice_id)
        
        if not practice:
            flash('Practice not found', 'error')
            return redirect(url_for('list_practices'))
        
        if request.method == 'POST':
            # Store old Sanskrit name for comparison
            old_sanskrit = (practice.practice_sanskrit or '').strip()
            new_sanskrit = request.form.get('practice_sanskrit', '').strip()
            
            # Validate enums
            try:
                _ensure_category_and_kosha(request.form['practice_segment'], request.form.get('kosha', ''))
            except ValueError as ve:
                flash(str(ve), 'error')
                session.close()
                return render_template('edit_practice.html', practice=practice)
            
            # Update practice fields
            practice.practice_sanskrit = new_sanskrit
            practice.practice_english = request.form['practice_english']
            practice.practice_segment = request.form['practice_segment']
            practice.sub_category = request.form.get('sub_category', '')
            practice.kosha = request.form.get('kosha', '')
            practice.rounds = int(request.form['rounds']) if request.form.get('rounds') else None
            practice.time_minutes = float(request.form['time_minutes']) if request.form.get('time_minutes') else None
            practice.how_to_do = request.form.get('how_to_do', '')
            practice.description = request.form.get('description', '')
            
            # Handle practice code - ENFORCE DATA INTEGRITY RULES
            user_provided_code = request.form.get('code', '').strip()
            
            # RULE 1: If Sanskrit name changed to one that exists, MUST use that code
            # RULE 2: If code changed to one that exists, Sanskrit name MUST match
            new_code = None
            
            # Check if new Sanskrit name already exists (DATA INTEGRITY RULE 1)
            existing_practice_with_new_sanskrit = None
            if new_sanskrit and old_sanskrit.lower() != new_sanskrit.lower():
                existing_practice_with_new_sanskrit = session.query(Practice).filter(
                    Practice.practice_sanskrit.ilike(new_sanskrit),
                    Practice.id != practice_id
                ).first()
            
            # Check if user-provided code already exists (DATA INTEGRITY RULE 2)
            existing_practice_with_code = None
            if user_provided_code:
                existing_practice_with_code = session.query(Practice).filter(
                    Practice.code == user_provided_code,
                    Practice.id != practice_id
                ).first()
            
            # Determine new code based on data integrity rules
            if existing_practice_with_new_sanskrit and existing_practice_with_new_sanskrit.code:
                # PRIORITY 1: Sanskrit name exists → MUST use its code (ignore user code if different)
                new_code = existing_practice_with_new_sanskrit.code
                if user_provided_code and user_provided_code != new_code:
                    flash(f'Warning: Practice with Sanskrit name "{new_sanskrit}" already exists with code "{new_code}". Using existing code for consistency.', 'warning')
            elif user_provided_code and existing_practice_with_code:
                # PRIORITY 2: User provided code that exists → Sanskrit name MUST match
                existing_sanskrit = (existing_practice_with_code.practice_sanskrit or '').strip()
                if new_sanskrit and new_sanskrit.lower() != existing_sanskrit.lower():
                    flash(f'Error: Code "{user_provided_code}" already exists for practice "{existing_sanskrit}". Practices with the same code must have the same Sanskrit name.', 'error')
                    session.close()
                    return render_template('edit_practice.html', practice=practice)
                new_code = user_provided_code
            elif user_provided_code:
                # PRIORITY 3: User provided a new code (doesn't exist yet)
                new_code = user_provided_code
            elif new_sanskrit and old_sanskrit.lower() != new_sanskrit.lower():
                # PRIORITY 4: Sanskrit name changed, generate new code
                new_code = generate_practice_code(new_sanskrit, session)
            
            # Update code for all practices with the same Sanskrit name (RULE 1: Same name = Same code)
            if new_code:
                if old_sanskrit and old_sanskrit.lower() != new_sanskrit.lower():
                    # Sanskrit name changed - update all practices with OLD Sanskrit name to new code
                    practices_with_old_sanskrit = session.query(Practice).filter(
                        Practice.practice_sanskrit.ilike(old_sanskrit)
                    ).all()
                    for p in practices_with_old_sanskrit:
                        p.code = new_code
                elif new_sanskrit:
                    # Sanskrit name unchanged but code may have changed - update all practices with same Sanskrit name
                    practices_with_same_sanskrit = session.query(Practice).filter(
                        Practice.practice_sanskrit.ilike(new_sanskrit)
                    ).all()
                    for p in practices_with_same_sanskrit:
                        p.code = new_code
                
                practice.code = new_code
            elif not practice.code and new_sanskrit:
                # No code yet and we have Sanskrit name - find or generate code
                existing_practice_with_sanskrit = session.query(Practice).filter(
                    Practice.practice_sanskrit.ilike(new_sanskrit),
                    Practice.code.isnot(None),
                    Practice.id != practice_id
                ).first()
                
                if existing_practice_with_sanskrit and existing_practice_with_sanskrit.code:
                    practice.code = existing_practice_with_sanskrit.code
                    # Update all practices with same Sanskrit name
                    practices_with_same_sanskrit = session.query(Practice).filter(
                        Practice.practice_sanskrit.ilike(new_sanskrit)
                    ).all()
                    for p in practices_with_same_sanskrit:
                        p.code = practice.code
                else:
                    practice.code = generate_practice_code(new_sanskrit, session)
            elif not practice.code and new_sanskrit:
                # No code set and we have a Sanskrit name - generate one
                existing_practice_with_sanskrit = session.query(Practice).filter(
                    Practice.practice_sanskrit.ilike(new_sanskrit),
                    Practice.id != practice_id
                ).first()
                
                if existing_practice_with_sanskrit and existing_practice_with_sanskrit.code:
                    practice.code = existing_practice_with_sanskrit.code
                else:
                    practice.code = generate_practice_code(new_sanskrit, session)
            
            # Final code validation
            final_code = practice.code
            if not final_code:
                flash('Error: A unique practice code is required for every practice.', 'error')
                session.close()
                return render_template('edit_practice.html', practice=practice)
            conflict = session.query(Practice).filter(
                Practice.code == final_code,
                Practice.id != practice_id
            ).first()
            if conflict:
                flash(f'Error: Practice code "{final_code}" already exists. Please choose another code.', 'error')
                session.close()
                return render_template('edit_practice.html', practice=practice)
            
            # Handle optional fields
            if request.form.get('strokes_per_min'):
                practice.strokes_per_min = int(request.form['strokes_per_min'])
            
            if request.form.get('strokes_per_cycle'):
                practice.strokes_per_cycle = int(request.form['strokes_per_cycle'])
            
            if request.form.get('rest_between_cycles_sec'):
                practice.rest_between_cycles_sec = int(request.form['rest_between_cycles_sec'])
            
            if 'cvr_score' in request.form:
                cvr_score_value = request.form.get('cvr_score')
                try:
                    practice.cvr_score = float(cvr_score_value) if cvr_score_value else None
                except (TypeError, ValueError):
                    practice.cvr_score = None
            
            # Handle variations (dynamic fields)
            variations = []
            variation_keys = [key for key in request.form.keys() if key.startswith('variation_')]
            for i in range(1, len(variation_keys) + 1):
                variation_text = request.form.get(f'variation_{i}', '').strip()
                variation_ref = request.form.get(f'variation_ref_{i}', '').strip()
                if variation_text:
                    variations.append({
                        'text': variation_text,
                        'referred_in': variation_ref
                    })
            
            if variations:
                practice.variations = json.dumps(variations)
            
            # Handle file uploads
            if 'photo' in request.files:
                photo = request.files['photo']
                if photo and photo.filename:
                    if not allowed_file(photo.filename):
                        session.rollback()
                        flash('Unsupported photo file type. Allowed: png, jpg, jpeg, gif.', 'error')
                        session.close()
                        return render_template('edit_practice.html', practice=practice)
                    if not allowed_mimetype(photo):
                        session.rollback()
                        flash('Invalid photo MIME type.', 'error')
                        session.close()
                        return render_template('edit_practice.html', practice=practice)
                    filename = secure_filename(photo.filename)
                    photo_path = os.path.join(UPLOAD_FOLDER, 'photos', f'{practice.id}_{filename}')
                    photo.save(photo_path)
                    practice.photo_path = f'/static/uploads/photos/{practice.id}_{filename}'
            
            if 'video' in request.files:
                video = request.files['video']
                if video and video.filename:
                    if not allowed_file(video.filename):
                        session.rollback()
                        flash('Unsupported video file type. Allowed: mp4, avi, mov, wmv.', 'error')
                        session.close()
                        return render_template('edit_practice.html', practice=practice)
                    if not allowed_mimetype(video):
                        session.rollback()
                        flash('Invalid video MIME type.', 'error')
                        session.close()
                        return render_template('edit_practice.html', practice=practice)
                    filename = secure_filename(video.filename)
                    video_path = os.path.join(UPLOAD_FOLDER, 'videos', f'{practice.id}_{filename}')
                    video.save(video_path)
                    practice.video_path = f'/static/uploads/videos/{practice.id}_{filename}'
            
            # Store old category and disease associations for comparison
            old_category = practice.practice_segment
            old_disease_ids = set([d.id for d in practice.diseases])
            
            # Find all practices with the SAME CODE - these should all be synced
            # Get the code (either from current practice or from form)
            current_code = practice.code or user_provided_code
            if not current_code and new_sanskrit:
                # If no code yet, check if other practices with same Sanskrit have a code
                existing_with_code = session.query(Practice).filter(
                    Practice.practice_sanskrit.ilike(new_sanskrit),
                    Practice.code.isnot(None),
                    Practice.id != practice_id
                ).first()
                if existing_with_code:
                    current_code = existing_with_code.code
            
            # Find all practices with the same CODE (excluding CVR score which is module-specific)
            related_practices = []
            if current_code:
                related_practices = session.query(Practice).filter(
                    Practice.code == current_code,
                    Practice.id != practice_id
                ).all()
            
            # Also update the code for all related practices if it changed
            if current_code and practice.code != current_code:
                practice.code = current_code
                for p in related_practices:
                    p.code = current_code
            
            # Update all related practices with new field values (EXCEPT CVR score - it's module-specific)
            for p in related_practices:
                p.practice_sanskrit = practice.practice_sanskrit
                p.practice_english = practice.practice_english
                p.practice_segment = practice.practice_segment
                p.sub_category = practice.sub_category
                p.kosha = practice.kosha
                p.rounds = practice.rounds
                p.time_minutes = practice.time_minutes
                p.strokes_per_min = practice.strokes_per_min
                p.strokes_per_cycle = practice.strokes_per_cycle
                p.rest_between_cycles_sec = practice.rest_between_cycles_sec
                p.variations = practice.variations
                p.steps = practice.steps
                p.description = practice.description
                p.how_to_do = practice.how_to_do
                p.photo_path = practice.photo_path
                p.video_path = practice.video_path
                p.citation_id = practice.citation_id
                p.rct_count = practice.rct_count
                # DO NOT sync CVR score - it's module-specific and should remain different for each module
                # p.cvr_score = practice.cvr_score
            
            # Check if this is a module-specific edit (has module_id in form) or a general edit from practices tab
            # Only do module/disease management if form has disease/module data
            disease_ids = request.form.getlist('diseases')
            
            if disease_ids:
                # This is a module-specific edit - handle module associations
                # Collect all module IDs for each disease
                modules_by_disease = {}
                for disease_id in disease_ids:
                    disease_id_int = int(disease_id)
                    # Get all module IDs for this disease (format: module_id_diseaseId_index)
                    module_keys = [key for key in request.form.keys() 
                                  if key.startswith(f'module_id_{disease_id_int}_')]
                    modules_for_disease = []
                    for key in module_keys:
                        module_id = request.form.get(key)
                        if module_id:
                            modules_for_disease.append(int(module_id))
                    modules_by_disease[disease_id_int] = modules_for_disease
                
                # Update disease associations for all related practices
                for p in related_practices:
                    p.diseases = []
                for disease_id in disease_ids:
                    disease = session.query(Disease).get(int(disease_id))
                    if disease:
                        for p in related_practices:
                            if disease not in p.diseases:
                                p.diseases.append(disease)
                
                # Create/update/delete practice entries based on modules
                # First, delete practices that don't have a module in the new list
                practices_to_delete = []
                for p in related_practices:
                    if p.module:
                        module_found = False
                        for disease_id, module_ids in modules_by_disease.items():
                            if p.module.id in module_ids and p.module.disease_id == disease_id:
                                module_found = True
                                break
                        if not module_found:
                            practices_to_delete.append(p)
                
                for p in practices_to_delete:
                    session.delete(p)
                    related_practices.remove(p)
                
                # Create new practice entries for modules that don't have a practice yet
                for disease_id, module_ids in modules_by_disease.items():
                    disease = session.query(Disease).get(disease_id)
                    if not disease:
                        continue
                    
                    for module_id in module_ids:
                        module = session.query(Module).get(module_id)
                        if not module or module.disease_id != disease_id:
                            continue
                        
                        # Check if a practice with this module already exists
                        practice_exists = False
                        for p in related_practices:
                            if p.module and p.module.id == module_id:
                                practice_exists = True
                                break
                        
                        if not practice_exists:
                            # Use the same code as the original practice, or generate one
                            practice_code = practice.code
                            if not practice_code and practice.practice_sanskrit:
                                practice_code = generate_practice_code(practice.practice_sanskrit, session)
                            elif not practice_code:
                                practice_code = generate_practice_code(practice.practice_english, session)
                            
                            # Create new practice entry
                            new_practice = Practice(
                                practice_sanskrit=practice.practice_sanskrit,
                                practice_english=practice.practice_english,
                                practice_segment=practice.practice_segment,
                                sub_category=practice.sub_category,
                                kosha=practice.kosha,
                                rounds=practice.rounds,
                                time_minutes=practice.time_minutes,
                                strokes_per_min=practice.strokes_per_min,
                                strokes_per_cycle=practice.strokes_per_cycle,
                                rest_between_cycles_sec=practice.rest_between_cycles_sec,
                                variations=practice.variations,
                                steps=practice.steps,
                                description=practice.description,
                                how_to_do=practice.how_to_do,
                                photo_path=practice.photo_path,
                                video_path=practice.video_path,
                                citation_id=practice.citation_id,
                                cvr_score=practice.cvr_score,
                                code=practice_code,
                                module_id=module_id,
                                rct_count=practice.rct_count
                            )
                            new_practice.diseases.append(disease)
                            session.add(new_practice)
                
                # Update module_id for existing practices
                for p in related_practices:
                    if p.module:
                        # Find the module for this practice's disease
                        for disease_id, module_ids in modules_by_disease.items():
                            if p.module.disease_id == disease_id and p.module.id in module_ids:
                                # Keep the same module
                                break
                        else:
                            # Assign first module for first disease if no match
                            if modules_by_disease:
                                first_disease_id = list(modules_by_disease.keys())[0]
                                first_module_id = modules_by_disease[first_disease_id][0] if modules_by_disease[first_disease_id] else None
                                if first_module_id:
                                    p.module_id = first_module_id
                
                new_disease_ids = set([int(d) for d in disease_ids])
                
                # Recalculate RCT count if category or diseases changed
                if old_category != practice.practice_segment or old_disease_ids != new_disease_ids:
                    for p in related_practices:
                        recalculate_practice_rct_count(session, p)
            else:
                # This is a general edit from practices tab - just sync fields, don't touch modules/diseases
                # Keep all existing practices and their module associations intact
                pass
            
            # Store the practice name before closing session
            practice_name = practice.practice_english
            
            session.commit()
            session.close()
            
            flash(f'Practice "{practice_name}" updated successfully!', 'success')
            return redirect(url_for('list_practices'))
        
        # GET request - find all practices that are identical (except module)
        # Create a key based on all fields except module_id
        practice_key = (
            practice.practice_sanskrit or '',
            practice.practice_english,
            practice.practice_segment,
            practice.sub_category or '',
            practice.kosha or '',
            practice.rounds,
            practice.time_minutes,
            practice.strokes_per_min,
            practice.strokes_per_cycle,
            practice.rest_between_cycles_sec,
            practice.variations or '',
            practice.steps or '',
            practice.description or '',
            practice.how_to_do or '',
            practice.photo_path or '',
            practice.video_path or '',
            practice.citation_id,
            tuple(sorted([d.id for d in practice.diseases])),
            practice.cvr_score,
            practice.rct_count or 0
        )
        
        # Find all practices with the same key
        all_practices = session.query(Practice).all()
        related_practices = []
        for p in all_practices:
            p_key = (
                p.practice_sanskrit or '',
                p.practice_english,
                p.practice_segment,
                p.sub_category or '',
                p.kosha or '',
                p.rounds,
                p.time_minutes,
                p.strokes_per_min,
                p.strokes_per_cycle,
                p.rest_between_cycles_sec,
                p.variations or '',
                p.steps or '',
                p.description or '',
                p.how_to_do or '',
                p.photo_path or '',
                p.video_path or '',
                p.citation_id,
                tuple(sorted([d.id for d in p.diseases])),
                p.cvr_score,
                p.rct_count or 0
            )
            if p_key == practice_key:
                related_practices.append(p)
                # Force load module
                if p.module:
                    _ = p.module.id
                    _ = p.module.developed_by
                    _ = p.module.disease_id
        
        # Group modules by disease
        modules_by_disease = {}
        for p in related_practices:
            for disease in p.diseases:
                if disease.id not in modules_by_disease:
                    modules_by_disease[disease.id] = []
                if p.module and p.module.disease_id == disease.id:
                    module_info = (p.module.id, p.module.developed_by, p.id)
                    if module_info not in modules_by_disease[disease.id]:
                        modules_by_disease[disease.id].append(module_info)
        
        diseases = session.query(Disease).all()
        return render_template('edit_practice.html', 
                             practice=practice, 
                             diseases=diseases,
                             modules_by_disease=modules_by_disease,
                             related_practices=related_practices)
    finally:
        session.close()


@app.route('/practice/<int:practice_id>/delete', methods=['POST'])
def delete_practice(practice_id):
    """Delete a practice"""
    session = get_db_session()
    
    try:
        practice = session.query(Practice).get(practice_id)
        
        if not practice:
            flash('Practice not found', 'error')
            return redirect(url_for('list_practices'))
        
        practice_english = practice.practice_english
        session.delete(practice)
        session.commit()
        session.close()
        
        flash(f'Practice "{practice_english}" deleted successfully!', 'success')
        return redirect(url_for('list_practices'))
    except Exception as e:
        session.close()
        flash(f'Error deleting practice: {str(e)}', 'error')
        return redirect(url_for('list_practices'))


@app.route('/practice/<int:practice_id>')
def view_practice(practice_id):
    """View practice details"""
    session = get_db_session()
    
    try:
        practice = session.query(Practice).get(practice_id)
        
        if not practice:
            flash('Practice not found', 'error')
            return redirect(url_for('list_practices'))
        
        # Force load relationships
        _ = practice.diseases
        _ = practice.citation
        
        return render_template('view_practice.html', practice=practice)
    finally:
        session.close()


@app.route('/contraindications')
def list_contraindications():
    """List all contraindications grouped by disease with pagination"""
    session = get_db_session()
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        per_page = min(per_page, 100)  # Cap at 100 per page
        
        # Use eager loading
        query = session.query(Disease).options(
            selectinload(Disease.contraindications)
        )
        
        # Paginate diseases
        pagination = paginate_query(query, page, per_page)
        
        diseases = pagination.items
        disease_contraindications = {}
        
        for disease in diseases:
            if disease.contraindications:
                disease_contraindications[disease] = disease.contraindications
        
        return render_template('contraindications.html', 
                             disease_contraindications=disease_contraindications,
                             pagination=pagination)
    finally:
        session.close()


@app.route('/contraindication/add', methods=['GET', 'POST'])
def add_contraindication():
    """Add a new contraindication for a disease"""
    session = get_db_session()
    
    try:
        if request.method == 'POST':
            disease_id = request.form.get('disease_id')
            practice_id = request.form.get('practice_id')
            reason_html = request.form.get('reason', '')
            reference_full_html = request.form.get('reference_full', '')

            if not disease_id:
                flash('Please select a disease before adding a contraindication.', 'error')
                return redirect(url_for('add_contraindication'))

            disease = session.query(Disease).get(int(disease_id))
            if not disease:
                flash('Selected disease could not be found.', 'error')
                return redirect(url_for('add_contraindication'))

            if not practice_id:
                flash('Please select a practice to add as a contraindication.', 'error')
                return redirect(url_for('add_contraindication', disease_id=disease.id))

            practice = session.query(Practice).get(int(practice_id))
            if not practice:
                flash('Selected practice could not be found.', 'error')
                return redirect(url_for('add_contraindication', disease_id=disease.id))

            practice_sanskrit_input = (request.form.get('practice_sanskrit') or '').strip()
            practice_english_input = (request.form.get('practice_english') or '').strip()
            practice_segment_input = (request.form.get('practice_segment') or '').strip()
            sub_category_input = (request.form.get('sub_category') or '').strip()

            practice_sanskrit_value = practice_sanskrit_input or (practice.practice_sanskrit or '')
            practice_english_value = practice_english_input or practice.practice_english
            practice_segment_value = practice_segment_input or practice.practice_segment
            sub_category_value = sub_category_input or (practice.sub_category or '')

            if not practice_english_value:
                flash('Practice English name is required.', 'error')
                return redirect(url_for('add_contraindication', disease_id=disease.id))

            contraindication = Contraindication(
                practice_sanskrit=practice_sanskrit_value,
                practice_english=practice_english_value,
                practice_segment=practice_segment_value,
                sub_category=sub_category_value,
                reason=reason_html,
                source_type=request.form.get('parenthetical_citation', ''),
                source_name=request.form.get('reference_link', ''),
                page_number='',
                apa_citation=reference_full_html
            )

            session.add(contraindication)
            contraindication.diseases.append(disease)
            session.commit()

            flash('Contraindication added successfully!', 'success')

            if request.form.get('add_another') == 'yes':
                return redirect(url_for('add_contraindication', disease_id=disease.id))

            return redirect(url_for('list_contraindications'))

        # GET request
        disease_id = request.args.get('disease_id', type=int)
        selected_disease = None
        existing_contras = []

        practice_segments = ALLOWED_CATEGORIES

        if disease_id:
            selected_disease = session.query(Disease).get(disease_id)
            if selected_disease:
                existing_contras = list(selected_disease.contraindications)

        return render_template(
            'add_contraindication.html',
            selected_disease=selected_disease,
            existing_contras=existing_contras,
            practice_segments=practice_segments
        )
    finally:
        session.close()


@app.route('/contraindication/<int:contraindication_id>/edit', methods=['GET', 'POST'])
def edit_contraindication(contraindication_id):
    """Edit an existing contraindication"""
    session = get_db_session()
    
    try:
        contraindication = session.query(Contraindication).get(contraindication_id)
        
        if not contraindication:
            flash('Contraindication not found', 'error')
            return redirect(url_for('list_contraindications'))
        
        if request.method == 'POST':
            contraindication.reason = request.form.get('reason', '')
            contraindication.apa_citation = request.form.get('reference_full', '')
            contraindication.source_type = request.form.get('parenthetical_citation', '')
            contraindication.source_name = request.form.get('reference_link', '')
            
            session.commit()
            flash('Contraindication updated successfully!', 'success')
            return redirect(url_for('list_contraindications'))
        
        selected_disease = contraindication.diseases[0] if contraindication.diseases else None

        return render_template(
            'edit_contraindication.html',
                             contraindication=contraindication, 
            selected_disease=selected_disease
        )
    finally:
        session.close()


@app.route('/contraindication/<int:contraindication_id>/delete', methods=['POST'])
def delete_contraindication(contraindication_id):
    """Delete a contraindication"""
    session = get_db_session()
    
    try:
        contraindication = session.query(Contraindication).get(contraindication_id)
        
        if not contraindication:
            flash('Contraindication not found', 'error')
            return redirect(url_for('list_contraindications'))
        
        practice_name = contraindication.practice_english
        session.delete(contraindication)
        session.commit()
        session.close()
        
        flash(f'Contraindication for "{practice_name}" deleted successfully!', 'success')
        return redirect(url_for('list_contraindications'))
    except Exception as e:
        session.close()
        flash(f'Error deleting contraindication: {str(e)}', 'error')
        return redirect(url_for('list_contraindications'))


@app.route('/citations')
def list_citations():
    """List all citations with pagination and eager loading"""
    session = get_db_session()
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        per_page = min(per_page, 100)  # Cap at 100 per page
        
        # Use eager loading to prevent N+1 queries
        query = session.query(Citation).options(
            selectinload(Citation.practices)
        )
        
        # Paginate results
        pagination = paginate_query(query, page, per_page)
        
        citations = pagination.items
        
        return render_template('citations.html', 
                             citations=citations,
                             pagination=pagination)
    finally:
        session.close()


@app.route('/citation/add', methods=['GET', 'POST'])
def add_citation():
    """Add a new citation"""
    if request.method == 'POST':
        session = get_db_session()
        
        citation = Citation(
            citation_text=request.form['citation_text'],
            citation_type=request.form.get('citation_type', 'research_paper'),
            full_reference=request.form.get('full_reference', ''),
            url=request.form.get('url', '')
        )
        
        session.add(citation)
        session.commit()
        session.close()
        
        flash('Citation added successfully!', 'success')
        return redirect(url_for('list_citations'))
    
    return render_template('add_citation.html')


# ==================== MODULE MANAGEMENT ROUTES ====================

@app.route('/modules')
def list_modules():
    """List all modules with pagination and eager loading"""
    session = get_db_session()
    try:
        # Get filter parameters
        disease_id = request.args.get('disease_id')
        disease_name = request.args.get('disease_name', '').strip()
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        per_page = min(per_page, 100)  # Cap at 100 per page

        # Use eager loading to prevent N+1 queries
        query = session.query(Module).options(
            joinedload(Module.disease)
        ).outerjoin(Disease, Module.disease)

        selected_disease_name = ''
        selected_disease_id = ''

        if disease_id:
            try:
                disease_id_int = int(disease_id)
                query = query.filter(Module.disease_id == disease_id_int)
                disease_obj = session.query(Disease).get(disease_id_int)
                if disease_obj:
                    selected_disease_name = disease_obj.name
                    selected_disease_id = str(disease_id_int)
            except ValueError:
                pass
        elif disease_name:
            query = query.filter(Disease.name.ilike(f'%{disease_name}%'))
            selected_disease_name = disease_name

        query = query.order_by(Disease.name.asc(), Module.developed_by.asc())
        
        # Paginate results
        pagination = paginate_query(query, page, per_page)
        
        modules = pagination.items

        return render_template(
            'modules.html',
            modules=modules,
            pagination=pagination,
            selected_disease_name=selected_disease_name,
            selected_disease_id=selected_disease_id
        )
    finally:
        session.close()


@app.route('/module/add', methods=['GET', 'POST'])
def add_module():
    """Add a new module"""
    session = get_db_session()
    
    if request.method == 'POST':
        try:
            disease_id = request.form.get('disease_id')
            disease_name = request.form.get('disease_name', '').strip()
            
            # If disease_id is provided, use it
            if disease_id:
                disease = session.query(Disease).get(disease_id)
                if not disease:
                    flash('Disease not found', 'error')
                    diseases = session.query(Disease).all()
                    return render_template('add_module.html', diseases=diseases)
            # If disease_name is provided but no disease_id, create new disease
            elif disease_name:
                # Check if disease already exists
                disease = session.query(Disease).filter_by(name=disease_name).first()
                if not disease:
                    # Create new disease
                    disease = Disease(name=disease_name)
                    session.add(disease)
                    session.flush()  # Get the ID
                    flash(f'New disease "{disease_name}" created!', 'success')
                disease_id = disease.id
            else:
                flash('Please select or enter a disease', 'error')
                diseases = session.query(Disease).all()
                return render_template('add_module.html', diseases=diseases)
            
            module = Module(
                disease_id=disease_id,
                developed_by=request.form.get('developed_by', ''),
                paper_link=request.form.get('paper_link', ''),
                module_description=request.form.get('module_description', '')
            )
            
            session.add(module)
            session.commit()
            
            flash(f'Module "{module.developed_by}" added successfully!', 'success')
            return redirect(url_for('view_module', module_id=module.id))
        except Exception as e:
            session.rollback()
            flash(f'Error adding module: {str(e)}', 'error')
            diseases = session.query(Disease).all()
            return render_template('add_module.html', diseases=diseases)
        finally:
            session.close()
    
    try:
        diseases = session.query(Disease).all()
        return render_template('add_module.html', diseases=diseases)
    finally:
        session.close()


@app.route('/module/<int:module_id>')
def view_module(module_id):
    """View a specific module and its practices"""
    session = get_db_session()
    
    try:
        module = session.query(Module).get(module_id)
        
        if not module:
            flash('Module not found', 'error')
            return redirect(url_for('list_modules'))
        
        # Organize practices by kosha -> category
        practices_by_kosha = {}
        kosha_order = [
            'Annamaya Kosha',
            'Pranamaya Kosha',
            'Manomaya Kosha',
            'Vijnanamaya Kosha',
            'Anandamaya Kosha'
        ]
        category_order = [
            'Preparatory practices',
            'Breathing practices',
            'Sequential yogic practices',
            'Yogasana',
            'Pranayama',
            'Meditation',
            'Chanting',
            'Additional practices',
            'Kriya (cleansing)',
            'Yogic counselling',
            'Lifestyle modifications (Anna)',
            'Yogic diet (Anna)',
            'Chair Yoga (Anna)',
            # legacy spellings
            'Preparatory Practice',
            'Breathing Practice',
            'Sequential Yogic Practice',
            'Additional Practices',
            'Kriya (Cleansing Techniques)',
            'Yogic Counselling',
            'Suryanamaskara',
        ]

        if module.practices:
            for practice in module.practices:
                kosha = practice.kosha or 'Unspecified Kosha'
                category = practice.practice_segment or 'Uncategorized'

                if kosha not in practices_by_kosha:
                    practices_by_kosha[kosha] = {}

                if category not in practices_by_kosha[kosha]:
                    practices_by_kosha[kosha][category] = []

                practices_by_kosha[kosha][category].append(practice)

                if practice.citation:
                    _ = practice.citation.citation_text

            # Sort practices within each category alphabetically by Sanskrit (fallback to English)
            for kosha_categories in practices_by_kosha.values():
                for category_name, practice_list in kosha_categories.items():
                    kosha_categories[category_name] = sorted(
                        practice_list,
                        key=lambda p: ((p.practice_sanskrit or p.practice_english or '').lower(), p.practice_english.lower())
                    )

        # Build ordered kosha list (defined order first, then alphabetical remainder)
        ordered_koshas = [k for k in kosha_order if k in practices_by_kosha]
        remaining_koshas = sorted([k for k in practices_by_kosha.keys() if k not in kosha_order])
        ordered_koshas.extend(remaining_koshas)

        return render_template('view_module.html',
                             module=module,
                             practices_by_kosha=practices_by_kosha,
                             ordered_koshas=ordered_koshas,
                             category_order=category_order)
    finally:
        session.close()


@app.route('/module/<int:module_id>/edit', methods=['GET', 'POST'])
def edit_module(module_id):
    """Edit an existing module"""
    session = get_db_session()
    
    try:
        module = session.query(Module).get(module_id)
        
        if not module:
            flash('Module not found', 'error')
            return redirect(url_for('list_modules'))
        
        if request.method == 'POST':
            try:
                module.developed_by = request.form.get('developed_by', '')
                module.paper_link = request.form.get('paper_link', '')
                module.module_description = request.form.get('module_description', '')
                
                session.commit()
                flash('Module updated successfully!', 'success')
                return redirect(url_for('view_module', module_id=module_id))
            except Exception as e:
                session.rollback()
                flash(f'Error updating module: {str(e)}', 'error')
        
        diseases = session.query(Disease).all()
        return render_template('edit_module.html', module=module, diseases=diseases)
    finally:
        session.close()


@app.route('/module/<int:module_id>/delete', methods=['POST'])
def delete_module(module_id):
    """Delete a module"""
    session = get_db_session()
    
    try:
        module = session.query(Module).get(module_id)
        
        if not module:
            flash('Module not found', 'error')
            return redirect(url_for('list_modules'))
        
        module_name = module.developed_by or f"Module {module_id}"
        session.delete(module)
        session.commit()
        
        flash(f'Module "{module_name}" deleted successfully!', 'success')
        return redirect(url_for('list_modules'))
    except Exception as e:
        session.rollback()
        flash(f'Error deleting module: {str(e)}', 'error')
        return redirect(url_for('list_modules'))
    finally:
        session.close()


@app.route('/module/<int:module_id>/practice/add', methods=['GET', 'POST'])
def add_practice_to_module(module_id):
    """Add a practice to a specific module (module-based practice addition)"""
    session = get_db_session()
    
    try:
        module = session.query(Module).get(module_id)
        
        if not module:
            flash('Module not found', 'error')
            return redirect(url_for('list_modules'))
        
        def get_existing_practices_list(mod):
            existing = []
            if mod and mod.practices:
                for practice in mod.practices:
                    existing.append({
                        'id': practice.id,
                        'sanskrit': practice.practice_sanskrit or '',
                        'english': practice.practice_english or ''
                    })
                existing.sort(key=lambda p: (p['sanskrit'] or p['english']).lower())
            return existing

        if request.method == 'POST':
            try:
                cvr_score_value = request.form.get('cvr_score')
                cvr_score = float(cvr_score_value) if cvr_score_value else None

                # Handle practice code
                practice_sanskrit = request.form.get('practice_sanskrit', '').strip()
                user_provided_code = request.form.get('code', '').strip()
                
                # DATA INTEGRITY RULE 1: Same Sanskrit name MUST have same code
                existing_practice_with_sanskrit = None
                if practice_sanskrit:
                    existing_practice_with_sanskrit = session.query(Practice).filter(
                        Practice.practice_sanskrit.ilike(practice_sanskrit)
                    ).first()
                
                # DATA INTEGRITY RULE 2: Same code MUST have same Sanskrit name
                existing_practice_with_code = None
                if user_provided_code:
                    existing_practice_with_code = session.query(Practice).filter(
                        Practice.code == user_provided_code
                    ).first()
                
                # Determine the code to use (enforcing data integrity)
                practice_code = None
                
                # PRIORITY 1: If Sanskrit name exists, MUST use its code (ignore user code if different)
                if existing_practice_with_sanskrit and existing_practice_with_sanskrit.code:
                    practice_code = existing_practice_with_sanskrit.code
                    # If user provided a different code, warn but use the correct one
                    if user_provided_code and user_provided_code != practice_code:
                        flash(f'Warning: Practice with Sanskrit name "{practice_sanskrit}" already exists with code "{practice_code}". Using existing code for consistency.', 'warning')
                # PRIORITY 2: If user provided a code that exists, MUST match Sanskrit name
                elif user_provided_code and existing_practice_with_code:
                    existing_sanskrit = (existing_practice_with_code.practice_sanskrit or '').strip()
                    if practice_sanskrit and practice_sanskrit.lower() != existing_sanskrit.lower():
                        flash(f'Error: Code "{user_provided_code}" already exists for practice "{existing_sanskrit}". Practices with the same code must have the same Sanskrit name.', 'error')
                        session.close()
                        practice_segments = ALLOWED_CATEGORIES
                        existing_practices = get_existing_practices_list(module)
                        return render_template('add_practice_to_module.html', 
                                             module=module, 
                                             practice_segments=practice_segments,
                                             existing_practices=existing_practices)
                    practice_code = user_provided_code
                # PRIORITY 3: User provided a new code (doesn't exist yet)
                elif user_provided_code:
                    practice_code = user_provided_code
                # PRIORITY 4: Generate new code based on Sanskrit name
                elif practice_sanskrit:
                    practice_code = generate_practice_code(practice_sanskrit, session)
                # PRIORITY 5: Fallback to English name if no Sanskrit name
                elif request.form['practice_english']:
                    practice_code = generate_practice_code(request.form['practice_english'], session)
                
                # Create practice
                practice = Practice(
                    practice_sanskrit=practice_sanskrit,
                    practice_english=request.form['practice_english'],
                    practice_segment=request.form['practice_segment'],
                    sub_category=request.form.get('sub_category', ''),
                    kosha=request.form.get('kosha', ''),
                    rounds=int(request.form['rounds']) if request.form.get('rounds') else None,
                    time_minutes=float(request.form['time_minutes']) if request.form.get('time_minutes') else None,
                    strokes_per_min=int(request.form['strokes_per_min']) if request.form.get('strokes_per_min') else None,
                    cvr_score=cvr_score,
                    code=practice_code,
                    module_id=module_id  # Associate with module
                )
                
                # Associate practice with module's disease automatically
                if module.disease:
                    practice.diseases.append(module.disease)
                
                session.add(practice)
                session.commit()
                
                flash(f'Practice "{practice.practice_english}" added to module!', 'success')
                
                # Check if user wants to add another practice
                if request.form.get('add_another') == 'yes':
                    return redirect(url_for('add_practice_to_module', module_id=module_id))
                else:
                    return redirect(url_for('view_module', module_id=module_id))
            except Exception as e:
                session.rollback()
                flash(f'Error adding practice: {str(e)}', 'error')
        
        # Get practice segments for dropdown (now called "Category")
        practice_segments = ALLOWED_CATEGORIES
        
        existing_practices = get_existing_practices_list(module)
        return render_template('add_practice_to_module.html', 
                             module=module, 
                             practice_segments=practice_segments,
                             existing_practices=existing_practices)
    finally:
        session.close()


@app.route('/module/<int:module_id>/practice/<int:practice_id>/edit', methods=['GET', 'POST'])
def edit_practice_in_module(module_id, practice_id):
    """Edit a practice that belongs to a specific module (limited fields)"""
    session = get_db_session()

    try:
        module = session.query(Module).get(module_id)
        practice = session.query(Practice).get(practice_id)

        if not module:
            flash('Module not found', 'error')
            return redirect(url_for('list_modules'))

        if not practice or practice.module_id != module_id:
            flash('Practice not found in this module', 'error')
            return redirect(url_for('view_module', module_id=module_id))

        if request.method == 'POST':
            try:
                # Store old Sanskrit name for comparison
                old_sanskrit = (practice.practice_sanskrit or '').strip()
                new_sanskrit = request.form.get('practice_sanskrit', '').strip()
                
                practice.practice_sanskrit = new_sanskrit
                practice.practice_english = request.form['practice_english']
                practice.practice_segment = request.form['practice_segment']
                practice.sub_category = request.form.get('sub_category', '')
                practice.kosha = request.form.get('kosha', '')
                
                # Handle practice code - ENFORCE DATA INTEGRITY RULES
                user_provided_code = request.form.get('code', '').strip()
                
                # RULE 1: If Sanskrit name changed to one that exists, MUST use its code
                # RULE 2: If code changed to one that exists, Sanskrit name MUST match
                new_code = None
                
                # Check if new Sanskrit name already exists (DATA INTEGRITY RULE 1)
                existing_practice_with_new_sanskrit = None
                if new_sanskrit and old_sanskrit.lower() != new_sanskrit.lower():
                    existing_practice_with_new_sanskrit = session.query(Practice).filter(
                        Practice.practice_sanskrit.ilike(new_sanskrit),
                        Practice.id != practice_id
                    ).first()
                
                # Check if user-provided code already exists (DATA INTEGRITY RULE 2)
                existing_practice_with_code = None
                if user_provided_code:
                    existing_practice_with_code = session.query(Practice).filter(
                        Practice.code == user_provided_code,
                        Practice.id != practice_id
                    ).first()
                
                # Determine new code based on data integrity rules
                if existing_practice_with_new_sanskrit and existing_practice_with_new_sanskrit.code:
                    # PRIORITY 1: Sanskrit name exists → MUST use its code (ignore user code if different)
                    new_code = existing_practice_with_new_sanskrit.code
                    if user_provided_code and user_provided_code != new_code:
                        flash(f'Warning: Practice with Sanskrit name "{new_sanskrit}" already exists with code "{new_code}". Using existing code for consistency.', 'warning')
                elif user_provided_code and existing_practice_with_code:
                    # PRIORITY 2: User provided code that exists → Sanskrit name MUST match
                    existing_sanskrit = (existing_practice_with_code.practice_sanskrit or '').strip()
                    if new_sanskrit and new_sanskrit.lower() != existing_sanskrit.lower():
                        flash(f'Error: Code "{user_provided_code}" already exists for practice "{existing_sanskrit}". Practices with the same code must have the same Sanskrit name.', 'error')
                        session.close()
                        practice_segments = ALLOWED_CATEGORIES
                        return render_template(
                            'edit_practice_in_module.html',
                            module=module,
                            practice=practice,
                            practice_segments=practice_segments
                        )
                    new_code = user_provided_code
                elif user_provided_code:
                    # PRIORITY 3: User provided a new code (doesn't exist yet)
                    new_code = user_provided_code
                elif new_sanskrit and old_sanskrit.lower() != new_sanskrit.lower():
                    # PRIORITY 4: Sanskrit name changed, generate new code
                    new_code = generate_practice_code(new_sanskrit, session)
                
                # Find all practices with the SAME CODE - these should all be synced
                related_practices = []
                
                # Update code for all practices with the same Sanskrit name (RULE 1: Same name = Same code)
                if new_code:
                    if old_sanskrit and old_sanskrit.lower() != new_sanskrit.lower():
                        # Sanskrit name changed - update all practices with OLD Sanskrit name to new code
                        practices_with_old_sanskrit = session.query(Practice).filter(
                            Practice.practice_sanskrit.ilike(old_sanskrit)
                        ).all()
                        for p in practices_with_old_sanskrit:
                            p.code = new_code
                        # Update related practices list with new code
                        related_practices = session.query(Practice).filter(
                            Practice.code == new_code,
                            Practice.id != practice_id
                        ).all()
                    elif new_sanskrit:
                        # Sanskrit name unchanged but code may have changed - update all practices with same Sanskrit name
                        practices_with_same_sanskrit = session.query(Practice).filter(
                            Practice.practice_sanskrit.ilike(new_sanskrit)
                        ).all()
                        for p in practices_with_same_sanskrit:
                            p.code = new_code
                        related_practices = session.query(Practice).filter(
                            Practice.code == new_code,
                            Practice.id != practice_id
                        ).all()
                    
                    practice.code = new_code
                elif not practice.code and new_sanskrit:
                    # No code yet and we have Sanskrit name - find or generate code
                    existing_practice_with_sanskrit = session.query(Practice).filter(
                        Practice.practice_sanskrit.ilike(new_sanskrit),
                        Practice.code.isnot(None),
                        Practice.id != practice_id
                    ).first()
                    
                    if existing_practice_with_sanskrit and existing_practice_with_sanskrit.code:
                        practice.code = existing_practice_with_sanskrit.code
                        # Update all practices with same Sanskrit name
                        practices_with_same_sanskrit = session.query(Practice).filter(
                            Practice.practice_sanskrit.ilike(new_sanskrit)
                        ).all()
                        for p in practices_with_same_sanskrit:
                            p.code = practice.code
                        related_practices = session.query(Practice).filter(
                            Practice.code == practice.code,
                            Practice.id != practice_id
                        ).all()
                    else:
                        practice.code = generate_practice_code(new_sanskrit, session)
                elif practice.code:
                    # Code unchanged - find related practices with same code
                    related_practices = session.query(Practice).filter(
                        Practice.code == practice.code,
                        Practice.id != practice_id
                    ).all()
                
                # Sync all field values to related practices with same code (EXCEPT CVR score)
                for p in related_practices:
                    p.practice_sanskrit = practice.practice_sanskrit
                    p.practice_english = practice.practice_english
                    p.practice_segment = practice.practice_segment
                    p.sub_category = practice.sub_category
                    p.kosha = practice.kosha
                    # DO NOT sync CVR score - it's module-specific
                    # DO NOT sync rounds, time_minutes, strokes_per_min - these might be module-specific too
                    # Actually, let's sync these basic fields but not CVR
                
                rounds_val = request.form.get('rounds')
                practice.rounds = int(rounds_val) if rounds_val else None
                # Sync rounds to related practices
                for p in related_practices:
                    p.rounds = practice.rounds

                duration_val = request.form.get('time_minutes')
                practice.time_minutes = float(duration_val) if duration_val else None
                # Sync time_minutes to related practices
                for p in related_practices:
                    p.time_minutes = practice.time_minutes

                strokes_val = request.form.get('strokes_per_min')
                practice.strokes_per_min = int(strokes_val) if strokes_val else None
                # Sync strokes_per_min to related practices
                for p in related_practices:
                    p.strokes_per_min = practice.strokes_per_min

                cvr_val = request.form.get('cvr_score')
                try:
                    practice.cvr_score = float(cvr_val) if cvr_val else None
                except (TypeError, ValueError):
                    practice.cvr_score = None
                # DO NOT sync CVR score - it's module-specific

                session.commit()
                flash('Practice updated successfully!', 'success')
                return redirect(url_for('view_module', module_id=module_id))
            except Exception as e:
                session.rollback()
                flash(f'Error updating practice: {str(e)}', 'error')

        practice_segments = ALLOWED_CATEGORIES

        return render_template(
            'edit_practice_in_module.html',
            module=module,
            practice=practice,
            practice_segments=practice_segments
        )
    finally:
        session.close()


# API Endpoints for future RAG integration
@app.route('/api/recommendations', methods=['POST'])
def api_get_recommendations():
    """
    API endpoint to get recommendations for diseases
    
    Expected JSON body:
    {
        "diseases": ["Depression", "GAD"]
    }
    """
    from core.recommendation_engine import YogaTherapyRecommendationEngine
    
    data = request.get_json(silent=True)
    
    if not isinstance(data, dict) or 'diseases' not in data:
        return jsonify({'error': 'Please provide a list of diseases'}), 400
    
    diseases = data.get('diseases')
    if not isinstance(diseases, list):
        return jsonify({'error': '"diseases" must be a list of disease names'}), 400
    
    diseases_clean = [str(d).strip() for d in diseases if str(d).strip()]
    if not diseases_clean:
        return jsonify({'error': '"diseases" must contain at least one name'}), 400
    
    engine = YogaTherapyRecommendationEngine(DB_PATH)
    try:
        recommendations = engine.get_recommendations(diseases_clean)
        return jsonify(recommendations)
    finally:
        engine.close()


@app.route('/api/summary', methods=['POST'])
def api_get_summary():
    """
    API endpoint to get text summary of recommendations
    
    Expected JSON body:
    {
        "diseases": ["Depression", "GAD"]
    }
    """
    from core.recommendation_engine import YogaTherapyRecommendationEngine
    
    data = request.get_json(silent=True)
    
    if not isinstance(data, dict) or 'diseases' not in data:
        return jsonify({'error': 'Please provide a list of diseases'}), 400
    
    diseases = data.get('diseases')
    if not isinstance(diseases, list):
        return jsonify({'error': '"diseases" must be a list of disease names'}), 400
    
    diseases_clean = [str(d).strip() for d in diseases if str(d).strip()]
    if not diseases_clean:
        return jsonify({'error': '"diseases" must contain at least one name'}), 400
    
    engine = YogaTherapyRecommendationEngine(DB_PATH)
    try:
        summary = engine.get_summary(diseases_clean)
        return jsonify({'summary': summary})
    finally:
        engine.close()


@app.route('/api/disease/search', methods=['GET'])
def api_search_diseases():
    """Autocomplete diseases by name (unique per disease)."""
    query = request.args.get('q', '').strip()

    if not query:
        return jsonify([])

    session = get_db_session()
    try:
        diseases = (
            session.query(Disease)
            .filter(Disease.name.ilike(f'{query}%'))
            .order_by(Disease.name.asc())
            .limit(20)
            .all()
        )

        results = [
            {
                'id': disease.id,
                'name': disease.name
            }
            for disease in diseases
        ]

        return jsonify(results)
    finally:
        session.close()


@app.route('/api/practice/search', methods=['GET'])
def api_search_practices():
    """
    API endpoint for autocomplete - search practices by Sanskrit name or code
    Query parameters: q (search query), disease (optional - filter by disease), search_by (optional - 'code' or 'sanskrit', default 'sanskrit')
    Returns list of matching practices with all details
    """
    query = request.args.get('q', '')
    disease_filter = request.args.get('disease', '').strip()
    search_by = request.args.get('search_by', 'sanskrit').strip().lower()  # 'code' or 'sanskrit'
    
    if not query:
        return jsonify([])
    
    session = get_db_session()
    
    try:
        # Search for practices by code or Sanskrit name (case insensitive)
        if search_by == 'code':
            practices_query = session.query(Practice).filter(
                Practice.code.ilike(f'{query}%')
            )
        else:
            practices_query = session.query(Practice).filter(
                Practice.practice_sanskrit.ilike(f'{query}%')
            )
        
        # If disease filter is provided, filter practices linked to that disease
        if disease_filter:
            disease = session.query(Disease).filter_by(name=disease_filter).first()
            if disease:
                disease_id = disease.id
                # Filter practices that are linked to this disease
                practices_query = practices_query.join(disease_practice_association).filter(
                    disease_practice_association.c.disease_id == disease_id
                )
        
        practices = practices_query.limit(10).all()
        
        results = []
        for practice in practices:
            results.append({
                'id': practice.id,
                'practice_sanskrit': practice.practice_sanskrit or '',
                'practice_english': practice.practice_english,
                'code': practice.code or '',
                'practice_segment': practice.practice_segment,
                'kosha': practice.kosha or '',
                'sub_category': practice.sub_category or '',
                'rounds': practice.rounds,
                'time_minutes': practice.time_minutes,
                'strokes_per_min': practice.strokes_per_min,
                'strokes_per_cycle': practice.strokes_per_cycle,
                'rest_between_cycles_sec': practice.rest_between_cycles_sec,
                'description': practice.description or '',
                'how_to_do': practice.how_to_do or '',
                'variations': practice.variations or '',
                'steps': practice.steps or '',
                'cvr_score': practice.cvr_score
            })
        
        return jsonify(results)
    finally:
        session.close()


@app.route('/api/practice/validate-code-sanskrit', methods=['GET'])
def api_validate_code_sanskrit():
    """
    API endpoint to validate code/Sanskrit name consistency
    Query parameters: code (optional), sanskrit_name (optional)
    Returns validation result with any conflicts
    """
    code = request.args.get('code', '').strip()
    sanskrit_name = request.args.get('sanskrit_name', '').strip()
    
    if not code and not sanskrit_name:
        return jsonify({'valid': True, 'message': ''})
    
    session = get_db_session()
    
    try:
        # Check if code exists
        existing_practice_with_code = None
        if code:
            existing_practice_with_code = session.query(Practice).filter(
                Practice.code == code
            ).first()
        
        # Check if Sanskrit name exists
        existing_practice_with_sanskrit = None
        if sanskrit_name:
            existing_practice_with_sanskrit = session.query(Practice).filter(
                Practice.practice_sanskrit.ilike(sanskrit_name)
            ).first()
        
        # Validation logic
        if code and sanskrit_name:
            # Both provided - check for conflicts
            if existing_practice_with_code and existing_practice_with_sanskrit:
                # Both exist
                if existing_practice_with_code.code == existing_practice_with_sanskrit.code:
                    # Same code - names must match
                    existing_sanskrit = (existing_practice_with_code.practice_sanskrit or '').strip()
                    if sanskrit_name.lower() != existing_sanskrit.lower():
                        return jsonify({
                            'valid': False,
                            'message': f'Code "{code}" already exists for practice "{existing_sanskrit}". Practices with the same code must have the same Sanskrit name.',
                            'conflict_type': 'code_sanskrit_mismatch',
                            'existing_sanskrit': existing_sanskrit
                        })
                    else:
                        return jsonify({'valid': True, 'message': ''})
                else:
                    # Different codes for same Sanskrit name
                    existing_code = existing_practice_with_sanskrit.code
                    return jsonify({
                        'valid': False,
                        'message': f'Practice with Sanskrit name "{sanskrit_name}" already exists with code "{existing_code}". Using existing code for consistency.',
                        'conflict_type': 'sanskrit_code_mismatch',
                        'existing_code': existing_code
                    })
            elif existing_practice_with_code:
                # Code exists, Sanskrit name doesn't match
                existing_sanskrit = (existing_practice_with_code.practice_sanskrit or '').strip()
                if sanskrit_name.lower() != existing_sanskrit.lower():
                    return jsonify({
                        'valid': False,
                        'message': f'Code "{code}" already exists for practice "{existing_sanskrit}". Practices with the same code must have the same Sanskrit name.',
                        'conflict_type': 'code_sanskrit_mismatch',
                        'existing_sanskrit': existing_sanskrit
                    })
            elif existing_practice_with_sanskrit:
                # Sanskrit name exists, code doesn't match
                existing_code = existing_practice_with_sanskrit.code
                if existing_code and code != existing_code:
                    return jsonify({
                        'valid': False,
                        'message': f'Practice with Sanskrit name "{sanskrit_name}" already exists with code "{existing_code}". Using existing code for consistency.',
                        'conflict_type': 'sanskrit_code_mismatch',
                        'existing_code': existing_code
                    })
        
        elif code and existing_practice_with_code:
            # Only code provided - check if it exists
            existing_sanskrit = (existing_practice_with_code.practice_sanskrit or '').strip()
            if sanskrit_name:  # User is typing Sanskrit name
                if sanskrit_name.lower() != existing_sanskrit.lower():
                    return jsonify({
                        'valid': False,
                        'message': f'Code "{code}" already exists for practice "{existing_sanskrit}". Practices with the same code must have the same Sanskrit name.',
                        'conflict_type': 'code_sanskrit_mismatch',
                        'existing_sanskrit': existing_sanskrit
                    })
        
        elif sanskrit_name and existing_practice_with_sanskrit:
            # Only Sanskrit name provided - check if it exists
            existing_code = existing_practice_with_sanskrit.code
            if code:  # User is typing code
                if existing_code and code != existing_code:
                    return jsonify({
                        'valid': False,
                        'message': f'Practice with Sanskrit name "{sanskrit_name}" already exists with code "{existing_code}". Using existing code for consistency.',
                        'conflict_type': 'sanskrit_code_mismatch',
                        'existing_code': existing_code
                    })
        
        return jsonify({'valid': True, 'message': ''})
    finally:
        session.close()


@app.route('/api/contraindications/by-disease/<int:disease_id>', methods=['GET'])
def api_contraindications_by_disease(disease_id):
    """Return existing contraindications for a disease."""
    session = get_db_session()
    try:
        disease = session.query(Disease).get(disease_id)
        if not disease:
            return jsonify([])

        results = []
        for contraindication in disease.contraindications:
            results.append({
                'id': contraindication.id,
                'practice_sanskrit': contraindication.practice_sanskrit or '',
                'practice_english': contraindication.practice_english,
                'parenthetical': contraindication.source_type or ''
            })

        results.sort(key=lambda c: (c['practice_sanskrit'] or c['practice_english']).lower())
        return jsonify(results)
    finally:
        session.close()


@app.route('/api/module/search', methods=['GET'])
def api_search_modules():
    """
    API endpoint for autocomplete - search modules by name for a specific disease
    Query parameters: q (search query), disease_id (required)
    Returns list of matching modules
    """
    query = request.args.get('q', '')
    disease_id = request.args.get('disease_id')
    
    if not query or not disease_id:
        return jsonify([])
    
    session = get_db_session()
    
    try:
        # Search for modules for the specified disease
        modules = session.query(Module).filter(
            Module.disease_id == int(disease_id),
            Module.developed_by.ilike(f'%{query}%')
        ).limit(10).all()
        
        results = []
        for module in modules:
            results.append({
                'id': module.id,
                'name': module.developed_by or 'N/A'
            })
        
        return jsonify(results)
    finally:
        session.close()


@app.route('/api/module/search/all', methods=['GET'])
def api_search_all_modules():
    """
    API endpoint for autocomplete - search all modules by name
    Query parameter: q (search query)
    Returns list of matching modules with disease names
    """
    query = request.args.get('q', '')
    
    if not query:
        return jsonify([])
    
    session = get_db_session()
    
    try:
        # Search for modules
        modules = session.query(Module).filter(
            Module.developed_by.ilike(f'%{query}%')
        ).limit(10).all()
        
        results = []
        for module in modules:
            disease_name = module.disease.name if module.disease else 'N/A'
            results.append({
                'id': module.id,
                'name': module.developed_by or 'N/A',
                'disease': disease_name
            })
        
        return jsonify(results)
    finally:
        session.close()


@app.route('/api/module/search/recommendation', methods=['GET'])
def api_search_modules_for_recommendation():
    """
    API endpoint for recommendation system autocomplete
    Returns modules in format "Disease (Module Name)"
    Query parameter: q (search query)
    Prioritizes results starting with the query
    """
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify([])
    
    session = get_db_session()
    
    try:
        query_lower = query.lower()
        
        # Get all modules with their diseases
        all_modules = session.query(Module).join(Disease).all()
        
        results = []
        for module in all_modules:
            disease_name = module.disease.name if module.disease else 'N/A'
            module_name = module.developed_by or 'N/A'
            display_name = f"{disease_name} ({module_name})"
            
            disease_lower = disease_name.lower()
            module_lower = (module_name or '').lower()
            display_lower = display_name.lower()
            
            # Calculate match score: higher = better match
            score = 0
            match_type = None
            
            # Priority 1: Disease name starts with query
            if disease_lower.startswith(query_lower):
                score = 1000 + len(disease_lower)
                match_type = 'disease_starts'
            # Priority 2: Module name starts with query
            elif module_lower.startswith(query_lower):
                score = 500 + len(module_lower)
                match_type = 'module_starts'
            # Priority 3: Display name starts with query
            elif display_lower.startswith(query_lower):
                score = 300 + len(display_lower)
                match_type = 'display_starts'
            # Priority 4: Disease name contains query
            elif query_lower in disease_lower:
                score = 100 + len(disease_lower)
                match_type = 'disease_contains'
            # Priority 5: Module name contains query
            elif query_lower in module_lower:
                score = 50 + len(module_lower)
                match_type = 'module_contains'
            # Priority 6: Display name contains query
            elif query_lower in display_lower:
                score = 10 + len(display_lower)
                match_type = 'display_contains'
            else:
                continue  # No match, skip this module
            
            results.append({
                'id': module.id,
                'module_id': module.id,
                'disease_id': module.disease_id,
                'disease_name': disease_name,
                'module_name': module_name,
                'display_name': display_name,
                'score': score,
                'match_type': match_type
            })
        
        # Sort by score (descending) and then by display name
        results.sort(key=lambda x: (-x['score'], x['display_name']))
        
        # Remove score and match_type from response (they were just for sorting)
        for result in results:
            del result['score']
            del result['match_type']
        
        # Limit to top 20 results
        return jsonify(results[:20])
    finally:
        session.close()


@app.route('/api/module/practice-counts', methods=['POST'])
def api_get_practice_counts():
    """
    API endpoint to get practice counts and contraindication counts for selected modules
    Expects JSON body: {
        "major_module_id": 1,
        "comorbid_module_ids": [2, 3]
    }
    Returns: {
        "major_module": {
            "module_id": 1,
            "display_name": "Depression (Dr Hemant Bhargav, 2013)",
            "practice_count": 7,
            "contraindication_count": 1
        },
        "comorbid_modules": [
            {
                "module_id": 2,
                "display_name": "GAD (Dr Naveen GH et al., 2019)",
                "practice_count": 3,
                "contraindication_count": 2
            }
        ],
        "total_practices": 10,
        "total_contraindications": 3
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400
    
    major_module_id = data.get('major_module_id')
    comorbid_module_ids = data.get('comorbid_module_ids', [])
    
    if not major_module_id:
        return jsonify({'error': 'Major module ID required'}), 400
    
    session = get_db_session()
    
    try:
        # Get major module with practices
        major_module = session.query(Module).options(
            joinedload(Module.disease).selectinload(Disease.contraindications),
            joinedload(Module.practices)
        ).filter(Module.id == int(major_module_id)).first()
        
        if not major_module:
            return jsonify({'error': 'Major module not found'}), 404
        
        # Get contraindications for major disease
        major_contraindications = set()
        if major_module.disease:
            for contra in major_module.disease.contraindications:
                major_contraindications.add((
                    contra.practice_english.lower().strip() if contra.practice_english else '',
                    contra.practice_segment
                ))
        
        # Count practices after filtering contraindications
        major_practice_count = 0
        for practice in major_module.practices:
            practice_key = (
                practice.practice_english.lower().strip() if practice.practice_english else '',
                practice.practice_segment
            )
            if practice_key not in major_contraindications:
                major_practice_count += 1
        
        major_module_info = {
            'module_id': major_module.id,
            'display_name': f"{major_module.disease.name if major_module.disease else 'N/A'} ({major_module.developed_by or 'N/A'})",
            'practice_count': major_practice_count,
            'contraindication_count': len(major_contraindications)
        }
        
        # Get comorbid modules
        comorbid_modules_info = []
        total_comorbid_practices = 0
        total_comorbid_contraindications = set()
        
        all_comorbid_disease_ids = set()
        
        for module_id in comorbid_module_ids:
            module = session.query(Module).options(
                joinedload(Module.disease).selectinload(Disease.contraindications),
                joinedload(Module.practices)
            ).filter(Module.id == int(module_id)).first()
            
            if module:
                if module.disease:
                    all_comorbid_disease_ids.add(module.disease.id)
                
                # Get contraindications for this disease
                module_contraindications = set()
                if module.disease:
                    for contra in module.disease.contraindications:
                        module_contraindications.add((
                            contra.practice_english.lower().strip() if contra.practice_english else '',
                            contra.practice_segment
                        ))
                        total_comorbid_contraindications.add((
                            contra.practice_english.lower().strip() if contra.practice_english else '',
                            contra.practice_segment
                        ))
                
                # Count practices after filtering contraindications
                module_practice_count = 0
                for practice in module.practices:
                    practice_key = (
                        practice.practice_english.lower().strip() if practice.practice_english else '',
                        practice.practice_segment
                    )
                    if practice_key not in module_contraindications:
                        module_practice_count += 1
                
                total_comorbid_practices += module_practice_count
                
                comorbid_modules_info.append({
                    'module_id': module.id,
                    'display_name': f"{module.disease.name if module.disease else 'N/A'} ({module.developed_by or 'N/A'})",
                    'practice_count': module_practice_count,
                    'contraindication_count': len(module_contraindications)
                })
        
        # Calculate total (note: we need to account for overlapping contraindications)
        # Get all unique contraindications across all diseases
        all_disease_ids = {major_module.disease_id} | all_comorbid_disease_ids
        all_contraindications = set()
        for disease_id in all_disease_ids:
            disease = session.query(Disease).options(
                selectinload(Disease.contraindications)
            ).get(disease_id)
            if disease:
                for contra in disease.contraindications:
                    all_contraindications.add((
                        contra.practice_english.lower().strip() if contra.practice_english else '',
                        contra.practice_segment
                    ))
        
        return jsonify({
            'major_module': major_module_info,
            'comorbid_modules': comorbid_modules_info,
            'total_practices': major_practice_count + total_comorbid_practices,
            'total_contraindications': len(all_contraindications)
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================================
# Recommendation System Routes
# ============================================================================

@app.route('/recommendations', methods=['GET', 'POST'])
def recommendations():
    """Step 1: Select diseases and set weightages"""
    session = get_db_session()
    
    try:
        if request.method == 'POST':
            # Validate and redirect to category selection
            major_module_id = request.form.get('major_module_id')
            weight_major = request.form.get('weight_major', '0')
            
            if not major_module_id:
                flash('Please select a major disease module', 'error')
                return redirect(url_for('recommendations'))
            
            try:
                weight_major = int(weight_major)
            except (ValueError, TypeError):
                weight_major = 0
            
            # Validate weight total
            comorbid_module_ids = request.form.getlist('comorbid_module_ids')
            comorbid_ids_int = []
            for module_id in comorbid_module_ids:
                try:
                    comorbid_ids_int.append(int(module_id))
                except (ValueError, TypeError):
                    continue
            
            comorbid_weights = {}
            for mid in comorbid_ids_int:
                weight_key = f'weight_module_{mid}'
                w = request.form.get(weight_key, '0')
                try:
                    w = int(w)
                    if w < 0:
                        w = 0
                    if w > 100:
                        w = 100
                    comorbid_weights[mid] = w
                except (ValueError, TypeError):
                    comorbid_weights[mid] = 0
            
            total_weight = weight_major + sum(comorbid_weights.get(mid, 0) for mid in comorbid_ids_int)
            if total_weight != 100:
                flash(f'Weights must total exactly 100 (currently {total_weight}).', 'error')
                return redirect(url_for('recommendations'))
            
            # Store in session and redirect to category selection
            flask_session['recommendation_major_module_id'] = int(major_module_id)
            flask_session['recommendation_comorbid_module_ids'] = comorbid_ids_int
            flask_session['recommendation_weight_major'] = weight_major
            flask_session['recommendation_comorbid_weights'] = comorbid_weights
            
            return redirect(url_for('recommendations_categories'))
        
        # GET request - show form
        return render_template('recommendations.html')
    except Exception as e:
        flash(f'Unexpected error: {str(e)}', 'error')
        import traceback
        traceback.print_exc()
        return render_template('recommendations.html')
    finally:
        session.close()


@app.route('/recommendations/categories', methods=['GET', 'POST'])
def recommendations_categories():
    """Step 2: Select practices per category, then generate recommendations"""
    session = get_db_session()
    
    def _practice_identifier(p: Practice):
        return (p.code or '').strip().lower() or (p.practice_english or '').strip().lower()

    def _rank_key(p: Practice, selected_disease_ids: set):
        rct_val = p.rct_count if p.rct_count is not None else 0
        repeat = len([d for d in p.diseases if d.id in selected_disease_ids]) if getattr(p, 'diseases', None) else 0
        cvr_val = p.cvr_score if p.cvr_score is not None else 0
        name_val = p.practice_english or ''
        return (-rct_val, -repeat, -cvr_val, name_val)

    def _group_practices_by_category(module: Module, contraindicated_keys: set, selected_disease_ids: set):
        by_category = {}
        for p in module.practices:
            category = p.practice_segment or 'Unknown'
            if not _is_valid_category(category):
                continue
            pk = (
                (p.practice_english or '').lower().strip(),
                p.practice_segment
            )
            if pk in contraindicated_keys:
                continue
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(p)
        for category in by_category:
            by_category[category].sort(key=lambda pr: _rank_key(pr, selected_disease_ids))
        return by_category

    def _compute_category_max_counts(major_module: Module, comorbid_modules: list, contraindicated_keys: set, selected_disease_ids: set):
        category_max_counts = {}
        seen_by_category = {}
        
        def _add_practice(practice):
            category = practice.practice_segment or 'Unknown'
            if not _is_valid_category(category):
                return
            pk = (
                (practice.practice_english or '').lower().strip(),
                practice.practice_segment
            )
            if pk in contraindicated_keys:
                return
            ident = _practice_identifier(practice)
            if not ident:
                return
            if category not in seen_by_category:
                seen_by_category[category] = set()
            if ident in seen_by_category[category]:
                return
            seen_by_category[category].add(ident)
            category_max_counts[category] = category_max_counts.get(category, 0) + 1
        
        for p in major_module.practices:
            _add_practice(p)
        for m in comorbid_modules:
            for p in m.practices:
                _add_practice(p)
        
        sorted_categories = sorted(category_max_counts.items(), key=lambda x: x[0])
        total_max = sum(category_max_counts.values())
        return category_max_counts, sorted_categories, total_max
    
    try:
        if request.method == 'POST':
            # Generate recommendations based on category selections
            try:
                # Get data from session
                major_module_id = flask_session.get('recommendation_major_module_id')
                comorbid_module_ids = flask_session.get('recommendation_comorbid_module_ids', [])
                weight_major = flask_session.get('recommendation_weight_major', 0)
                comorbid_weights = flask_session.get('recommendation_comorbid_weights', {})
                
                if not major_module_id:
                    flash('Session expired. Please start over.', 'error')
                    return redirect(url_for('recommendations'))
                
                # Get category selections from form
                category_selections = {}  # category -> user_selected_count
                for key in request.form:
                    if key.startswith('category_'):
                        category = key.replace('category_', '')
                        try:
                            count = int(request.form.get(key, '0'))
                            if count > 0:
                                category_selections[category] = count
                        except (ValueError, TypeError):
                            continue
                
                if not category_selections:
                    flash('Please select at least one practice from any category', 'error')
                    return redirect(url_for('recommendations_categories'))
                
                # Fetch modules
                major_module = session.query(Module).options(
                    joinedload(Module.disease),
                    joinedload(Module.practices).joinedload(Practice.diseases)
                ).filter(Module.id == major_module_id).first()
                if not major_module:
                    flash('Major disease module not found', 'error')
                    return redirect(url_for('recommendations'))
                
                comorbid_modules = []
                for mid in comorbid_module_ids:
                    module = session.query(Module).options(
                        joinedload(Module.disease),
                        joinedload(Module.practices).joinedload(Practice.diseases)
                    ).filter(Module.id == mid).first()
                    if module:
                        comorbid_modules.append(module)
                
                # Get all diseases and contraindications
                all_modules = [major_module] + comorbid_modules
                selected_disease_ids = set()
                for module in all_modules:
                    if module.disease_id:
                        selected_disease_ids.add(module.disease_id)
                
                contraindications = []
                for disease_id in selected_disease_ids:
                    disease = session.query(Disease).get(disease_id)
                    if disease:
                        for contraindication in disease.contraindications:
                            contraindications.append(contraindication)
                
                seen_contraindications = set()
                unique_contraindications = []
                for contra in contraindications:
                    key = (contra.practice_english, contra.practice_segment)
                    if key not in seen_contraindications:
                        seen_contraindications.add(key)
                        unique_contraindications.append(contra)
                
                contraindicated_keys = set()
                for contra in unique_contraindications:
                    contraindicated_keys.add((
                        contra.practice_english.lower().strip(),
                        contra.practice_segment
                    ))
                
                # Validate category selections against maxima
                category_max_counts, _, _ = _compute_category_max_counts(major_module, comorbid_modules, contraindicated_keys, selected_disease_ids)
                validated_category_selections = {}
                for category, count in category_selections.items():
                    if category not in category_max_counts:
                        flash(f'Invalid category selection "{category}".', 'error')
                        return redirect(url_for('recommendations_categories'))
                    if count > category_max_counts[category]:
                        flash(f'Selection for "{category}" exceeds available maximum ({count} > {category_max_counts[category]}).', 'error')
                        return redirect(url_for('recommendations_categories'))
                    validated_category_selections[category] = count
                category_selections = validated_category_selections
                total_requested = sum(category_selections.values())
                
                # Get practices by category for each module with ranking
                major_practices_by_cat = _group_practices_by_category(major_module, contraindicated_keys, selected_disease_ids)
                comorbid_practices_by_cat = {}
                for m in comorbid_modules:
                    comorbid_practices_by_cat[m.id] = _group_practices_by_category(m, contraindicated_keys, selected_disease_ids)
                
                # For each category, apply weightages to user's selection
                order_modules = [major_module] + comorbid_modules  # order reflects severity (major first, then user order)
                weights_by_id = {major_module.id: weight_major}
                for m in comorbid_modules:
                    weights_by_id[m.id] = comorbid_weights.get(m.id, 0)
                
                selected_practices = []
                seen = set()
                
                def take_from_category_list(practice_list, want):
                    picked = 0
                    for p in practice_list:
                        ident = _practice_identifier(p)
                        if not ident or ident in seen:
                            continue
                        # attach selected disease repetition for downstream display
                        p.selected_disease_count = len([d for d in p.diseases if d.id in selected_disease_ids]) if getattr(p, 'diseases', None) else 0
                        seen.add(ident)
                        selected_practices.append(p)
                        picked += 1
                        if picked >= want:
                            break
                    return picked
                
                # Process each category
                for category, user_selected_count in category_selections.items():
                    # Calculate per-module targets for this category
                    base_counts = {}
                    for m in order_modules:
                        raw = (weights_by_id.get(m.id, 0) / 100.0) * user_selected_count
                        base_counts[m.id] = int(raw)  # floor
                    
                    remaining = user_selected_count - sum(base_counts.values())
                    idx = 0
                    while remaining > 0 and order_modules:
                        mid = order_modules[idx % len(order_modules)].id
                        base_counts[mid] += 1
                        remaining -= 1
                        idx += 1
                    
                    # Select practices from each module for this category
                    picked_total = 0
                    # Major module
                    major_cat_practices = major_practices_by_cat.get(category, [])
                    picked_total += take_from_category_list(major_cat_practices, base_counts.get(major_module.id, 0))
                    
                    # Comorbid modules
                    for m in comorbid_modules:
                        comorbid_cat_practices = comorbid_practices_by_cat.get(m.id, {}).get(category, [])
                        picked_total += take_from_category_list(comorbid_cat_practices, base_counts.get(m.id, 0))
                    
                    # Fallback allocation if deficit remains: pull remaining ranked items in severity order
                    deficit = user_selected_count - picked_total
                    if deficit > 0:
                        fallback_candidates = []
                        for m in order_modules:
                            cat_list = major_cat_practices if m.id == major_module.id else comorbid_practices_by_cat.get(m.id, {}).get(category, [])
                            for p in cat_list:
                                ident = _practice_identifier(p)
                                if ident and ident not in seen:
                                    fallback_candidates.append((m.id, p))
                        for _, p in fallback_candidates:
                            if deficit <= 0:
                                break
                            ident = _practice_identifier(p)
                            if not ident or ident in seen:
                                continue
                            p.selected_disease_count = len([d for d in p.diseases if d.id in selected_disease_ids]) if getattr(p, 'diseases', None) else 0
                            seen.add(ident)
                            selected_practices.append(p)
                            deficit -= 1
                
                if len(selected_practices) == 0:
                    flash('No practices selected after filtering contraindications/duplicates', 'error')
                    return redirect(url_for('recommendations_categories'))
                
                filtered_practices = selected_practices
                if len(filtered_practices) < total_requested:
                    flash(f'Only {len(filtered_practices)} of {total_requested} practices available after applying weights, deduplication, and contraindications.', 'warning')
                
                # Get RCTs for practices
                all_practice_disease_ids = set()
                practice_disease_map = {}
                for practice in filtered_practices:
                    practice_disease_ids = [d.id for d in practice.diseases]
                    practice_disease_map[practice.id] = practice_disease_ids
                    all_practice_disease_ids.update(practice_disease_ids)
                
                matching_rcts = []
                if all_practice_disease_ids:
                    matching_rcts = session.query(RCT).join(
                        rct_disease_association
                    ).filter(
                        rct_disease_association.c.disease_id.in_(list(all_practice_disease_ids))
                    ).options(
                        selectinload(RCT.diseases)
                    ).all()
                
                practice_rcts = {}
                for practice in filtered_practices:
                    practice_rcts[practice.id] = []
                    practice_disease_ids = practice_disease_map[practice.id]
                    
                    for rct in matching_rcts:
                        rct_disease_ids = [d.id for d in rct.diseases]
                        if any(did in practice_disease_ids for did in rct_disease_ids):
                            if rct.intervention_practices:
                                try:
                                    intervention_list = json.loads(rct.intervention_practices)
                                    for intervention in intervention_list:
                                        practice_name = intervention.get('name', '').strip()
                                        intervention_category = intervention.get('category', '').strip()
                                        
                                        if (practice_name and 
                                            ((practice.practice_sanskrit and practice.practice_sanskrit.lower() == practice_name.lower()) or
                                             (practice.practice_english and practice.practice_english.lower() == practice_name.lower()))):
                                            if rct.parenthetical_citation:
                                                practice_rcts[practice.id].append(rct.parenthetical_citation)
                                                break
                                        elif intervention_category and practice.practice_segment == intervention_category:
                                            if rct.parenthetical_citation:
                                                practice_rcts[practice.id].append(rct.parenthetical_citation)
                                                break
                                except:
                                    pass
                
                # Organize practices by Kosha, then Category, then Subcategory
                kosha_order = {
                    'Annamaya Kosha': 1,
                    'Pranamaya Kosha': 2,
                    'Manomaya Kosha': 3,
                    'Anandamaya Kosha': 4,
                    'Vijnanamaya Kosha': 5
                }
                
                organized_practices = {}
                for practice in filtered_practices:
                    if not hasattr(practice, 'selected_disease_count'):
                        practice.selected_disease_count = len([d for d in practice.diseases if d.id in selected_disease_ids]) if getattr(practice, 'diseases', None) else 0
                    kosha = practice.kosha or 'Unknown'
                    category = practice.practice_segment or 'Unknown'
                    subcategory = practice.sub_category or 'None'
                    
                    if kosha not in organized_practices:
                        organized_practices[kosha] = {}
                    if category not in organized_practices[kosha]:
                        organized_practices[kosha][category] = {}
                    if subcategory not in organized_practices[kosha][category]:
                        organized_practices[kosha][category][subcategory] = []
                    
                    organized_practices[kosha][category][subcategory].append({
                        'practice': practice,
                        'rcts': practice_rcts.get(practice.id, [])
                    })
                
                # Sort practices within each subcategory by RCT count
                for kosha in organized_practices:
                    for category in organized_practices[kosha]:
                        for subcategory in organized_practices[kosha][category]:
                            organized_practices[kosha][category][subcategory].sort(
                                key=lambda x: (
                                    -(x['practice'].rct_count if x['practice'].rct_count is not None else 0),
                                    -(getattr(x['practice'], 'selected_disease_count', 0)),
                                    -(x['practice'].cvr_score if x['practice'].cvr_score is not None else 0),
                                    x['practice'].practice_english or ''
                                )
                            )
                
                major_disease_name = major_module.disease.name if major_module.disease else 'N/A'
                major_module_name = major_module.developed_by or 'N/A'
                
                comorbid_disease_names = [
                    m.disease.name if m.disease else 'N/A' 
                    for m in comorbid_modules
                ]
                comorbid_module_names = [
                    m.developed_by or 'N/A'
                    for m in comorbid_modules
                ]
                
                sorted_koshas = sorted(
                    organized_practices.keys(),
                    key=lambda x: kosha_order.get(x, 999)
                )
                
                # Clear session data
                flask_session.pop('recommendation_major_module_id', None)
                flask_session.pop('recommendation_comorbid_module_ids', None)
                flask_session.pop('recommendation_weight_major', None)
                flask_session.pop('recommendation_comorbid_weights', None)
                
                return render_template('recommendations_result.html',
                                     major_disease_name=major_disease_name,
                                     major_module_name=major_module_name,
                                     comorbid_disease_names=comorbid_disease_names,
                                     comorbid_module_names=comorbid_module_names,
                                     organized_practices=organized_practices,
                                     contraindications=unique_contraindications,
                                     kosha_order=kosha_order,
                                     sorted_koshas=sorted_koshas)
            except Exception as e:
                flash(f'Error generating recommendations: {str(e)}', 'error')
                import traceback
                traceback.print_exc()
                return redirect(url_for('recommendations_categories'))
        
        # GET request - show category selection form
        # Get data from session
        major_module_id = flask_session.get('recommendation_major_module_id')
        comorbid_module_ids = flask_session.get('recommendation_comorbid_module_ids', [])
        
        if not major_module_id:
            flash('Please start from the recommendations page', 'error')
            return redirect(url_for('recommendations'))
        
        # Fetch modules
        major_module = session.query(Module).options(
            joinedload(Module.disease),
            joinedload(Module.practices)
        ).filter(Module.id == major_module_id).first()
        if not major_module:
            flash('Major disease module not found', 'error')
            return redirect(url_for('recommendations'))
        
        comorbid_modules = []
        for mid in comorbid_module_ids:
            module = session.query(Module).options(
                joinedload(Module.disease),
                joinedload(Module.practices)
            ).filter(Module.id == mid).first()
            if module:
                comorbid_modules.append(module)
        
        # Get all diseases and contraindications
        all_modules = [major_module] + comorbid_modules
        selected_disease_ids = {m.disease_id for m in all_modules if m.disease_id}
        
        contraindications = []
        for disease_id in selected_disease_ids:
            disease = session.query(Disease).get(disease_id)
            if disease:
                for contraindication in disease.contraindications:
                    contraindications.append(contraindication)
        
        seen_contraindications = set()
        unique_contraindications = []
        for contra in contraindications:
            key = (contra.practice_english, contra.practice_segment)
            if key not in seen_contraindications:
                seen_contraindications.add(key)
                unique_contraindications.append(contra)
        
        contraindicated_keys = set()
        for contra in unique_contraindications:
            contraindicated_keys.add((
                contra.practice_english.lower().strip(),
                contra.practice_segment
            ))
        
        # Count max practices per category across all modules using shared helper
        category_max_counts, sorted_categories, total_max = _compute_category_max_counts(
            major_module, comorbid_modules, contraindicated_keys, selected_disease_ids
        )
        
        return render_template('recommendations_categories.html',
                             major_module=major_module,
                             comorbid_modules=comorbid_modules,
                             category_max_counts=category_max_counts,
                             sorted_categories=sorted_categories,
                             total_max=total_max)
    except Exception as e:
        flash(f'Unexpected error: {str(e)}', 'error')
        import traceback
        traceback.print_exc()
        return redirect(url_for('recommendations'))
    finally:
        session.close()


# ============================================================================
# RCT Database Routes
# ============================================================================

def calculate_age_range(mean, std_dev):
    """Calculate age range from mean and standard deviation"""

def calculate_age_range(mean, std_dev):
    """Calculate age range from mean and standard deviation"""
    if mean and std_dev:
        lower = max(0, mean - std_dev)  # Ensure non-negative
        upper = mean + std_dev
        return f"{lower:.1f} - {upper:.1f}"
    return "N/A"


def calculate_p_value_significance(operator, p_value):
    """Determine if p-value is significant (<= 0.05)"""
    if not p_value:
        return 0
    
    if operator in ['<', '<=']:
        return 1 if p_value <= 0.05 else 0
    elif operator == '>':
        return 1 if p_value < 0.05 else 0  # p > 0.05 means not significant
    elif operator == '>=':
        return 1 if p_value <= 0.05 else 0
    elif operator == '=':
        return 1 if p_value <= 0.05 else 0
    return 0


def recalculate_practice_rct_count(session, practice):
    """
    Recalculate RCT count for a practice based on all RCT entries.
    This is called when a practice's category or disease associations change.
    """
    # Reset count
    practice.rct_count = 0
    
    # Get all RCTs
    rcts = session.query(RCT).all()
    
    for rct in rcts:
        if not rct.intervention_practices:
            continue
        
        import json
        try:
            practice_list = json.loads(rct.intervention_practices)
        except:
            continue
        
        # Get disease IDs for this RCT
        rct_disease_ids = [d.id for d in rct.diseases]
        
        # Get practice disease IDs
        practice_disease_ids = [d.id for d in practice.diseases]
        
        # Check if practice is linked to any of the RCT's diseases
        if not any(did in practice_disease_ids for did in rct_disease_ids):
            continue
        
        # Count RCTs that mention this practice (either specifically or by category)
        for practice_data in practice_list:
            practice_name = practice_data.get('name', '').strip()
            intervention_category = practice_data.get('category', '').strip()
            
            # If specific practice is mentioned
            if practice_name:
                # Check if this is the same practice
                if ((practice.practice_sanskrit == practice_name) or 
                    (practice.practice_english == practice_name)):
                    practice.rct_count += 1
                    break
            else:
                # If only category is mentioned, check if practice is in that category
                if practice.practice_segment == intervention_category:
                    practice.rct_count += 1
                    break


def increment_rct_counts(session, practice_data, disease_ids):
    """
    Increment RCT count for practices based on whether specific practice or category is specified.
    
    Args:
        practice_data: dict with 'name' and 'category' keys
            - If 'name' is provided: increment only that specific practice
            - If 'name' is empty: increment all practices in that category
        disease_ids: list of disease IDs this RCT is linked to
    """
    if not practice_data.get('category') or not disease_ids:
        return
    
    practice_name = practice_data.get('name', '').strip()
    intervention_category = practice_data.get('category', '').strip()
    
    # If specific practice is mentioned
    if practice_name:
        # Try to find the exact practice by name (check both Sanskrit and English)
        practice = session.query(Practice).filter(
            (Practice.practice_sanskrit == practice_name) |
            (Practice.practice_english == practice_name)
        ).first()
        
        if practice:
            # Check if this practice is linked to any of the diseases
            practice_disease_ids = [d.id for d in practice.diseases]
            if any(did in practice_disease_ids for did in disease_ids):
                if practice.rct_count is None:
                    practice.rct_count = 1
                else:
                    practice.rct_count += 1
    else:
        # No specific practice - increment all practices in this category
        practices = session.query(Practice).filter_by(
            practice_segment=intervention_category
        ).all()
        
        for practice in practices:
            # Check if practice is linked to any of the diseases
            practice_disease_ids = [d.id for d in practice.diseases]
            if any(did in practice_disease_ids for did in disease_ids):
                # Increment RCT count
                if practice.rct_count is None:
                    practice.rct_count = 1
                else:
                    practice.rct_count += 1
    
    session.commit()


@app.route('/rcts')
def list_rcts():
    """List all RCT entries with pagination and eager loading"""
    session = get_db_session()
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        per_page = min(per_page, 100)  # Cap at 100 per page
        
        # Use eager loading for RCTs
        query = session.query(RCT).options(
            selectinload(RCT.diseases),
            selectinload(RCT.symptoms)
        ).order_by(RCT.id.desc())
        
        # Paginate RCTs
        pagination = paginate_query(query, page, per_page)
        
        rcts = pagination.items
        
        # Get all diseases and practices for filters (these are small, no pagination needed)
        diseases = session.query(Disease).order_by(Disease.name).all()
        practices = session.query(Practice).order_by(Practice.practice_english).limit(1000).all()
        
        return render_template('rcts.html', 
                             rcts=rcts,
                             pagination=pagination,
                             diseases=diseases, 
                             practices=practices)
    except Exception as e:
        flash(f'Error loading RCTs: {str(e)}', 'error')
        return render_template('rcts.html', rcts=[], pagination=None, diseases=[], practices=[])
    finally:
        session.close()


@app.route('/api/practices')
def api_practices():
    """API endpoint to get all practices for RCT form"""
    session = get_db_session()
    try:
        practices = session.query(Practice).order_by(Practice.practice_english).all()
        results = []
        for practice in practices:
            results.append({
                'id': practice.id,
                'practice_english': practice.practice_english,
                'practice_sanskrit': practice.practice_sanskrit or '',
                'practice_segment': practice.practice_segment,
                'sub_category': practice.sub_category or '',
                'kosha': practice.kosha or '',
                'code': practice.code or ''
            })
        return jsonify(results)
    finally:
        session.close()


@app.route('/api/rct-count')
def api_rct_count():
    """API endpoint to get RCT count for a disease + practice combination"""
    session = get_db_session()
    try:
        disease_name = request.args.get('disease', '').strip()
        practice_name = request.args.get('practice', '').strip()
        
        if not disease_name or not practice_name:
            return jsonify({'error': 'Both disease and practice are required'}), 400
        
        # Find the disease
        disease = session.query(Disease).filter_by(name=disease_name).first()
        if not disease:
            return jsonify({'error': f'Disease "{disease_name}" not found'}), 404
        
        # Find the practice
        practice = session.query(Practice).filter(
            (Practice.practice_sanskrit == practice_name) |
            (Practice.practice_english == practice_name)
        ).first()
        
        if not practice:
            return jsonify({'error': f'Practice "{practice_name}" not found'}), 404
        
        # Check if the practice is linked to the disease
        practice_disease_ids = [d.id for d in practice.diseases]
        if disease.id not in practice_disease_ids:
            return jsonify({'error': f'Practice "{practice_name}" is not linked to disease "{disease_name}"'}), 404
        
        # Return the RCT count (or 0 if not set)
        count = practice.rct_count or 0
        return jsonify({'count': count})
    
    except Exception as e:
        return jsonify({'error': f'Error getting RCT count: {str(e)}'}), 500
    finally:
        session.close()


@app.route('/rct/add', methods=['GET', 'POST'])
def add_rct():
    """Add a new RCT entry"""
    session = get_db_session()
    
    try:
        if request.method == 'POST':
            # Create RCT entry
            rct = RCT(
                data_enrolled_date=request.form.get('data_enrolled_date', ''),
                database_journal=request.form.get('database_journal', ''),
                keywords=request.form.get('keywords', ''),
                doi=request.form.get('doi', ''),
                pmic_nmic=request.form.get('pmic_nmic', ''),
                title=request.form.get('title', ''),
                parenthetical_citation=request.form.get('parenthetical_citation', ''),
                citation_full=request.form.get('citation_full', ''),
                citation_link=request.form.get('citation_link', ''),
                study_type=request.form.get('study_type', ''),
                participant_type=request.form.get('participant_type', ''),
                age_mean=float(request.form.get('age_mean', 0)) if request.form.get('age_mean') else None,
                age_std_dev=float(request.form.get('age_std_dev', 0)) if request.form.get('age_std_dev') else None,
                gender_male=int(request.form.get('gender_male', 0)) if request.form.get('gender_male') else 0,
                gender_female=int(request.form.get('gender_female', 0)) if request.form.get('gender_female') else 0,
                gender_not_mentioned=int(request.form.get('gender_not_mentioned', 0)) if request.form.get('gender_not_mentioned') else 0,
                duration_type=request.form.get('duration_type', ''),
                duration_value=int(request.form.get('duration_value', 0)) if request.form.get('duration_value') else None,
                frequency_per_duration=request.form.get('frequency_per_duration', ''),
                results=request.form.get('results', ''),
                conclusion=request.form.get('conclusion', ''),
                remarks=request.form.get('remarks', '')
            )
            
            # Calculate age range
            if rct.age_mean and rct.age_std_dev:
                rct.age_range_calculated = calculate_age_range(rct.age_mean, rct.age_std_dev)
            
            # Store practices as JSON
            practice_list = []
            practice_count = int(request.form.get('practice_count', 0))
            for i in range(1, practice_count + 1):
                practice_name = request.form.get(f'practice_name_{i}', '').strip()
                practice_category = request.form.get(f'practice_category_{i}', '').strip()
                # Allow category-only entries (no practice name needed)
                if practice_category:
                    practice_list.append({
                        'name': practice_name,  # Will be empty if only category specified
                        'category': practice_category
                    })
            
            if practice_list:
                import json
                rct.intervention_practices = json.dumps(practice_list)
            
            session.add(rct)
            session.flush()  # Get the ID
            
            # Add symptoms with p-values
            symptom_count = int(request.form.get('symptom_count', 0))
            for i in range(1, symptom_count + 1):
                symptom_name = request.form.get(f'symptom_name_{i}', '').strip()
                if symptom_name:
                    p_operator = request.form.get(f'p_operator_{i}', '')
                    p_value = request.form.get(f'p_value_{i}', '')
                    scale = request.form.get(f'scale_{i}', '').strip()
                    
                    if p_value:
                        p_value_float = float(p_value)
                        is_significant = calculate_p_value_significance(p_operator, p_value_float)
                        
                        symptom = RCTSymptom(
                            symptom_name=symptom_name,
                            p_value_operator=p_operator,
                            p_value=p_value_float,
                            is_significant=is_significant,
                            scale=scale
                        )
                        session.add(symptom)
                        session.flush()
                        rct.symptoms.append(symptom)
            
            # Link diseases by name (will need to look up or create)
            disease_count = int(request.form.get('disease_count', 0))
            for i in range(1, disease_count + 1):
                disease_name = request.form.get(f'disease_{i}', '').strip()
                if disease_name:
                    # Try to find existing disease
                    disease = session.query(Disease).filter_by(name=disease_name).first()
                    if not disease:
                        # Create new disease
                        disease = Disease(name=disease_name, description=f"Disease from RCT entry")
                        session.add(disease)
                        session.flush()
                    rct.diseases.append(disease)
            
            # Increment RCT counts for each practice/category and disease combo
            if practice_list:
                disease_ids = [d.id for d in rct.diseases]
                for practice_data in practice_list:
                    increment_rct_counts(session, practice_data, disease_ids)
            
            session.commit()
            flash('RCT entry added successfully!', 'success')
            return redirect(url_for('list_rcts'))
        
        # GET request - show form
        diseases = session.query(Disease).order_by(Disease.name).all()
        practices = session.query(Practice).order_by(Practice.practice_english).all()
        return render_template('add_rct.html', diseases=diseases, practices=practices)
    
    except Exception as e:
        session.rollback()
        flash(f'Error adding RCT: {str(e)}', 'error')
        import traceback
        traceback.print_exc()
        diseases = session.query(Disease).order_by(Disease.name).all()
        practices = session.query(Practice).order_by(Practice.practice_english).all()
        return render_template('add_rct.html', diseases=diseases, practices=practices)
    finally:
        session.close()


@app.route('/rct/<int:rct_id>')
def view_rct(rct_id):
    """View a specific RCT entry"""
    session = get_db_session()
    try:
        rct = session.query(RCT).get(rct_id)
        if not rct:
            flash('RCT entry not found', 'error')
            return redirect(url_for('list_rcts'))
        
        return render_template('view_rct.html', rct=rct)
    finally:
        session.close()


@app.route('/rct/<int:rct_id>/edit', methods=['GET', 'POST'])
def edit_rct(rct_id):
    """Edit an RCT entry"""
    session = get_db_session()
    
    try:
        rct = session.query(RCT).get(rct_id)
        if not rct:
            flash('RCT entry not found', 'error')
            return redirect(url_for('list_rcts'))
        
        if request.method == 'POST':
            # Update RCT fields
            rct.data_enrolled_date = request.form.get('data_enrolled_date', '')
            rct.database_journal = request.form.get('database_journal', '')
            rct.keywords = request.form.get('keywords', '')
            rct.doi = request.form.get('doi', '')
            rct.pmic_nmic = request.form.get('pmic_nmic', '')
            rct.title = request.form.get('title', '')
            rct.parenthetical_citation = request.form.get('parenthetical_citation', '')
            rct.citation_full = request.form.get('citation_full', '')
            rct.citation_link = request.form.get('citation_link', '')
            rct.study_type = request.form.get('study_type', '')
            rct.participant_type = request.form.get('participant_type', '')
            rct.age_mean = float(request.form.get('age_mean', 0)) if request.form.get('age_mean') else None
            rct.age_std_dev = float(request.form.get('age_std_dev', 0)) if request.form.get('age_std_dev') else None
            rct.gender_male = int(request.form.get('gender_male', 0)) if request.form.get('gender_male') else 0
            rct.gender_female = int(request.form.get('gender_female', 0)) if request.form.get('gender_female') else 0
            rct.gender_not_mentioned = int(request.form.get('gender_not_mentioned', 0)) if request.form.get('gender_not_mentioned') else 0
            rct.duration_type = request.form.get('duration_type', '')
            rct.duration_value = int(request.form.get('duration_value', 0)) if request.form.get('duration_value') else None
            rct.frequency_per_duration = request.form.get('frequency_per_duration', '')
            rct.results = request.form.get('results', '')
            rct.conclusion = request.form.get('conclusion', '')
            rct.remarks = request.form.get('remarks', '')
            
            # Calculate age range
            if rct.age_mean and rct.age_std_dev:
                rct.age_range_calculated = calculate_age_range(rct.age_mean, rct.age_std_dev)
            
            # Update practices
            practice_list = []
            practice_count = int(request.form.get('practice_count', 0))
            for i in range(1, practice_count + 1):
                practice_name = request.form.get(f'practice_name_{i}', '').strip()
                practice_category = request.form.get(f'practice_category_{i}', '').strip()
                # Allow category-only entries (no practice name needed)
                if practice_category:
                    practice_list.append({
                        'name': practice_name,  # Will be empty if only category specified
                        'category': practice_category
                    })
            
            if practice_list:
                import json
                rct.intervention_practices = json.dumps(practice_list)
            else:
                rct.intervention_practices = None
            
            # Remove old symptoms
            for symptom in rct.symptoms:
                session.delete(symptom)
            rct.symptoms = []
            
            # Add new symptoms
            symptom_count = int(request.form.get('symptom_count', 0))
            for i in range(1, symptom_count + 1):
                symptom_name = request.form.get(f'symptom_name_{i}', '').strip()
                if symptom_name:
                    p_operator = request.form.get(f'p_operator_{i}', '')
                    p_value = request.form.get(f'p_value_{i}', '')
                    scale = request.form.get(f'scale_{i}', '').strip()
                    
                    if p_value:
                        p_value_float = float(p_value)
                        is_significant = calculate_p_value_significance(p_operator, p_value_float)
                        
                        symptom = RCTSymptom(
                            symptom_name=symptom_name,
                            p_value_operator=p_operator,
                            p_value=p_value_float,
                            is_significant=is_significant,
                            scale=scale
                        )
                        session.add(symptom)
                        session.flush()
                        rct.symptoms.append(symptom)
            
            # Update diseases
            rct.diseases = []
            disease_count = int(request.form.get('disease_count', 0))
            for i in range(1, disease_count + 1):
                disease_name = request.form.get(f'disease_{i}', '').strip()
                if disease_name:
                    disease = session.query(Disease).filter_by(name=disease_name).first()
                    if not disease:
                        disease = Disease(name=disease_name, description=f"Disease from RCT entry")
                        session.add(disease)
                        session.flush()
                    rct.diseases.append(disease)
            
            session.commit()
            flash('RCT entry updated successfully!', 'success')
            return redirect(url_for('list_rcts'))
        
        # GET request - show form
        diseases = session.query(Disease).order_by(Disease.name).all()
        practices = session.query(Practice).order_by(Practice.practice_english).all()
        return render_template('edit_rct.html', rct=rct, diseases=diseases, practices=practices)
    
    except Exception as e:
        session.rollback()
        flash(f'Error updating RCT: {str(e)}', 'error')
        import traceback
        traceback.print_exc()
        diseases = session.query(Disease).order_by(Disease.name).all()
        practices = session.query(Practice).order_by(Practice.practice_english).all()
        return render_template('edit_rct.html', rct=rct, diseases=diseases, practices=practices)
    finally:
        session.close()


def decrement_rct_counts(session, practice_data, disease_ids):
    """
    Decrement RCT count for practices based on whether specific practice or category is specified.
    This is the reverse of increment_rct_counts.
    """
    if not practice_data.get('category') or not disease_ids:
        return
    
    practice_name = practice_data.get('name', '').strip()
    intervention_category = practice_data.get('category', '').strip()
    
    # If specific practice is mentioned
    if practice_name:
        # Try to find the exact practice by name (check both Sanskrit and English)
        practice = session.query(Practice).filter(
            (Practice.practice_sanskrit == practice_name) |
            (Practice.practice_english == practice_name)
        ).first()
        
        if practice:
            # Check if this practice is linked to any of the diseases
            practice_disease_ids = [d.id for d in practice.diseases]
            if any(did in practice_disease_ids for did in disease_ids):
                if practice.rct_count and practice.rct_count > 0:
                    practice.rct_count -= 1
    else:
        # No specific practice - decrement all practices in this category
        practices = session.query(Practice).filter_by(
            practice_segment=intervention_category
        ).all()
        
        for practice in practices:
            # Check if practice is linked to any of the diseases
            practice_disease_ids = [d.id for d in practice.diseases]
            if any(did in practice_disease_ids for did in disease_ids):
                # Decrement RCT count
                if practice.rct_count and practice.rct_count > 0:
                    practice.rct_count -= 1
    
    session.commit()


@app.route('/rct/<int:rct_id>/delete', methods=['POST'])
def delete_rct(rct_id):
    """Delete an RCT entry"""
    session = get_db_session()
    try:
        rct = session.query(RCT).get(rct_id)
        if not rct:
            flash('RCT entry not found', 'error')
            return redirect(url_for('list_rcts'))
        
        # Get the intervention practices and diseases before deleting
        disease_ids = [d.id for d in rct.diseases]
        if rct.intervention_practices:
            import json
            practice_list = json.loads(rct.intervention_practices)
            # Decrement RCT counts for each practice/category
            for practice_data in practice_list:
                decrement_rct_counts(session, practice_data, disease_ids)
        
        session.delete(rct)
        session.commit()
        flash('RCT entry deleted successfully', 'success')
        return redirect(url_for('list_rcts'))
    except Exception as e:
        session.rollback()
        flash(f'Error deleting RCT: {str(e)}', 'error')
        return redirect(url_for('list_rcts'))
    finally:
        session.close()


# CSV Export Routes
@app.route('/export/diseases/csv')
def export_diseases_csv():
    """Export all diseases to CSV"""
    session = get_db_session()
    try:
        diseases = session.query(Disease).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Name', 'Description', 'Developed By', 'Module Description'])
        
        # Write data
        for disease in diseases:
            module = session.query(Module).filter_by(disease_id=disease.id).first()
            writer.writerow([
                disease.name or '',
                disease.description or '',
                module.developed_by if module else '',
                module.module_description if module else ''
            ])
        
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = 'attachment; filename=diseases.csv'
        return response
    finally:
        session.close()


@app.route('/export/practices/csv')
def export_practices_csv():
    """Export all practices to CSV (excluding images/videos)"""
    session = get_db_session()
    try:
        practices = session.query(Practice).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Practice Sanskrit', 'Practice English', 'Practice Segment', 'Sub Category',
            'Rounds', 'Time Minutes', 'Strokes Per Min', 'Strokes Per Cycle',
            'Rest Between Cycles Sec', 'Variations', 'Steps', 'Description',
            'How To Do', 'Used In Diseases', 'Citation Text', 'Citation Type',
            'Full Reference', 'Citation URL', 'RCT Count'
        ])
        
        # Write data
        for practice in practices:
            # Get diseases as comma-separated string
            disease_names = ', '.join([d.name for d in practice.diseases])
            
            # Get citation info
            citation_text = ''
            citation_type = ''
            full_reference = ''
            citation_url = ''
            if practice.citation:
                citation_text = practice.citation.citation_text or ''
                citation_type = practice.citation.citation_type or ''
                full_reference = practice.citation.full_reference or ''
                citation_url = practice.citation.url or ''
            
            # Parse JSON fields to readable format
            variations_str = ''
            if practice.variations:
                try:
                    variations = json.loads(practice.variations)
                    variations_str = ', '.join([str(v) for v in variations])
                except:
                    variations_str = practice.variations
            
            steps_str = ''
            if practice.steps:
                try:
                    steps = json.loads(practice.steps)
                    steps_str = ' | '.join([str(s) for s in steps])
                except:
                    steps_str = practice.steps
            
            writer.writerow([
                practice.practice_sanskrit or '',
                practice.practice_english or '',
                practice.practice_segment or '',
                practice.sub_category or '',
                practice.rounds if practice.rounds else '',
                practice.time_minutes if practice.time_minutes else '',
                practice.strokes_per_min if practice.strokes_per_min else '',
                practice.strokes_per_cycle if practice.strokes_per_cycle else '',
                practice.rest_between_cycles_sec if practice.rest_between_cycles_sec else '',
                variations_str,
                steps_str,
                practice.description or '',
                practice.how_to_do or '',
                disease_names,
                citation_text,
                citation_type,
                full_reference,
                citation_url,
                practice.rct_count or 0
            ])
        
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = 'attachment; filename=practices.csv'
        return response
    finally:
        session.close()


@app.route('/export/contraindications/csv')
def export_contraindications_csv():
    """Export all contraindications to CSV"""
    session = get_db_session()
    try:
        contraindications = session.query(Contraindication).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Practice Sanskrit', 'Practice English', 'Practice Segment', 'Sub Category',
            'Reason', 'Source Type', 'Source Name', 'Page Number', 'APA Citation',
            'Diseases'
        ])
        
        # Write data
        for contra in contraindications:
            # Get diseases as comma-separated string
            disease_names = ', '.join([d.name for d in contra.diseases])
            
            writer.writerow([
                contra.practice_sanskrit or '',
                contra.practice_english or '',
                contra.practice_segment or '',
                contra.sub_category or '',
                contra.reason or '',
                contra.source_type or '',
                contra.source_name or '',
                contra.page_number or '',
                contra.apa_citation or '',
                disease_names
            ])
        
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = 'attachment; filename=contraindications.csv'
        return response
    finally:
        session.close()


@app.route('/export/rcts/csv')
def export_rcts_csv():
    """Export all RCTs to CSV"""
    session = get_db_session()
    try:
        rcts = session.query(RCT).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Data Enrolled Date', 'Database/Journal', 'Keywords', 'DOI', 'PMIC/NMIC',
            'Title', 'Citation', 'Citation Full', 'Citation Link',
            'Study Type', 'Participant Type', 'Age Mean', 'Age Std Dev', 'Age Range Calculated',
            'Gender Male', 'Gender Female', 'Gender Not Mentioned',
            'Intervention Practices', 'Duration Type', 'Duration Value', 'Frequency Per Duration',
            'Scales', 'Results', 'Conclusion', 'Remarks', 'Diseases', 'Symptoms'
        ])
        
        # Write data
        for rct in rcts:
            # Get diseases as comma-separated string
            disease_names = ', '.join([d.name for d in rct.diseases])
            
            # Get symptoms with details
            symptom_details = []
            for symptom in rct.symptoms:
                sig_status = 'Significant' if symptom.is_significant else 'Not Significant'
                symptom_str = f"{symptom.symptom_name} (p{symptom.p_value_operator}{symptom.p_value}, {sig_status}, Scale: {symptom.scale or 'N/A'})"
                symptom_details.append(symptom_str)
            symptoms_str = ' | '.join(symptom_details)
            
            # Parse intervention practices
            intervention_str = ''
            if rct.intervention_practices:
                try:
                    practices = json.loads(rct.intervention_practices)
                    practice_details = []
                    for p in practices:
                        if p.get('name'):
                            practice_details.append(f"{p.get('name')} ({p.get('category')})")
                        else:
                            practice_details.append(f"Category: {p.get('category')}")
                    intervention_str = ' | '.join(practice_details)
                except:
                    intervention_str = rct.intervention_practices
            
            writer.writerow([
                rct.data_enrolled_date or '',
                rct.database_journal or '',
                rct.keywords or '',
                rct.doi or '',
                rct.pmic_nmic or '',
                rct.title or '',
                rct.parenthetical_citation or '',
                rct.citation_full or '',
                rct.citation_link or '',
                rct.study_type or '',
                rct.participant_type or '',
                rct.age_mean if rct.age_mean else '',
                rct.age_std_dev if rct.age_std_dev else '',
                rct.age_range_calculated or '',
                rct.gender_male if rct.gender_male else 0,
                rct.gender_female if rct.gender_female else 0,
                rct.gender_not_mentioned if rct.gender_not_mentioned else 0,
                intervention_str,
                rct.duration_type or '',
                rct.duration_value if rct.duration_value else '',
                rct.frequency_per_duration or '',
                rct.scales or '',
                rct.results or '',
                rct.conclusion or '',
                rct.remarks or '',
                disease_names,
                symptoms_str
            ])
        
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = 'attachment; filename=rcts.csv'
        return response
    finally:
        session.close()


@app.route('/api/practices/by-disease/<int:disease_id>', methods=['GET'])
def api_practices_by_disease(disease_id):
    """Return practices that belong to modules for a given disease."""
    session = get_db_session()
    try:
        practices = (
            session.query(Practice)
            .join(Module, Practice.module_id == Module.id)
            .filter(Module.disease_id == disease_id)
            .all()
        )

        unique_practices = {}
        for practice in practices:
            key = (practice.practice_sanskrit or practice.practice_english).lower()
            if key not in unique_practices:
                unique_practices[key] = practice

        results = []
        for practice in unique_practices.values():
            results.append({
                'id': practice.id,
                'practice_sanskrit': practice.practice_sanskrit or '',
                'practice_english': practice.practice_english,
                'practice_segment': practice.practice_segment,
                'sub_category': practice.sub_category or '',
                'kosha': practice.kosha or ''
            })

        results.sort(key=lambda p: (p['practice_sanskrit'] or p['practice_english']).lower())
        return jsonify(results)
    finally:
        session.close()


@app.route('/generate-synthetic-data', methods=['GET', 'POST'])
def generate_synthetic_data():
    """Generate synthetic data for testing and demonstration"""
    if request.method == 'GET':
        return render_template('generate_synthetic_data.html')
    
    # POST request - generate the data
    session = get_db_session()
    
    try:
        # 1. Create Diseases (check if they exist first, if not create them)
        diseases_data = [
            {
                'name': 'Chronic Lower Back Pain',
                'description': 'Persistent pain in the lower back region lasting more than 12 weeks'
            },
            {
                'name': 'Hypertension',
                'description': 'High blood pressure condition requiring lifestyle management'
            },
            {
                'name': 'Type 2 Diabetes',
                'description': 'Metabolic disorder characterized by insulin resistance'
            },
            {
                'name': 'Insomnia',
                'description': 'Sleep disorder characterized by difficulty falling or staying asleep'
            },
            {
                'name': 'Osteoarthritis',
                'description': 'Degenerative joint disease affecting cartilage and bone'
            }
        ]
        
        diseases = {}
        for d_data in diseases_data:
            # Check if disease already exists
            disease = session.query(Disease).filter_by(name=d_data['name']).first()
            if not disease:
                disease = Disease(name=d_data['name'], description=d_data['description'])
                session.add(disease)
                session.flush()
            diseases[d_data['name']] = disease
        
        # 2. Create Citations
        citations_data = [
            {
                'citation_text': 'Sharma et al., 2021',
                'citation_type': 'research_paper',
                'full_reference': 'Sharma, M., Singh, A., & Patel, R. (2021). Yoga therapy for chronic pain management: A randomized controlled trial. Journal of Alternative Medicine, 45(3), 234-245. doi:10.1234/jam.2021.045',
                'url': 'https://doi.org/10.1234/jam.2021.045'
            },
            {
                'citation_text': 'Kumar & Reddy, 2020',
                'citation_type': 'research_paper',
                'full_reference': 'Kumar, S., & Reddy, P. (2020). Effects of pranayama on cardiovascular health: A systematic review. International Journal of Yoga Therapy, 32(2), 156-167.',
                'url': 'https://doi.org/10.5678/ijyt.2020.032'
            },
            {
                'citation_text': 'Patel et al., 2019',
                'citation_type': 'research_paper',
                'full_reference': 'Patel, N., Gupta, M., & Desai, K. (2019). Yoga asana protocol for metabolic syndrome. Evidence-Based Complementary Medicine, 28(4), 345-358.',
                'url': 'https://doi.org/10.7890/ebcm.2019.028'
            },
            {
                'citation_text': 'Iyengar, B.K.S., 2014',
                'citation_type': 'book',
                'full_reference': 'Iyengar, B.K.S. (2014). Light on Yoga: The Classic Guide to Yoga. HarperCollins Publishers.',
                'url': None
            },
            {
                'citation_text': 'Nagendra & Nagarathna, 2018',
                'citation_type': 'research_paper',
                'full_reference': 'Nagendra, H.R., & Nagarathna, R. (2018). Integrated approach of yoga therapy for sleep disorders. Sleep Medicine Reviews, 42, 78-89.',
                'url': 'https://doi.org/10.1111/smr.2018.042'
            }
        ]
        
        citations = {}
        for c_data in citations_data:
            # Check if citation already exists
            citation = session.query(Citation).filter_by(citation_text=c_data['citation_text']).first()
            if not citation:
                citation = Citation(**c_data)
                session.add(citation)
                session.flush()
            citations[c_data['citation_text']] = citation
        
        # 3. Create Modules
        modules_data = [
            {
                'disease': 'Chronic Lower Back Pain',
                'developed_by': 'Sharma et al., 2021',
                'paper_link': 'https://doi.org/10.1234/jam.2021.045',
                'module_description': 'Comprehensive yoga therapy module for chronic lower back pain management focusing on strengthening, flexibility, and pain reduction.'
            },
            {
                'disease': 'Hypertension',
                'developed_by': 'Kumar & Reddy, 2020',
                'paper_link': 'https://doi.org/10.5678/ijyt.2020.032',
                'module_description': 'Yoga therapy protocol for hypertension management emphasizing breathing practices and relaxation techniques.'
            },
            {
                'disease': 'Type 2 Diabetes',
                'developed_by': 'Patel et al., 2019',
                'paper_link': 'https://doi.org/10.7890/ebcm.2019.028',
                'module_description': 'Integrated yoga therapy approach for Type 2 Diabetes focusing on metabolic regulation and stress management.'
            },
            {
                'disease': 'Insomnia',
                'developed_by': 'Nagendra & Nagarathna, 2018',
                'paper_link': 'https://doi.org/10.1111/smr.2018.042',
                'module_description': 'Yoga therapy module for sleep disorders incorporating relaxation, breathing, and meditation practices.'
            },
            {
                'disease': 'Osteoarthritis',
                'developed_by': 'Sharma et al., 2021',
                'paper_link': 'https://doi.org/10.1234/jam.2021.045',
                'module_description': 'Gentle yoga therapy protocol for osteoarthritis management with focus on joint mobility and pain relief.'
            }
        ]
        
        modules = {}
        for m_data in modules_data:
            # Always create new module (even if disease exists, we want new modules for synthetic data)
            module = Module(
                disease_id=diseases[m_data['disease']].id,
                developed_by=m_data['developed_by'],
                paper_link=m_data['paper_link'],
                module_description=m_data['module_description']
            )
            session.add(module)
            session.flush()
            # Store by disease name for easy lookup in practices
            modules[m_data['disease']] = module
        
        # 4. Create Practices with CVR scores
        practices_data = [
            # Chronic Lower Back Pain practices
            {
                'practice_sanskrit': 'Tadasana',
                'practice_english': 'Mountain Pose',
                'practice_segment': 'Yogasana',
                'sub_category': 'standing_asana',
                'kosha': 'Annamaya Kosha',
                'rounds': 3,
                'time_minutes': 2.0,
                'description': 'Foundation standing pose that improves posture and strengthens core muscles',
                'how_to_do': 'Stand with feet together, arms at sides. Engage thigh muscles, lift kneecaps, lengthen spine. Hold for 30-60 seconds.',
                'cvr_score': 7.5,
                'citation': 'Sharma et al., 2021',
                'module': 'Chronic Lower Back Pain',
                'diseases': ['Chronic Lower Back Pain']
            },
            {
                'practice_sanskrit': 'Bhujangasana',
                'practice_english': 'Cobra Pose',
                'practice_segment': 'Yogasana',
                'sub_category': 'prone_asana',
                'kosha': 'Annamaya Kosha',
                'rounds': 5,
                'time_minutes': 1.5,
                'description': 'Backbend that strengthens the spine and opens the chest',
                'how_to_do': 'Lie prone, place palms beside chest. Inhale and lift chest, keeping pelvis on ground. Hold for 20-30 seconds.',
                'cvr_score': 8.0,
                'citation': 'Sharma et al., 2021',
                'module': 'Chronic Lower Back Pain',
                'diseases': ['Chronic Lower Back Pain']
            },
            {
                'practice_sanskrit': 'Shavasana',
                'practice_english': 'Corpse Pose',
                'practice_segment': 'Yogasana',
                'sub_category': 'supine_asana',
                'kosha': 'Annamaya Kosha',
                'rounds': 1,
                'time_minutes': 10.0,
                'description': 'Deep relaxation pose that promotes healing and stress reduction',
                'how_to_do': 'Lie supine, arms at sides, palms up. Close eyes and relax completely. Focus on natural breathing.',
                'cvr_score': 6.0,
                'citation': 'Sharma et al., 2021',
                'module': 'Chronic Lower Back Pain',
                'diseases': ['Chronic Lower Back Pain', 'Insomnia']
            },
            {
                'practice_sanskrit': 'Marjariasana',
                'practice_english': 'Cat-Cow Pose',
                'practice_segment': 'Preparatory Practice',
                'sub_category': 'warm_up',
                'kosha': 'Annamaya Kosha',
                'rounds': 10,
                'time_minutes': 3.0,
                'description': 'Dynamic spinal movement that improves flexibility and reduces stiffness',
                'how_to_do': 'Start on hands and knees. Inhale arch back (cow), exhale round spine (cat). Repeat smoothly.',
                'cvr_score': 7.0,
                'citation': 'Sharma et al., 2021',
                'module': 'Chronic Lower Back Pain',
                'diseases': ['Chronic Lower Back Pain', 'Osteoarthritis']
            },
            
            # Hypertension practices
            {
                'practice_sanskrit': 'Anulom Vilom',
                'practice_english': 'Alternate Nostril Breathing',
                'practice_segment': 'Pranayama',
                'sub_category': 'balancing_pranayama',
                'kosha': 'Pranamaya Kosha',
                'rounds': 10,
                'time_minutes': 5.0,
                'description': 'Balancing breathing technique that calms the nervous system and reduces blood pressure',
                'how_to_do': 'Sit comfortably. Close right nostril, inhale through left. Close left, exhale through right. Reverse and repeat.',
                'cvr_score': 8.5,
                'citation': 'Kumar & Reddy, 2020',
                'module': 'Hypertension',
                'diseases': ['Hypertension']
            },
            {
                'practice_sanskrit': 'Bhramari',
                'practice_english': 'Bee Breath',
                'practice_segment': 'Pranayama',
                'sub_category': 'calming_pranayama',
                'kosha': 'Pranamaya Kosha',
                'rounds': 5,
                'time_minutes': 3.0,
                'description': 'Humming breath that activates parasympathetic nervous system',
                'how_to_do': 'Sit comfortably. Close ears with thumbs, place fingers on eyes. Inhale, exhale making humming sound like a bee.',
                'cvr_score': 9.0,
                'citation': 'Kumar & Reddy, 2020',
                'module': 'Hypertension',
                'diseases': ['Hypertension', 'Insomnia']
            },
            {
                'practice_sanskrit': 'Yoga Nidra',
                'practice_english': 'Yogic Sleep',
                'practice_segment': 'Meditation',
                'sub_category': 'guided_relaxation',
                'kosha': 'Manomaya Kosha',
                'rounds': 1,
                'time_minutes': 20.0,
                'description': 'Deep guided relaxation practice that reduces stress and promotes healing',
                'how_to_do': 'Lie in Shavasana. Follow guided instructions for body scan and visualization. Maintain awareness while deeply relaxed.',
                'cvr_score': 7.5,
                'citation': 'Kumar & Reddy, 2020',
                'module': 'Hypertension',
                'diseases': ['Hypertension', 'Insomnia']
            },
            
            # Type 2 Diabetes practices
            {
                'practice_sanskrit': 'Surya Namaskar',
                'practice_english': 'Sun Salutation',
                'practice_segment': 'Sequential Yogic Practice',
                'sub_category': 'dynamic_sequence',
                'kosha': 'Annamaya Kosha',
                'rounds': 6,
                'time_minutes': 5.0,
                'description': 'Dynamic sequence of poses that improves circulation and metabolic function',
                'how_to_do': 'Flow through 12 poses: prayer pose, upward salute, standing forward bend, lunge, plank, eight-point pose, cobra, downward dog, lunge, forward bend, upward salute, prayer pose.',
                'cvr_score': 6.5,
                'citation': 'Patel et al., 2019',
                'module': 'Type 2 Diabetes',
                'diseases': ['Type 2 Diabetes']
            },
            {
                'practice_sanskrit': 'Vajrasana',
                'practice_english': 'Thunderbolt Pose',
                'practice_segment': 'Yogasana',
                'sub_category': 'sitting_asana',
                'kosha': 'Annamaya Kosha',
                'rounds': 1,
                'time_minutes': 5.0,
                'description': 'Sitting pose that aids digestion and can be practiced after meals',
                'how_to_do': 'Kneel and sit back on heels. Keep spine straight, hands on knees. Breathe normally.',
                'cvr_score': 8.0,
                'citation': 'Patel et al., 2019',
                'module': 'Type 2 Diabetes',
                'diseases': ['Type 2 Diabetes']
            },
            {
                'practice_sanskrit': 'Kapalabhati',
                'practice_english': 'Skull Shining Breath',
                'practice_segment': 'Pranayama',
                'sub_category': 'energizing_pranayama',
                'kosha': 'Pranamaya Kosha',
                'rounds': 3,
                'time_minutes': 3.0,
                'strokes_per_min': 60,
                'strokes_per_cycle': 20,
                'rest_between_cycles_sec': 30,
                'description': 'Rapid exhalation technique that stimulates metabolism',
                'how_to_do': 'Sit comfortably. Forcefully exhale through nose while pulling navel in. Inhalation is passive. Start with 20 strokes per round.',
                'cvr_score': 7.0,
                'citation': 'Patel et al., 2019',
                'module': 'Type 2 Diabetes',
                'diseases': ['Type 2 Diabetes']
            },
            
            # Insomnia practices
            {
                'practice_sanskrit': 'Shitali',
                'practice_english': 'Cooling Breath',
                'practice_segment': 'Pranayama',
                'sub_category': 'cooling_pranayama',
                'kosha': 'Pranamaya Kosha',
                'rounds': 10,
                'time_minutes': 5.0,
                'description': 'Cooling breathing technique that calms the mind and prepares for sleep',
                'how_to_do': 'Roll tongue into tube shape. Inhale through rolled tongue, exhale through nose. If tongue cannot roll, use teeth and lips.',
                'cvr_score': 8.5,
                'citation': 'Nagendra & Nagarathna, 2018',
                'module': 'Insomnia',
                'diseases': ['Insomnia']
            },
            {
                'practice_sanskrit': 'Om Chanting',
                'practice_english': 'Om Mantra Chanting',
                'practice_segment': 'Chanting',
                'sub_category': 'mantra',
                'kosha': 'Manomaya Kosha',
                'rounds': 21,
                'time_minutes': 5.0,
                'description': 'Sacred sound vibration that calms the mind and promotes deep relaxation',
                'how_to_do': 'Sit comfortably. Chant "Om" with elongated sound: A-U-M. Feel the vibration in the body. Repeat 21 times.',
                'cvr_score': 7.5,
                'citation': 'Nagendra & Nagarathna, 2018',
                'module': 'Insomnia',
                'diseases': ['Insomnia']
            },
            
            # Osteoarthritis practices
            {
                'practice_sanskrit': 'Vrikshasana',
                'practice_english': 'Tree Pose',
                'practice_segment': 'Yogasana',
                'sub_category': 'standing_asana',
                'kosha': 'Annamaya Kosha',
                'rounds': 2,
                'time_minutes': 1.0,
                'description': 'Balancing pose that strengthens legs and improves joint stability',
                'how_to_do': 'Stand on one leg. Place other foot on inner thigh or calf (not knee). Bring hands to prayer position. Hold and switch sides.',
                'cvr_score': 6.5,
                'citation': 'Sharma et al., 2021',
                'module': 'Osteoarthritis',
                'diseases': ['Osteoarthritis']
            },
            {
                'practice_sanskrit': 'Gomukhasana',
                'practice_english': 'Cow Face Pose',
                'practice_segment': 'Yogasana',
                'sub_category': 'sitting_asana',
                'kosha': 'Annamaya Kosha',
                'rounds': 2,
                'time_minutes': 1.5,
                'description': 'Hip and shoulder opening pose that improves flexibility',
                'how_to_do': 'Sit with legs crossed. Stack knees. Reach one arm up and back, other arm behind back. Clasp hands if possible. Switch sides.',
                'cvr_score': 7.0,
                'citation': 'Sharma et al., 2021',
                'module': 'Osteoarthritis',
                'diseases': ['Osteoarthritis']
            },
            {
                'practice_sanskrit': 'Pawanmuktasana',
                'practice_english': 'Wind Relieving Pose',
                'practice_segment': 'Yogasana',
                'sub_category': 'supine_asana',
                'kosha': 'Annamaya Kosha',
                'rounds': 5,
                'time_minutes': 2.0,
                'description': 'Gentle pose that improves joint mobility and digestion',
                'how_to_do': 'Lie supine. Bring both knees to chest. Hug knees and rock gently side to side. Hold for 30 seconds.',
                'cvr_score': 8.0,
                'citation': 'Sharma et al., 2021',
                'module': 'Osteoarthritis',
                'diseases': ['Osteoarthritis']
            }
        ]
        
        for p_data in practices_data:
            # Generate code for practice
            practice_sanskrit = p_data.get('practice_sanskrit', '')
            practice_code = None
            if practice_sanskrit:
                # Check if practice with same Sanskrit name exists
                existing = session.query(Practice).filter(
                    Practice.practice_sanskrit.ilike(practice_sanskrit)
                ).first()
                if existing and existing.code:
                    practice_code = existing.code
                else:
                    practice_code = generate_practice_code(practice_sanskrit, session)
            else:
                practice_code = generate_practice_code(p_data['practice_english'], session)
            
            # Always create new practice (same practice can have different CVR in different modules)
            practice = Practice(
                practice_sanskrit=p_data.get('practice_sanskrit'),
                practice_english=p_data['practice_english'],
                practice_segment=p_data['practice_segment'],
                sub_category=p_data.get('sub_category'),
                kosha=p_data.get('kosha'),
                rounds=p_data.get('rounds'),
                time_minutes=p_data.get('time_minutes'),
                strokes_per_min=p_data.get('strokes_per_min'),
                strokes_per_cycle=p_data.get('strokes_per_cycle'),
                rest_between_cycles_sec=p_data.get('rest_between_cycles_sec'),
                description=p_data.get('description'),
                how_to_do=p_data.get('how_to_do'),
                cvr_score=p_data.get('cvr_score'),
                code=practice_code,
                citation_id=citations[p_data['citation']].id,
                module_id=modules[p_data['module']].id,
                rct_count=0
            )
            session.add(practice)
            session.flush()
            
            # Link to diseases (avoid duplicates)
            for disease_name in p_data['diseases']:
                if diseases[disease_name] not in practice.diseases:
                    practice.diseases.append(diseases[disease_name])
        
        # 5. Create Contraindications
        contraindications_data = [
            {
                'practice_sanskrit': 'Sarvangasana',
                'practice_english': 'Shoulder Stand',
                'practice_segment': 'Yogasana',
                'sub_category': 'inversion',
                'reason': 'May increase intraocular pressure and is contraindicated in hypertension',
                'source_type': 'book',
                'source_name': 'Light on Yoga by B.K.S. Iyengar',
                'page_number': '234-236',
                'apa_citation': 'Iyengar, B.K.S. (2014). Light on Yoga: The Classic Guide to Yoga (pp. 234-236). HarperCollins Publishers.',
                'diseases': ['Hypertension']
            },
            {
                'practice_sanskrit': 'Shirshasana',
                'practice_english': 'Headstand',
                'practice_segment': 'Yogasana',
                'sub_category': 'inversion',
                'reason': 'Advanced inversion that increases blood pressure and should be avoided in hypertension',
                'source_type': 'book',
                'source_name': 'Light on Yoga by B.K.S. Iyengar',
                'page_number': '198-202',
                'apa_citation': 'Iyengar, B.K.S. (2014). Light on Yoga: The Classic Guide to Yoga (pp. 198-202). HarperCollins Publishers.',
                'diseases': ['Hypertension']
            },
            {
                'practice_sanskrit': 'Paschimottanasana',
                'practice_english': 'Seated Forward Bend',
                'practice_segment': 'Yogasana',
                'sub_category': 'forward_bend',
                'reason': 'Deep forward bend may aggravate lower back pain if done incorrectly',
                'source_type': 'paper',
                'source_name': 'Sharma et al., 2021',
                'page_number': None,
                'apa_citation': 'Sharma, M., Singh, A., & Patel, R. (2021). Yoga therapy for chronic pain management: A randomized controlled trial. Journal of Alternative Medicine, 45(3), 234-245.',
                'diseases': ['Chronic Lower Back Pain']
            },
            {
                'practice_sanskrit': 'Kapalabhati',
                'practice_english': 'Skull Shining Breath',
                'practice_segment': 'Pranayama',
                'sub_category': 'energizing_pranayama',
                'reason': 'Rapid breathing technique may cause dizziness and is contraindicated in hypertension',
                'source_type': 'paper',
                'source_name': 'Kumar & Reddy, 2020',
                'page_number': None,
                'apa_citation': 'Kumar, S., & Reddy, P. (2020). Effects of pranayama on cardiovascular health: A systematic review. International Journal of Yoga Therapy, 32(2), 156-167.',
                'diseases': ['Hypertension']
            }
        ]
        
        for c_data in contraindications_data:
            contraindication = Contraindication(
                practice_sanskrit=c_data.get('practice_sanskrit'),
                practice_english=c_data['practice_english'],
                practice_segment=c_data['practice_segment'],
                sub_category=c_data.get('sub_category'),
                reason=c_data['reason'],
                source_type=c_data['source_type'],
                source_name=c_data['source_name'],
                page_number=c_data.get('page_number'),
                apa_citation=c_data.get('apa_citation')
            )
            session.add(contraindication)
            session.flush()
            
            # Link to diseases
            for disease_name in c_data['diseases']:
                contraindication.diseases.append(diseases[disease_name])
        
        # 6. Create RCTs with Symptoms
        rcts_data = [
            {
                'data_enrolled_date': '2021-03-15',
                'database_journal': 'PubMed',
                'keywords': 'yoga, chronic back pain, randomized controlled trial, alternative medicine',
                'doi': '10.1234/jam.2021.045',
                'pmic_nmic': 'PMC12345678',
                'title': 'Effectiveness of Yoga Therapy in Management of Chronic Lower Back Pain: A Randomized Controlled Trial',
                'parenthetical_citation': '(Sharma et al., 2021)',
                'citation_full': 'Sharma, M., Singh, A., & Patel, R. (2021). Effectiveness of Yoga Therapy in Management of Chronic Lower Back Pain: A Randomized Controlled Trial. Journal of Alternative Medicine, 45(3), 234-245.',
                'citation_link': 'https://doi.org/10.1234/jam.2021.045',
                'study_type': 'RCT',
                'participant_type': 'adults with chronic lower back pain',
                'age_mean': 45.2,
                'age_std_dev': 8.5,
                'age_range_calculated': '36.7-53.7',
                'gender_male': 35,
                'gender_female': 40,
                'gender_not_mentioned': 0,
                'duration_type': 'weeks',
                'duration_value': 12,
                'frequency_per_duration': '3 times per week',
                'intervention_practices': json.dumps([
                    {'practice': 'Tadasana', 'category': 'Yogasana'},
                    {'practice': 'Bhujangasana', 'category': 'Yogasana'},
                    {'practice': 'Shavasana', 'category': 'Yogasana'},
                    {'practice': 'Marjariasana', 'category': 'Preparatory Practice'}
                ]),
                'scales': 'Visual Analog Scale (VAS), Oswestry Disability Index (ODI), Roland-Morris Disability Questionnaire',
                'results': 'Significant reduction in pain intensity (VAS: p<0.001), improvement in functional disability (ODI: p<0.01), and enhanced quality of life measures.',
                'conclusion': 'Yoga therapy demonstrated significant effectiveness in reducing chronic lower back pain and improving functional outcomes.',
                'remarks': 'No adverse events reported. Participants with severe spinal conditions were excluded.',
                'diseases': ['Chronic Lower Back Pain'],
                'symptoms': [
                    {'name': 'Pain Intensity', 'p_value_operator': '<', 'p_value': 0.001, 'is_significant': 1, 'scale': 'Visual Analog Scale (VAS)'},
                    {'name': 'Functional Disability', 'p_value_operator': '<', 'p_value': 0.01, 'is_significant': 1, 'scale': 'Oswestry Disability Index (ODI)'},
                    {'name': 'Quality of Life', 'p_value_operator': '<', 'p_value': 0.05, 'is_significant': 1, 'scale': 'SF-36'}
                ]
            },
            {
                'data_enrolled_date': '2020-06-20',
                'database_journal': 'PubMed',
                'keywords': 'yoga, hypertension, blood pressure, pranayama, breathing exercises',
                'doi': '10.5678/ijyt.2020.032',
                'pmic_nmic': 'PMC98765432',
                'title': 'Effects of Pranayama-Based Yoga Therapy on Blood Pressure in Hypertensive Patients: A Randomized Controlled Study',
                'parenthetical_citation': '(Kumar & Reddy, 2020)',
                'citation_full': 'Kumar, S., & Reddy, P. (2020). Effects of Pranayama-Based Yoga Therapy on Blood Pressure in Hypertensive Patients: A Randomized Controlled Study. International Journal of Yoga Therapy, 32(2), 156-167.',
                'citation_link': 'https://doi.org/10.5678/ijyt.2020.032',
                'study_type': 'RCT',
                'participant_type': 'hypertensive adults',
                'age_mean': 52.8,
                'age_std_dev': 10.2,
                'age_range_calculated': '42.6-63.0',
                'gender_male': 42,
                'gender_female': 38,
                'gender_not_mentioned': 0,
                'duration_type': 'weeks',
                'duration_value': 8,
                'frequency_per_duration': 'Daily practice, 30 minutes',
                'intervention_practices': json.dumps([
                    {'practice': 'Anulom Vilom', 'category': 'Pranayama'},
                    {'practice': 'Bhramari', 'category': 'Pranayama'},
                    {'practice': 'Yoga Nidra', 'category': 'Meditation'}
                ]),
                'scales': 'Systolic Blood Pressure (SBP), Diastolic Blood Pressure (DBP), Heart Rate Variability (HRV)',
                'results': 'Significant reduction in both systolic (p<0.001) and diastolic (p<0.01) blood pressure. Improvement in HRV parameters indicating enhanced autonomic function.',
                'conclusion': 'Pranayama-based yoga therapy is an effective complementary intervention for hypertension management.',
                'remarks': 'Participants were advised to continue medication as prescribed. No adverse effects observed.',
                'diseases': ['Hypertension'],
                'symptoms': [
                    {'name': 'Systolic Blood Pressure', 'p_value_operator': '<', 'p_value': 0.001, 'is_significant': 1, 'scale': 'Systolic Blood Pressure (SBP)'},
                    {'name': 'Diastolic Blood Pressure', 'p_value_operator': '<', 'p_value': 0.01, 'is_significant': 1, 'scale': 'Diastolic Blood Pressure (DBP)'},
                    {'name': 'Heart Rate Variability', 'p_value_operator': '<', 'p_value': 0.05, 'is_significant': 1, 'scale': 'HRV'}
                ]
            },
            {
                'data_enrolled_date': '2019-09-10',
                'database_journal': 'PubMed',
                'keywords': 'yoga, type 2 diabetes, glycemic control, metabolic syndrome',
                'doi': '10.7890/ebcm.2019.028',
                'pmic_nmic': 'PMC55555555',
                'title': 'Integrated Yoga Therapy for Glycemic Control in Type 2 Diabetes Mellitus: A Randomized Controlled Trial',
                'parenthetical_citation': '(Patel et al., 2019)',
                'citation_full': 'Patel, N., Gupta, M., & Desai, K. (2019). Integrated Yoga Therapy for Glycemic Control in Type 2 Diabetes Mellitus: A Randomized Controlled Trial. Evidence-Based Complementary Medicine, 28(4), 345-358.',
                'citation_link': 'https://doi.org/10.7890/ebcm.2019.028',
                'study_type': 'RCT',
                'participant_type': 'adults with Type 2 Diabetes',
                'age_mean': 48.5,
                'age_std_dev': 9.8,
                'age_range_calculated': '38.7-58.3',
                'gender_male': 30,
                'gender_female': 35,
                'gender_not_mentioned': 0,
                'duration_type': 'weeks',
                'duration_value': 16,
                'frequency_per_duration': '5 times per week',
                'intervention_practices': json.dumps([
                    {'practice': 'Surya Namaskar', 'category': 'Sequential Yogic Practice'},
                    {'practice': 'Vajrasana', 'category': 'Yogasana'},
                    {'practice': 'Kapalabhati', 'category': 'Pranayama'}
                ]),
                'scales': 'Fasting Blood Glucose (FBG), Postprandial Blood Glucose (PPBG), HbA1c, Lipid Profile',
                'results': 'Significant improvement in FBG (p<0.01), PPBG (p<0.05), and HbA1c (p<0.001). Positive changes in lipid profile observed.',
                'conclusion': 'Integrated yoga therapy significantly improves glycemic control and metabolic parameters in Type 2 Diabetes.',
                'remarks': 'Participants maintained their diabetic medication. Yoga was used as complementary therapy.',
                'diseases': ['Type 2 Diabetes'],
                'symptoms': [
                    {'name': 'Fasting Blood Glucose', 'p_value_operator': '<', 'p_value': 0.01, 'is_significant': 1, 'scale': 'FBG (mg/dL)'},
                    {'name': 'HbA1c', 'p_value_operator': '<', 'p_value': 0.001, 'is_significant': 1, 'scale': 'HbA1c (%)'},
                    {'name': 'Postprandial Blood Glucose', 'p_value_operator': '<', 'p_value': 0.05, 'is_significant': 1, 'scale': 'PPBG (mg/dL)'}
                ]
            },
            {
                'data_enrolled_date': '2018-11-05',
                'database_journal': 'PubMed',
                'keywords': 'yoga, insomnia, sleep disorders, sleep quality, pranayama',
                'doi': '10.1111/smr.2018.042',
                'pmic_nmic': 'PMC44444444',
                'title': 'Yoga Therapy for Primary Insomnia: A Randomized Controlled Trial',
                'parenthetical_citation': '(Nagendra & Nagarathna, 2018)',
                'citation_full': 'Nagendra, H.R., & Nagarathna, R. (2018). Yoga Therapy for Primary Insomnia: A Randomized Controlled Trial. Sleep Medicine Reviews, 42, 78-89.',
                'citation_link': 'https://doi.org/10.1111/smr.2018.042',
                'study_type': 'RCT',
                'participant_type': 'adults with primary insomnia',
                'age_mean': 38.6,
                'age_std_dev': 11.4,
                'age_range_calculated': '27.2-50.0',
                'gender_male': 25,
                'gender_female': 45,
                'gender_not_mentioned': 0,
                'duration_type': 'weeks',
                'duration_value': 6,
                'frequency_per_duration': 'Daily practice before bedtime',
                'intervention_practices': json.dumps([
                    {'practice': 'Shitali', 'category': 'Pranayama'},
                    {'practice': 'Om Chanting', 'category': 'Chanting'},
                    {'practice': 'Shavasana', 'category': 'Yogasana'},
                    {'practice': 'Yoga Nidra', 'category': 'Meditation'}
                ]),
                'scales': 'Pittsburgh Sleep Quality Index (PSQI), Insomnia Severity Index (ISI), Sleep Efficiency',
                'results': 'Significant improvement in PSQI scores (p<0.001), reduction in ISI scores (p<0.01), and increased sleep efficiency (p<0.05).',
                'conclusion': 'Yoga therapy significantly improves sleep quality and reduces insomnia symptoms in patients with primary insomnia.',
                'remarks': 'Practice was done in evening before sleep. Participants reported feeling more relaxed and falling asleep faster.',
                'diseases': ['Insomnia'],
                'symptoms': [
                    {'name': 'Sleep Quality', 'p_value_operator': '<', 'p_value': 0.001, 'is_significant': 1, 'scale': 'Pittsburgh Sleep Quality Index (PSQI)'},
                    {'name': 'Insomnia Severity', 'p_value_operator': '<', 'p_value': 0.01, 'is_significant': 1, 'scale': 'Insomnia Severity Index (ISI)'},
                    {'name': 'Sleep Efficiency', 'p_value_operator': '<', 'p_value': 0.05, 'is_significant': 1, 'scale': 'Sleep Efficiency (%)'}
                ]
            },
            {
                'data_enrolled_date': '2021-01-20',
                'database_journal': 'PubMed',
                'keywords': 'yoga, osteoarthritis, joint pain, mobility, flexibility',
                'doi': '10.1234/jam.2021.045',
                'pmic_nmic': 'PMC33333333',
                'title': 'Gentle Yoga Therapy for Knee Osteoarthritis: A Randomized Controlled Trial',
                'parenthetical_citation': '(Sharma et al., 2021)',
                'citation_full': 'Sharma, M., Singh, A., & Patel, R. (2021). Gentle Yoga Therapy for Knee Osteoarthritis: A Randomized Controlled Trial. Journal of Alternative Medicine, 45(3), 234-245.',
                'citation_link': 'https://doi.org/10.1234/jam.2021.045',
                'study_type': 'RCT',
                'participant_type': 'elderly adults with knee osteoarthritis',
                'age_mean': 62.3,
                'age_std_dev': 7.8,
                'age_range_calculated': '54.5-70.1',
                'gender_male': 20,
                'gender_female': 30,
                'gender_not_mentioned': 0,
                'duration_type': 'weeks',
                'duration_value': 10,
                'frequency_per_duration': '3 times per week',
                'intervention_practices': json.dumps([
                    {'practice': 'Vrikshasana', 'category': 'Yogasana'},
                    {'practice': 'Gomukhasana', 'category': 'Yogasana'},
                    {'practice': 'Pawanmuktasana', 'category': 'Yogasana'},
                    {'practice': 'Marjariasana', 'category': 'Preparatory Practice'}
                ]),
                'scales': 'Western Ontario and McMaster Universities Osteoarthritis Index (WOMAC), Visual Analog Scale (VAS), Range of Motion (ROM)',
                'results': 'Significant improvement in WOMAC scores (p<0.01), reduction in pain intensity (p<0.05), and increased range of motion (p<0.05).',
                'conclusion': 'Gentle yoga therapy improves pain, function, and mobility in patients with knee osteoarthritis.',
                'remarks': 'All poses were modified for safety. Participants with severe joint deformities were excluded.',
                'diseases': ['Osteoarthritis'],
                'symptoms': [
                    {'name': 'Pain Intensity', 'p_value_operator': '<', 'p_value': 0.05, 'is_significant': 1, 'scale': 'Visual Analog Scale (VAS)'},
                    {'name': 'Functional Status', 'p_value_operator': '<', 'p_value': 0.01, 'is_significant': 1, 'scale': 'WOMAC'},
                    {'name': 'Range of Motion', 'p_value_operator': '<', 'p_value': 0.05, 'is_significant': 1, 'scale': 'ROM (degrees)'}
                ]
            }
        ]
        
        for rct_data in rcts_data:
            rct = RCT(
                data_enrolled_date=rct_data['data_enrolled_date'],
                database_journal=rct_data['database_journal'],
                keywords=rct_data['keywords'],
                doi=rct_data['doi'],
                pmic_nmic=rct_data['pmic_nmic'],
                title=rct_data['title'],
                parenthetical_citation=rct_data['parenthetical_citation'],
                citation_full=rct_data['citation_full'],
                citation_link=rct_data['citation_link'],
                study_type=rct_data['study_type'],
                participant_type=rct_data['participant_type'],
                age_mean=rct_data['age_mean'],
                age_std_dev=rct_data['age_std_dev'],
                age_range_calculated=rct_data['age_range_calculated'],
                gender_male=rct_data['gender_male'],
                gender_female=rct_data['gender_female'],
                gender_not_mentioned=rct_data['gender_not_mentioned'],
                duration_type=rct_data['duration_type'],
                duration_value=rct_data['duration_value'],
                frequency_per_duration=rct_data['frequency_per_duration'],
                intervention_practices=rct_data['intervention_practices'],
                scales=rct_data['scales'],
                results=rct_data['results'],
                conclusion=rct_data['conclusion'],
                remarks=rct_data.get('remarks'),
                rct_number=1
            )
            session.add(rct)
            session.flush()
            
            # Link to diseases
            for disease_name in rct_data['diseases']:
                rct.diseases.append(diseases[disease_name])
            
            # Create and link symptoms
            for symptom_data in rct_data['symptoms']:
                symptom = RCTSymptom(
                    symptom_name=symptom_data['name'],
                    p_value_operator=symptom_data['p_value_operator'],
                    p_value=symptom_data['p_value'],
                    is_significant=symptom_data['is_significant'],
                    scale=symptom_data['scale']
                )
                session.add(symptom)
                session.flush()
                rct.symptoms.append(symptom)
        
        # Commit all changes
        session.commit()
        
        # Get final counts
        final_disease_count = session.query(Disease).count()
        final_module_count = session.query(Module).count()
        final_practice_count = session.query(Practice).count()
        
        flash(f'✅ Synthetic data generated successfully! Added: {len(diseases)} diseases (total in DB: {final_disease_count}), {len(citations)} citations, {len(modules)} modules (total in DB: {final_module_count}), {len(practices_data)} practices (total in DB: {final_practice_count}), {len(contraindications_data)} contraindications, and {len(rcts_data)} RCTs.', 'success')
        return redirect(url_for('list_modules'))
        
    except Exception as e:
        session.rollback()
        flash(f'❌ Error generating synthetic data: {str(e)}', 'error')
        import traceback
        traceback.print_exc()
        return redirect(url_for('generate_synthetic_data'))
    finally:
        session.close()


if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '5000'))
    app.run(debug=debug_mode, host=host, port=port)