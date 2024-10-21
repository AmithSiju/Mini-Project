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
        user = conn.execute('SELECT * FROM users WHERE username = ?', (session['username'],)).fetchone()
        conn.close()
        return render_template('home.html', username=user['username'], user=user)
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
    conn = get_db_connection()
    photos = conn.execute('''
        SELECT photos.*, users.username AS uploader_name
        FROM photos
        JOIN users ON photos.u_id = users.user_id
        WHERE photos.sold = 0
    ''').fetchall()
    conn.close()
    return render_template('buy.html', photos=photos)

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
