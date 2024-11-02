from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import sqlite3
from datetime import datetime
from appam_analyzer import count_holes
import secrets


app = Flask(__name__)


app.secret_key = secrets.token_hex(16)


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def init_db():
    conn = sqlite3.connect('appam.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            hole_count INTEGER NOT NULL,
            image_path TEXT NOT NULL,
            steps_path TEXT NOT NULL,
            final_path TEXT NOT NULL,
            submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_leaderboard():
    conn = sqlite3.connect('appam.db')
    c = conn.cursor()
    c.execute('''
        SELECT name, hole_count, image_path, final_path, submission_date 
        FROM submissions 
        ORDER BY hole_count DESC, submission_date DESC
        LIMIT 10
    ''')
    leaders = c.fetchall()
    conn.close()
    return leaders

@app.template_filter('format_date')
def format_date(date_str):
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        return date_obj.strftime('%Y-%m-%d %H:%M')
    except:
        return date_str

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        
        if 'name' not in request.form:
            flash('Please enter your name', 'error')
            return redirect(request.url)
        
        name = request.form['name'].strip()
        if not name:
            flash('Please enter your name', 'error')
            return redirect(request.url)
        
        
        if 'file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            try:
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = secure_filename(f"{timestamp}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                
                num_holes, steps_path, final_path = count_holes(filepath)
                
                
                steps_rel_path = os.path.relpath(steps_path, 'static')
                final_rel_path = os.path.relpath(final_path, 'static')
                image_rel_path = os.path.relpath(filepath, 'static')
                
               
                conn = sqlite3.connect('appam.db')
                c = conn.cursor()
                c.execute('''
                    INSERT INTO submissions 
                    (name, hole_count, image_path, steps_path, final_path)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, num_holes, image_rel_path, steps_rel_path, final_rel_path))
                conn.commit()
                conn.close()
                
                flash(f'Success! Found {num_holes} holes in your appam!', 'success')
                
                return redirect(url_for('index', 
                                      last_analysis=final_rel_path,
                                      last_steps=steps_rel_path,
                                      last_holes=num_holes))
                
            except Exception as e:
                flash(f'Error processing image: {str(e)}', 'error')
                return redirect(url_for('index'))
            
        else:
            flash('Invalid file type. Please upload a PNG or JPEG image.', 'error')
            return redirect(request.url)
    
    
    leaderboard = get_leaderboard()
    
    
    last_analysis = request.args.get('last_analysis')
    last_steps = request.args.get('last_steps')
    last_holes = request.args.get('last_holes')
    
    return render_template('index.html', 
                         leaderboard=leaderboard,
                         last_analysis=last_analysis,
                         last_steps=last_steps,
                         last_holes=last_holes)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)