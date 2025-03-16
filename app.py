import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import threading

from config import (
    SECRET_KEY, UPLOAD_FOLDER, ALLOWED_EXTENSIONS, 
    MAX_CONTENT_LENGTH
)
from database import (
    initialize_db, save_document_metadata, get_all_documents,
    get_document_data, redis_client
)
from pdf_processor import process_pdf

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Initialize database on startup
with app.app_context():
    initialize_db()

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    success = None
    document_id = None
    
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'pdf_file' not in request.files:
            error = 'No file part'
        else:
            file = request.files['pdf_file']
            
            if file.filename == '':
                error = 'No file selected'
            elif not allowed_file(file.filename):
                error = 'Only PDF files are allowed'
            else:
                try:
                    # Secure filename and create a unique name
                    original_filename = secure_filename(file.filename)
                    filename = f"{uuid.uuid4()}_{original_filename}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    
                    # Save the file temporarily
                    file.save(filepath)
                    
                    # Save document metadata and get ID
                    document_id = save_document_metadata(original_filename)
                    
                    # Process the PDF in a background thread
                    thread = threading.Thread(
                        target=process_pdf,
                        args=(filepath, document_id)
                    )
                    thread.daemon = True
                    thread.start()
                    
                    success = f"PDF uploaded successfully. Processing started."
                except Exception as e:
                    error = f"Error uploading file: {str(e)}"
    
    # Get all documents for the list
    documents = get_all_documents()
    
    return render_template(
        'index.html', 
        error=error, 
        success=success, 
        documents=documents,
        document_id=document_id
    )

@app.route('/results/<int:document_id>')
def results(document_id):
    # Get document data from database
    data = get_document_data(document_id)
    
    if not data or not data['document'] or data['document']['status'] != 'complete':
        return render_template('results.html', data=None)
    
    # Extract unique entity types for filtering
    entity_types = set()
    for entity in data['entities']:
        entity_types.add(entity['entity_type'])
    
    # Calculate statistics for each entity type
    entity_stats = []
    type_counts = {}
    type_confidences = {}
    
    for entity in data['entities']:
        entity_type = entity['entity_type']
        
        if entity_type not in type_counts:
            type_counts[entity_type] = 0
            type_confidences[entity_type] = 0
        
        type_counts[entity_type] += 1
        type_confidences[entity_type] += entity['confidence']
    
    for entity_type, count in type_counts.items():
        entity_stats.append({
            'type': entity_type,
            'count': count,
            'avg_confidence': type_confidences[entity_type] / count
        })
    
    # Sort stats by count (descending)
    entity_stats.sort(key=lambda x: x['count'], reverse=True)
    
    return render_template(
        'results.html',
        data=data,
        entity_types=sorted(entity_types),
        entity_stats=entity_stats
    )

@app.route('/progress/<int:document_id>')
def progress(document_id):
    """API endpoint to get the progress of PDF processing"""
    if redis_client:
        progress = redis_client.get(f"pdf_progress:{document_id}")
        if progress:
            return {'progress': int(progress)}
    return {'progress': 0}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)