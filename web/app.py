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

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
from database.models import (
    Disease, Practice, Citation, Contraindication, DiseaseCombination, Module,
    RCT, RCTSymptom,
    create_database, get_session, disease_contraindication_association,
    disease_practice_association
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

# Database path
DB_PATH = 'sqlite:///yoga_therapy.db'

# Configuration for file uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov', 'wmv'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# Create upload directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'photos'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'videos'), exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize database on startup
create_database(DB_PATH)


def get_db_session():
    """Helper function to get database session"""
    return get_session(DB_PATH)


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
    """List all diseases"""
    session = get_db_session()
    try:
        diseases = session.query(Disease).all()
        # Force load the practices and modules relationships before closing session
        for disease in diseases:
            _ = len(disease.practices)  # This loads the relationship
            _ = len(disease.modules)  # This loads the modules relationship
            # Force load module details
            for module in disease.modules:
                _ = module.developed_by
                _ = module.paper_link
        return render_template('diseases.html', diseases=diseases)
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
        session.delete(disease)
        
        # Also delete associated module if exists
        module = session.query(Module).filter_by(disease_id=disease_id).first()
        if module:
            session.delete(module)
        
        session.commit()
        session.close()
        
        flash(f'Disease "{disease_name}" deleted successfully!', 'success')
        return redirect(url_for('list_diseases'))
    except Exception as e:
        session.close()
        flash(f'Error deleting disease: {str(e)}', 'error')
        return redirect(url_for('list_diseases'))


@app.route('/practices')
def list_practices():
    """List all practices, grouped by all fields except module"""
    session = get_db_session()
    
    try:
        # Get filter parameters
        segment_filter = request.args.get('segment', '')
        search_term = request.args.get('search', '')
        
        query = session.query(Practice)
        
        if segment_filter:
            query = query.filter(Practice.practice_segment == segment_filter)
        
        if search_term:
            query = query.filter(
                (Practice.practice_english.ilike(f'%{search_term}%')) |
                (Practice.practice_sanskrit.ilike(f'%{search_term}%'))
            )
        
        practices = query.all()
        
        # Force load relationships before closing session
        for practice in practices:
            _ = len(practice.diseases)  # Load diseases relationship
            # Force load module and citation
            if practice.module:
                _ = practice.module.id  # Load module ID
                _ = practice.module.developed_by
                _ = practice.module.paper_link
            if practice.citation:
                _ = practice.citation.citation_text  # Load citation
        
        # Group practices by all fields except module_id
        # Create a key based on all fields except module_id
        grouped_practices = {}
        for practice in practices:
            # Create a unique key based on all fields except module_id
            key = (
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
                tuple(sorted([d.id for d in practice.diseases])),  # Sorted disease IDs
                practice.rct_count or 0
            )
            
            if key not in grouped_practices:
                grouped_practices[key] = {
                    'practice': practice,  # Use first practice as representative
                    'modules': [],  # List of (module_id, developed_by) tuples
                    'practice_ids': []  # All practice IDs in this group
                }
            
            # Add module information if it exists
            if practice.module and practice.module.developed_by:
                module_info = (practice.module.id, practice.module.developed_by)
                if module_info not in grouped_practices[key]['modules']:
                    grouped_practices[key]['modules'].append(module_info)
            
            # Track all practice IDs in this group
            if practice.id not in grouped_practices[key]['practice_ids']:
                grouped_practices[key]['practice_ids'].append(practice.id)
        
        # Convert to list for template
        grouped_list = list(grouped_practices.values())
        
        # Get all unique segments for filter dropdown
        all_segments = session.query(Practice.practice_segment).distinct().all()
        segments = [s[0] for s in all_segments]
        
        return render_template('practices.html',
                             practices=grouped_list,
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
        # Create practice
        practice = Practice(
            practice_sanskrit=request.form.get('practice_sanskrit', ''),
            practice_english=request.form['practice_english'],
            practice_segment=request.form['practice_segment'],
            sub_category=request.form.get('sub_category', ''),
            kosha=request.form.get('kosha', ''),
            rounds=int(request.form['rounds']) if request.form.get('rounds') else None,
            time_minutes=float(request.form['time_minutes']) if request.form.get('time_minutes') else None,
            description=request.form.get('description', ''),
            how_to_do=request.form.get('how_to_do', '')
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
        
        # Link to diseases and modules
        disease_ids = request.form.getlist('diseases')
        for disease_id in disease_ids:
            disease = session.query(Disease).get(int(disease_id))
            if disease:
                practice.diseases.append(disease)
                # Check if module is specified for this disease
                module_id_key = f'module_id_{disease_id}'
                module_id = request.form.get(module_id_key)
                if module_id:
                    module = session.query(Module).get(int(module_id))
                    if module and module.disease_id == int(disease_id):
                        practice.module_id = module.id
        
        session.add(practice)
        session.flush()  # Flush to get the ID
        
        # Handle file uploads after we have the ID
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and photo.filename and allowed_file(photo.filename):
                filename = secure_filename(photo.filename)
                photo_path = os.path.join(UPLOAD_FOLDER, 'photos', f'{practice.id}_{filename}')
                photo.save(photo_path)
                practice.photo_path = f'/static/uploads/photos/{practice.id}_{filename}'
        
        if 'video' in request.files:
            video = request.files['video']
            if video and video.filename and allowed_file(video.filename):
                filename = secure_filename(video.filename)
                video_path = os.path.join(UPLOAD_FOLDER, 'videos', f'{practice.id}_{filename}')
                video.save(video_path)
                practice.video_path = f'/static/uploads/videos/{practice.id}_{filename}'
        
        session.commit()
        
        flash(f'Practice "{practice.practice_english}" added successfully!', 'success')
        session.close()
        return redirect(url_for('list_practices'))
    
    # GET request - show form
    diseases = session.query(Disease).all()
    session.close()
    
    return render_template('add_practice.html', diseases=diseases)


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
            # Update practice fields
            practice.practice_sanskrit = request.form.get('practice_sanskrit', '')
            practice.practice_english = request.form['practice_english']
            practice.practice_segment = request.form['practice_segment']
            practice.sub_category = request.form.get('sub_category', '')
            practice.kosha = request.form.get('kosha', '')
            practice.rounds = int(request.form['rounds']) if request.form.get('rounds') else None
            practice.time_minutes = float(request.form['time_minutes']) if request.form.get('time_minutes') else None
            practice.how_to_do = request.form.get('how_to_do', '')
            practice.description = request.form.get('description', '')
            
            # Handle optional fields
            if request.form.get('strokes_per_min'):
                practice.strokes_per_min = int(request.form['strokes_per_min'])
            
            if request.form.get('strokes_per_cycle'):
                practice.strokes_per_cycle = int(request.form['strokes_per_cycle'])
            
            if request.form.get('rest_between_cycles_sec'):
                practice.rest_between_cycles_sec = int(request.form['rest_between_cycles_sec'])
            
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
                if photo and photo.filename and allowed_file(photo.filename):
                    filename = secure_filename(photo.filename)
                    photo_path = os.path.join(UPLOAD_FOLDER, 'photos', f'{practice.id}_{filename}')
                    photo.save(photo_path)
                    practice.photo_path = f'/static/uploads/photos/{practice.id}_{filename}'
            
            if 'video' in request.files:
                video = request.files['video']
                if video and video.filename and allowed_file(video.filename):
                    filename = secure_filename(video.filename)
                    video_path = os.path.join(UPLOAD_FOLDER, 'videos', f'{practice.id}_{filename}')
                    video.save(video_path)
                    practice.video_path = f'/static/uploads/videos/{practice.id}_{filename}'
            
            # Store old category and disease associations for comparison
            old_category = practice.practice_segment
            old_disease_ids = set([d.id for d in practice.diseases])
            
            # Get the practice key to find all related practices
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
                practice.rct_count or 0
            )
            
            # Find all related practices (identical except for module)
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
                    p.rct_count or 0
                )
                if p_key == practice_key:
                    related_practices.append(p)
            
            # Update all related practices with new field values
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
            
            # Get disease associations and modules from form
            disease_ids = request.form.getlist('diseases')
            
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
    """List all contraindications grouped by disease"""
    session = get_db_session()
    try:
        # Get all diseases with their contraindications
        diseases = session.query(Disease).all()
        disease_contraindications = {}
        
        for disease in diseases:
            contraindications = session.query(Contraindication).join(
                disease_contraindication_association
            ).filter(disease_contraindication_association.c.disease_id == disease.id).all()
            
            if contraindications:
                disease_contraindications[disease] = contraindications
        
        return render_template('contraindications.html', 
                             disease_contraindications=disease_contraindications)
    finally:
        session.close()


@app.route('/contraindication/add', methods=['GET', 'POST'])
def add_contraindication():
    """Add a new contraindication for one or more diseases"""
    session = get_db_session()
    
    if request.method == 'POST':
        # Create the contraindication
        contraindication = Contraindication(
            practice_english=request.form['practice_english'],
            practice_sanskrit=request.form.get('practice_sanskrit', ''),
            practice_segment=request.form['practice_segment'],
            sub_category=request.form.get('sub_category', ''),
            reason=request.form.get('reason', ''),
            source_type=request.form.get('source_type', ''),
            source_name=request.form.get('source_name', ''),
            page_number=request.form.get('page_number', ''),
            apa_citation=request.form.get('apa_citation', '')
        )
        
        session.add(contraindication)
        session.flush()  # Get the ID
        
        # Link to diseases (now we link to individual diseases, not combinations)
        disease_ids = request.form.getlist('diseases')
        for disease_id in disease_ids:
            disease = session.query(Disease).get(int(disease_id))
            if disease:
                contraindication.diseases.append(disease)
        
        session.commit()
        
        flash('Contraindication added successfully!', 'success')
        session.close()
        return redirect(url_for('list_contraindications'))
    
    # GET request - show individual diseases
    diseases = session.query(Disease).all()
    session.close()
    
    return render_template('add_contraindication.html', diseases=diseases)


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
            contraindication.practice_english = request.form['practice_english']
            contraindication.practice_sanskrit = request.form.get('practice_sanskrit', '')
            contraindication.practice_segment = request.form['practice_segment']
            contraindication.sub_category = request.form.get('sub_category', '')
            contraindication.reason = request.form.get('reason', '')
            contraindication.source_type = request.form.get('source_type', '')
            contraindication.source_name = request.form.get('source_name', '')
            contraindication.page_number = request.form.get('page_number', '')
            contraindication.apa_citation = request.form.get('apa_citation', '')
            
            # Update disease associations
            contraindication.diseases = []
            disease_ids = request.form.getlist('diseases')
            for disease_id in disease_ids:
                disease = session.query(Disease).get(int(disease_id))
                if disease:
                    contraindication.diseases.append(disease)
            
            session.commit()
            session.close()
            
            flash('Contraindication updated successfully!', 'success')
            return redirect(url_for('list_contraindications'))
        
        # GET request
        diseases = session.query(Disease).all()
        return render_template('edit_contraindication.html', 
                             contraindication=contraindication, 
                             diseases=diseases)
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
    """List all citations"""
    session = get_db_session()
    try:
        citations = session.query(Citation).all()
        # Force load practices relationship
        for citation in citations:
            _ = len(citation.practices)
        return render_template('citations.html', citations=citations)
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
    """List all modules"""
    session = get_db_session()
    try:
        # Get filter parameters
        search_term = request.args.get('search', '')
        
        query = session.query(Module)
        
        if search_term:
            query = query.filter(Module.developed_by.ilike(f'%{search_term}%'))
        
        modules = query.all()
        
        # Force load relationships before closing session
        for module in modules:
            if module.disease:
                _ = module.disease.name
            if module.practices:
                _ = len(module.practices)
        return render_template('modules.html', modules=modules, search_term=search_term)
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
        
        # Force load relationships
        if module.disease:
            _ = module.disease.name
        
        # Organize practices by segment
        practices_by_segment = {}
        if module.practices:
            for practice in module.practices:
                segment = practice.practice_segment
                if segment not in practices_by_segment:
                    practices_by_segment[segment] = []
                practices_by_segment[segment].append(practice)
                # Force load citation if exists
                if practice.citation:
                    _ = practice.citation.citation_text
        
        return render_template('view_module.html',
                             module=module,
                             practices_by_segment=practices_by_segment)
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
        
        if request.method == 'POST':
            try:
                # Collect variations from form
                variations = []
                variation_count = 1
                while True:
                    variation_key = f'variation_{variation_count}'
                    if variation_key not in request.form:
                        break
                    variation_text = request.form.get(variation_key, '').strip()
                    if variation_text:
                        variation_ref = request.form.get(f'variation_ref_{variation_count}', '').strip()
                        variations.append({
                            'text': variation_text,
                            'referred_in': variation_ref if variation_ref else None
                        })
                    variation_count += 1
                
                # Create practice
                practice = Practice(
                    practice_sanskrit=request.form.get('practice_sanskrit', ''),
                    practice_english=request.form['practice_english'],
                    practice_segment=request.form['practice_segment'],
                    sub_category=request.form.get('sub_category', ''),
                    kosha=request.form.get('kosha', ''),
                    rounds=int(request.form['rounds']) if request.form.get('rounds') else None,
                    time_minutes=float(request.form['time_minutes']) if request.form.get('time_minutes') else None,
                    strokes_per_min=int(request.form['strokes_per_min']) if request.form.get('strokes_per_min') else None,
                    variations=json.dumps(variations) if variations else None,
                    description=request.form.get('description', ''),
                    module_id=module_id  # Associate with module
                )
                
                # Associate practice with module's disease automatically
                if module.disease:
                    practice.diseases.append(module.disease)
                
                # Handle file uploads
                if 'photo' in request.files:
                    photo = request.files['photo']
                    if photo and photo.filename and allowed_file(photo.filename):
                        filename = secure_filename(photo.filename)
                        photo_path = os.path.join(UPLOAD_FOLDER, 'photos', f"{module_id}_{practice.practice_english}_{filename}")
                        photo.save(photo_path)
                        practice.photo_path = photo_path
                
                if 'video' in request.files:
                    video = request.files['video']
                    if video and video.filename and allowed_file(video.filename):
                        filename = secure_filename(video.filename)
                        video_path = os.path.join(UPLOAD_FOLDER, 'videos', f"{module_id}_{practice.practice_english}_{filename}")
                        video.save(video_path)
                        practice.video_path = video_path
                
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
        practice_segments = [
            'Preparatory Practice',
            'Breathing Practice',
            'Sequential Yogic Practice',
            'Yogasana',
            'Pranayama',
            'Meditation',
            'Chanting',
            'Additional Practices',
            'Kriya (Cleansing Techniques)',
            'Yogic Counselling'
        ]
        
        return render_template('add_practice_to_module.html', 
                             module=module, 
                             practice_segments=practice_segments)
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
    
    data = request.get_json()
    
    if not data or 'diseases' not in data:
        return jsonify({'error': 'Please provide a list of diseases'}), 400
    
    engine = YogaTherapyRecommendationEngine(DB_PATH)
    try:
        recommendations = engine.get_recommendations(data['diseases'])
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
    
    data = request.get_json()
    
    if not data or 'diseases' not in data:
        return jsonify({'error': 'Please provide a list of diseases'}), 400
    
    engine = YogaTherapyRecommendationEngine(DB_PATH)
    try:
        summary = engine.get_summary(data['diseases'])
        return jsonify({'summary': summary})
    finally:
        engine.close()


@app.route('/api/practice/search', methods=['GET'])
def api_search_practices():
    """
    API endpoint for autocomplete - search practices by Sanskrit name
    Query parameters: q (search query), disease (optional - filter by disease)
    Returns list of matching practices with all details
    """
    query = request.args.get('q', '')
    disease_filter = request.args.get('disease', '').strip()
    
    if not query:
        return jsonify([])
    
    session = get_db_session()
    
    try:
        # Search for practices starting with the query (case insensitive)
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
                'steps': practice.steps or ''
            })
        
        return jsonify(results)
    finally:
        session.close()


@app.route('/api/disease/search', methods=['GET'])
def api_search_diseases():
    """
    API endpoint for autocomplete - search diseases by name
    Query parameter: q (search query)
    Returns list of matching diseases
    """
    query = request.args.get('q', '')
    
    if not query:
        return jsonify([])
    
    session = get_db_session()
    
    try:
        # Search for diseases starting with the query (case insensitive)
        diseases = session.query(Disease).filter(
            Disease.name.ilike(f'{query}%')
        ).limit(10).all()
        
        results = []
        for disease in diseases:
            results.append({
                'id': disease.id,
                'name': disease.name
            })
        
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


# ============================================================================
# Recommendation System Routes
# ============================================================================

@app.route('/recommendations', methods=['GET', 'POST'])
def recommendations():
    """Generate practice recommendations based on selected modules"""
    session = get_db_session()
    
    try:
        if request.method == 'POST':
            # Get selected modules
            major_module_id = request.form.get('major_module_id')
            comorbid_module_ids = request.form.getlist('comorbid_module_ids')
            
            if not major_module_id:
                flash('Please select a major disease module', 'error')
                return redirect(url_for('recommendations'))
            
            # Fetch modules
            major_module = session.query(Module).get(int(major_module_id))
            if not major_module:
                flash('Major disease module not found', 'error')
                return redirect(url_for('recommendations'))
            
            comorbid_modules = []
            for module_id in comorbid_module_ids:
                module = session.query(Module).get(int(module_id))
                if module:
                    comorbid_modules.append(module)
            
            # Collect all modules
            all_modules = [major_module] + comorbid_modules
            
            # Get all diseases from selected modules
            all_disease_ids = set()
            for module in all_modules:
                if module.disease_id:
                    all_disease_ids.add(module.disease_id)
            
            # Get all practices from selected modules
            all_practices = []
            for module in all_modules:
                # Force load practices
                if module.practices:
                    for practice in module.practices:
                        # Force load relationships
                        _ = practice.practice_english
                        _ = practice.practice_segment
                        _ = practice.kosha
                        _ = practice.sub_category
                        all_practices.append(practice)
            
            # Get contraindications for all diseases
            contraindications = []
            for disease_id in all_disease_ids:
                disease = session.query(Disease).get(disease_id)
                if disease:
                    for contraindication in disease.contraindications:
                        contraindications.append(contraindication)
            
            # Remove duplicates from contraindications
            seen_contraindications = set()
            unique_contraindications = []
            for contra in contraindications:
                key = (contra.practice_english, contra.practice_segment)
                if key not in seen_contraindications:
                    seen_contraindications.add(key)
                    unique_contraindications.append(contra)
            
            # Filter out contraindicated practices
            contraindicated_keys = set()
            for contra in unique_contraindications:
                contraindicated_keys.add((
                    contra.practice_english.lower().strip(),
                    contra.practice_segment
                ))
            
            filtered_practices = []
            for practice in all_practices:
                practice_key = (
                    practice.practice_english.lower().strip() if practice.practice_english else '',
                    practice.practice_segment
                )
                if practice_key not in contraindicated_keys:
                    filtered_practices.append(practice)
            
            # Get RCTs for practices
            # We need to get all RCTs and match them to practices
            all_rcts = session.query(RCT).all()
            practice_rcts = {}  # practice_id -> list of RCT parenthetical citations
            
            for practice in filtered_practices:
                practice_rcts[practice.id] = []
                practice_disease_ids = [d.id for d in practice.diseases]
                
                for rct in all_rcts:
                    rct_disease_ids = [d.id for d in rct.diseases]
                    # Check if RCT is for any of the practice's diseases
                    if any(did in practice_disease_ids for did in rct_disease_ids):
                        # Check if RCT mentions this practice
                        if rct.intervention_practices:
                            try:
                                intervention_list = json.loads(rct.intervention_practices)
                                for intervention in intervention_list:
                                    practice_name = intervention.get('name', '').strip()
                                    intervention_category = intervention.get('category', '').strip()
                                    
                                    # Match by name or category
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
            # Kosha order: Annamaya, Pranamaya, Manomaya, Vijnanamaya, Anandamaya
            kosha_order = {
                'Annamaya Kosha': 1,
                'Pranamaya Kosha': 2,
                'Manomaya Kosha': 3,
                'Vijnanamaya Kosha': 4,
                'Anandamaya Kosha': 5
            }
            
            organized_practices = {}
            for practice in filtered_practices:
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
            
            # Sort practices within each subcategory by RCT count (descending)
            for kosha in organized_practices:
                for category in organized_practices[kosha]:
                    for subcategory in organized_practices[kosha][category]:
                        organized_practices[kosha][category][subcategory].sort(
                            key=lambda x: len(x['rcts']), 
                            reverse=True
                        )
            
            # Get disease names
            major_disease_name = major_module.disease.name if major_module.disease else 'N/A'
            comorbid_disease_names = [m.disease.name if m.disease else 'N/A' for m in comorbid_modules]
            
            # Sort koshas by order (descending: highest number first)
            sorted_koshas = sorted(
                organized_practices.keys(),
                key=lambda x: kosha_order.get(x, 0),
                reverse=True
            )
            
            return render_template('recommendations_result.html',
                                 major_disease_name=major_disease_name,
                                 comorbid_disease_names=comorbid_disease_names,
                                 organized_practices=organized_practices,
                                 contraindications=unique_contraindications,
                                 kosha_order=kosha_order,
                                 sorted_koshas=sorted_koshas)
        
        # GET request - show form
        return render_template('recommendations.html')
    finally:
        session.close()


# ============================================================================
# RCT Database Routes
# ============================================================================

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
    """List all RCT entries"""
    session = get_db_session()
    try:
        rcts = session.query(RCT).order_by(RCT.id.desc()).all()
        diseases = session.query(Disease).order_by(Disease.name).all()
        practices = session.query(Practice).order_by(Practice.practice_english).all()
        return render_template('rcts.html', rcts=rcts, diseases=diseases, practices=practices)
    except Exception as e:
        flash(f'Error loading RCTs: {str(e)}', 'error')
        return render_template('rcts.html', rcts=[], diseases=[], practices=[])
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
                'sub_category': practice.sub_category or ''
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
            'Title', 'Parenthetical Citation', 'Citation Full', 'Citation Link',
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)