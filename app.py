import os
from flask import Flask, render_template, redirect, url_for, request, session
from werkzeug.utils import secure_filename
import sqlite3

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['PROFILE_PHOTO'] = 'static/images/profile'
app.config['ITEMS']= 'static/images/items'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database connection
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    if 'username' in session:
        conn = get_db_connection()
        
        # Fetch user info
        user = conn.execute('SELECT * FROM users WHERE username = ?', (session['username'],)).fetchone()
        
        # Fetch the photos uploaded by the user (including photo_id for editing)
        photos = conn.execute('SELECT photo_id, title, genre, price, selling_img FROM photos WHERE u_id = ?', (user['user_id'],)).fetchall()
        
        conn.close()

        # Pass user and their photos to the template
        return render_template('home.html', username=user['username'], user=user, photos=photos)
    
    return redirect(url_for('login'))


@app.route('/update_bio', methods=['POST'])
def update_bio():
    if 'username' in session:
        new_bio = request.form.get('bio')  # Get the updated bio from the form
        username = session['username']

        # Update the user's bio in the database
        conn = get_db_connection()
        conn.execute('UPDATE users SET bio = ? WHERE username = ?', (new_bio, username))
        conn.commit()
        conn.close()

        # Redirect back to the home page
        return redirect(url_for('home'))

    return redirect(url_for('login'))

@app.route('/update_photo/<int:photo_id>', methods=['POST'])
def update_photo(photo_id):
    if 'username' in session:
        title = request.form.get('title')
        genre = request.form.get('genre')
        price = request.form.get('price')

        # Update the photo details in the database
        conn = get_db_connection()
        conn.execute('''
            UPDATE photos
            SET title = ?, genre = ?, price = ?
            WHERE photo_id = ? AND u_id = ?
        ''', (title, genre, price, photo_id, session['user_id']))
        conn.commit()
        conn.close()

        return redirect(url_for('home'))

    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        # Fetch user details, including user_id (typically it's the id from users table)
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()

        if user:
            # Set the username and user_id in the session after successful login
            session['username'] = user['username']
            session['user_id'] = user['user_id']  # Ensure 'id' is the correct field for user_id
            return redirect(url_for('home'))
        else:
            return 'Invalid credentials'
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        profile_pic = request.files['profile_pic']
        
        if profile_pic and allowed_file(profile_pic.filename):
            filename = secure_filename(profile_pic.filename)
            profile_pic.save(os.path.join(app.config['PROFILE_PHOTO'], filename))
            
            # Save user info in the database, including profile picture filename
            conn = get_db_connection()
            conn.execute('INSERT INTO users (username, email, password, profile_pic) VALUES (?, ?, ?, ?)',(username, email, password, filename))
            conn.commit()
            conn.close()
            
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/buy')
def buy():
    # Define the list of genres
    genres = [
        "Abstract Photography", "Aerial Photography", "Architectural Photography", "Astrophotography",
        "Black and White Photography", "Conceptual Photography", "Documentary Photography",
        "Editorial Photography", "Event Photography", "Fashion Photography", "Fine Art Photography",
        "Food Photography", "Geometric Photography", "High-Key Photography", "Landscape Photography",
        "Long Exposure Photography", "Low-Key Photography", "Macro Photography", "Minimalist Photography",
        "Monochrome Photography", "Negative Space Photography", "Portrait Photography", "Product Photography",
        "Reflections Photography", "Shadow Photography", "Silhouette Photography", "Sports Photography",
        "Still Life Photography", "Street Photography", "Symmetry Photography", "Texture Photography",
        "Travel Photography", "Underwater Photography", "Wildlife Photography"
    ]

    conn = get_db_connection()

    # Get the filter inputs from the request
    search_term = request.args.get('search')
    selected_genre = request.args.get('genre')
    selected_price = request.args.get('price')

    # Base query
    query = '''
        SELECT photos.*, users.username AS uploader_name
        FROM photos
        JOIN users ON photos.u_id = users.user_id
        WHERE photos.sold = 0
    '''
    params = []

    # Apply search filter
    if search_term:
        query += ' AND (photos.title LIKE ? OR users.username LIKE ?)'
        params.extend([f'%{search_term}%', f'%{search_term}%'])

    # Apply genre filter
    if selected_genre:
        query += ' AND photos.genre = ?'
        params.append(selected_genre)

    # Apply the price filter (for sorting)
    if selected_price == 'low':
        query += ' ORDER BY photos.price ASC'
    elif selected_price == 'high':
        query += ' ORDER BY photos.price DESC'

    # Execute the query
    photos = conn.execute(query, params).fetchall()
    conn.close()

    # Pass genres and photos to the template
    return render_template('buy.html', photos=photos, genres=genres)

@app.route('/sell', methods=['GET', 'POST'])
def sell():
    if request.method == 'POST':
        title = request.form['title']
        genre = request.form['genre']
        price = request.form['price']
        selling_img = request.files.get('image')
        
        if selling_img and allowed_file(selling_img.filename):
            filename = secure_filename(selling_img.filename)
            selling_img.save(os.path.join(app.config['ITEMS'], filename))

            # Get the logged-in user's user_id from session
            u_id = session['user_id']
            
            # Store image info along with uploader's username
            conn = get_db_connection()
            conn.execute('INSERT INTO photos (title, genre, price, selling_img, u_id, sold) VALUES (?, ?, ?, ?, ?, 0)', 
                         (title, genre, price, filename, u_id))
            conn.commit()
            conn.close()
            
            return redirect(url_for('home'))

    return render_template('sell.html')

if __name__ == '__main__':
    app.run(debug=True)
