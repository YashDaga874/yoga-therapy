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
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from database.models import (
    Disease, Practice, Citation, Contraindication, DiseaseCombination, Module,
    create_database, get_session, disease_contraindication_association
)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

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
    citation_count = session.query(Citation).count()
    contraindication_count = session.query(Contraindication).count()
    
    session.close()
    
    return render_template('index.html',
                         disease_count=disease_count,
                         practice_count=practice_count,
                         citation_count=citation_count,
                         contraindication_count=contraindication_count)


@app.route('/diseases')
def list_diseases():
    """List all diseases"""
    session = get_db_session()
    try:
        diseases = session.query(Disease).all()
        # Force load the practices relationship before closing session
        for disease in diseases:
            _ = len(disease.practices)  # This loads the relationship
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
    """View a specific disease and its practices"""
    session = get_db_session()
    
    try:
        disease = session.query(Disease).get(disease_id)
        
        if not disease:
            flash('Disease not found', 'error')
            return redirect(url_for('list_diseases'))
        
        # Get module info
        module = session.query(Module).filter_by(disease_id=disease_id).first()
        
        # Organize practices by segment and force load relationships
        practices_by_segment = {}
        for practice in disease.practices:
            if practice.practice_segment not in practices_by_segment:
                practices_by_segment[practice.practice_segment] = []
            practices_by_segment[practice.practice_segment].append(practice)
            # Force load citation
            if practice.citation:
                _ = practice.citation.citation_text
        
        # Get contraindications for this disease
        # Contraindications are now directly linked to individual diseases
        contraindications = disease.contraindications
        
        return render_template('view_disease.html',
                             disease=disease,
                             module=module,
                             practices_by_segment=practices_by_segment,
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
    """List all practices"""
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
            if practice.citation:
                _ = practice.citation.citation_text  # Load citation
        
        # Get all unique segments for filter dropdown
        all_segments = session.query(Practice.practice_segment).distinct().all()
        segments = [s[0] for s in all_segments]
        
        return render_template('practices.html',
                             practices=practices,
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
        
        # Link to diseases
        disease_ids = request.form.getlist('diseases')
        for disease_id in disease_ids:
            disease = session.query(Disease).get(int(disease_id))
            if disease:
                practice.diseases.append(disease)
        
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
            
            # Update disease associations
            practice.diseases = []
            disease_ids = request.form.getlist('diseases')
            for disease_id in disease_ids:
                disease = session.query(Disease).get(int(disease_id))
                if disease:
                    practice.diseases.append(disease)
            
            # Store the practice name before closing session
            practice_name = practice.practice_english
            
            session.commit()
            session.close()
            
            flash(f'Practice "{practice_name}" updated successfully!', 'success')
            return redirect(url_for('list_practices'))
        
        # GET request
        diseases = session.query(Disease).all()
        return render_template('edit_practice.html', practice=practice, diseases=diseases)
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
            reason=request.form.get('reason', '')
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
    Query parameter: q (search query)
    Returns list of matching practices with all details
    """
    query = request.args.get('q', '')
    
    if not query:
        return jsonify([])
    
    session = get_db_session()
    
    try:
        # Search for practices starting with the query (case insensitive)
        practices = session.query(Practice).filter(
            Practice.practice_sanskrit.ilike(f'{query}%')
        ).limit(10).all()
        
        results = []
        for practice in practices:
            results.append({
                'id': practice.id,
                'practice_sanskrit': practice.practice_sanskrit or '',
                'practice_english': practice.practice_english,
                'practice_segment': practice.practice_segment,
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)