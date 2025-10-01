#!/usr/bin/env python3
"""
Web App for Audio Transcriber
Mobile-friendly interface for audio transcription using OpenAI Whisper
"""

import os
import tempfile
import zipfile
import threading
import time
from pathlib import Path
from flask import Flask, request, render_template, redirect, url_for, flash, send_file, jsonify, session
from werkzeug.utils import secure_filename
import uuid
from functools import wraps
from audio_transcriber import AudioTranscriber

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-change-this-in-production')

# Security settings
APP_PASSCODE = os.environ.get('APP_PASSCODE', 'transcribe2024')  # Change in production!
SESSION_TIMEOUT = 3600  # 1 hour in seconds
MAX_CONTENT_LENGTH = 150 * 1024 * 1024  # 150MB max upload

# Security headers
@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    # Don't cache sensitive pages
    if request.endpoint in ['index', 'upload_files', 'process_audio']:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

# Configuration
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'m4a', 'mp3', 'wav', 'mp4'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Set max content length for Flask
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Cleanup configuration
RESULT_RETENTION_HOURS = 24  # Keep results for 24 hours
CLEANUP_INTERVAL_MINUTES = 60  # Run cleanup every hour

def cleanup_old_files():
    """Remove old upload and result files"""
    try:
        current_time = time.time()
        retention_seconds = RESULT_RETENTION_HOURS * 3600
        
        # Clean uploads folder
        uploads_path = Path(UPLOAD_FOLDER)
        if uploads_path.exists():
            for session_dir in uploads_path.iterdir():
                if session_dir.is_dir():
                    # Check if session folder is old
                    dir_age = current_time - session_dir.stat().st_mtime
                    if dir_age > retention_seconds:
                        import shutil
                        shutil.rmtree(session_dir, ignore_errors=True)
                        print(f"🧹 Cleaned up old upload session: {session_dir.name}")
        
        # Clean results folder
        results_path = Path(RESULTS_FOLDER)
        if results_path.exists():
            for session_dir in results_path.iterdir():
                if session_dir.is_dir():
                    # Check if session folder is old
                    dir_age = current_time - session_dir.stat().st_mtime
                    if dir_age > retention_seconds:
                        import shutil
                        shutil.rmtree(session_dir, ignore_errors=True)
                        print(f"🧹 Cleaned up old result session: {session_dir.name}")
                        
        # Also clean individual old files
        for folder in [uploads_path, results_path]:
            if folder.exists():
                for file_path in folder.rglob('*'):
                    if file_path.is_file():
                        file_age = current_time - file_path.stat().st_mtime
                        if file_age > retention_seconds:
                            file_path.unlink(missing_ok=True)
                            
    except Exception as e:
        print(f"🔧 Cleanup error (non-critical): {e}")

def start_cleanup_scheduler():
    """Start background cleanup scheduler"""
    def cleanup_loop():
        while True:
            time.sleep(CLEANUP_INTERVAL_MINUTES * 60)  # Convert to seconds
            cleanup_old_files()
    
    # Run initial cleanup
    cleanup_old_files()
    
    # Start background thread
    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
    cleanup_thread.start()
    print(f"🧹 Started auto-cleanup: keeping files for {RESULT_RETENTION_HOURS}h, checking every {CLEANUP_INTERVAL_MINUTES}m")

# Start cleanup scheduler when app starts
start_cleanup_scheduler()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size_mb(file_path):
    return os.path.getsize(file_path) / (1024 * 1024)

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            flash('Please enter the passcode to access this application.', 'error')
            return redirect(url_for('login'))
        # Check session timeout
        if 'login_time' in session:
            import time
            if time.time() - session['login_time'] > SESSION_TIMEOUT:
                session.clear()
                flash('Session expired. Please log in again.', 'error')
                return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def validate_file_security(file):
    """Validate uploaded file for security"""
    if not file or file.filename == '':
        return False, "No file selected"
    
    filename = secure_filename(file.filename)
    if not filename:
        return False, "Invalid filename"
    
    # Check file extension
    if not allowed_file(filename):
        return False, f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Check file size (additional check)
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
    
    if size < 1024:  # Less than 1KB is suspicious
        return False, "File too small to be a valid audio file"
    
    return True, filename

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    import time
    
    # Rate limiting (simple implementation)
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
    current_time = time.time()
    
    # Check for brute force attempts (store in session for simplicity)
    attempts_key = f'login_attempts_{client_ip}'
    if attempts_key not in session:
        session[attempts_key] = []
    
    # Clean old attempts (older than 15 minutes)
    session[attempts_key] = [t for t in session[attempts_key] if current_time - t < 900]
    
    # Check if too many attempts
    if len(session[attempts_key]) >= 5:
        flash('Too many login attempts. Please wait 15 minutes before trying again.', 'error')
        return redirect(url_for('login'))
    
    passcode = request.form.get('passcode', '').strip()
    if not passcode:
        flash('Please enter a passcode.', 'error')
        return redirect(url_for('login'))
    
    if passcode == APP_PASSCODE:
        session['authenticated'] = True
        session['login_time'] = current_time
        session.permanent = True
        # Clear failed attempts on successful login
        if attempts_key in session:
            del session[attempts_key]
        flash('Access granted! Welcome to Audio Transcriber.', 'success')
        return redirect(url_for('index'))
    else:
        # Record failed attempt
        session[attempts_key].append(current_time)
        session.modified = True
        flash('Invalid passcode. Please try again.', 'error')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
@login_required
def upload_files():
    try:
        # Check if files were uploaded
        if 'audio_files' not in request.files:
            flash('No files selected', 'error')
            return redirect(url_for('index'))
        
        files = request.files.getlist('audio_files')
        if not files or files[0].filename == '':
            flash('No files selected', 'error')
            return redirect(url_for('index'))
        
        # Get form data
        language = request.form.get('language', 'th')
        summary_lang = request.form.get('summary_lang', 'thai')
        model = request.form.get('model', 'whisper-1')
        test_mode = request.form.get('test_mode') == 'on'
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        session_folder = Path(UPLOAD_FOLDER) / session_id
        session_folder.mkdir(exist_ok=True)
        
        # Validate and save files
        uploaded_files = []
        for file in files:
            valid, result = validate_file_security(file)
            if not valid:
                flash(f'File validation failed: {result}', 'error')
                return redirect(url_for('index'))
            
            filename = result
            file_path = session_folder / filename
            file.save(str(file_path))
            
            # Double-check file size after saving
            if get_file_size_mb(file_path) > 100:
                os.remove(file_path)  # Clean up
                flash(f'File {filename} is too large (max 100MB)', 'error')
                return redirect(url_for('index'))
            
            uploaded_files.append(file_path)
        
        if not uploaded_files:
            flash('No valid audio files uploaded', 'error')
            return redirect(url_for('index'))
        
        # Store processing parameters
        processing_data = {
            'files': [str(f) for f in uploaded_files],
            'language': language,
            'summary_lang': summary_lang,
            'model': model,
            'test_mode': test_mode,
            'session_id': session_id
        }
        
        return render_template('processing.html', 
                             session_id=session_id,
                             file_count=len(uploaded_files),
                             test_mode=test_mode,
                             processing_data=processing_data)
        
    except Exception as e:
        flash(f'Error uploading files: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/process/<session_id>')
@login_required
def process_audio(session_id):
    try:
        # Get processing parameters from request
        files = request.args.getlist('files')
        language = request.args.get('language', 'th')
        summary_lang = request.args.get('summary_lang', 'thai')
        model = request.args.get('model', 'whisper-1')
        test_mode = request.args.get('test_mode') == 'True'
        
        if not files:
            flash('No files to process', 'error')
            return redirect(url_for('index'))
        
        # Initialize transcriber
        transcriber = AudioTranscriber(test_mode=test_mode, model=model)
        
        # Create results directory for this session
        results_dir = Path(RESULTS_FOLDER) / session_id
        results_dir.mkdir(exist_ok=True)
        
        # Process files sequentially (assuming they follow the naming pattern)
        file_paths = [Path(f) for f in files]
        file_paths.sort(key=lambda x: x.name)  # Sort by filename
        
        # Process the files
        transcript = transcriber.process_sequential_files(file_paths, language)
        
        if not transcript:
            flash('No transcript generated. Please check your audio files.', 'error')
            return redirect(url_for('index'))
        
        # Generate summary
        summary = transcriber.generate_summary(transcript, summary_lang)
        
        # Save results
        prefix = f"session_{session_id[:8]}"
        if test_mode:
            prefix += "_test"
        
        transcript_file = results_dir / f"{prefix}_transcript.txt"
        summary_file = results_dir / f"{prefix}_summary.txt"
        
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(transcript)
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        return render_template('results.html',
                             session_id=session_id,
                             transcript=transcript,
                             summary=summary,
                             transcript_file=transcript_file.name,
                             summary_file=summary_file.name,
                             test_mode=test_mode)
        
    except Exception as e:
        flash(f'Error processing audio: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/download/<session_id>/<filename>')
@login_required
def download_file(session_id, filename):
    try:
        file_path = Path(RESULTS_FOLDER) / session_id / filename
        if file_path.exists():
            return send_file(str(file_path), as_attachment=True)
        else:
            flash('File not found', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/download_all/<session_id>')
@login_required
def download_all(session_id):
    try:
        results_dir = Path(RESULTS_FOLDER) / session_id
        if not results_dir.exists():
            flash('Results not found', 'error')
            return redirect(url_for('index'))
        
        # Create zip file
        zip_path = Path(RESULTS_FOLDER) / f"{session_id}_results.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file_path in results_dir.glob('*.txt'):
                zipf.write(file_path, file_path.name)
        
        return send_file(str(zip_path), as_attachment=True, download_name=f"transcription_results.zip")
        
    except Exception as e:
        flash(f'Error creating download: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/api/process', methods=['POST'])
@login_required
def api_process():
    """API endpoint for processing status"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        # This is a simple implementation
        # In production, you'd want to use background tasks (Celery, etc.)
        return jsonify({
            'status': 'processing',
            'message': 'Processing audio files...'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.before_request
def handle_root_redirect():
    """Redirect root to login if not authenticated"""
    if request.endpoint is None:
        return redirect(url_for('login'))

if __name__ == '__main__':
    # For production deployment
    port = int(os.environ.get('PORT', 5000))  # Railway uses PORT env var
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port)