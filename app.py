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
    if 'user_id' in session:
        user_id = session['user_id']
        conn = get_db_connection()
        
        # Fetch user information
        user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
        
        # Fetch uploaded photos by the user
        photos = conn.execute('SELECT * FROM photos WHERE u_id = ?', (user_id,)).fetchall()
        
        # Fetch purchased items for the user
        purchased_items = conn.execute('''
            SELECT photos.title, photos.genre, photos.selling_img, purchases.price, purchases.purchase_date
            FROM purchases
            JOIN photos ON purchases.photo_id = photos.photo_id
            WHERE purchases.user_id = ?
            ORDER BY purchases.purchase_date DESC
        ''', (user_id,)).fetchall()

        # Fetch items uploaded by the user with purchaser information
        sold_items = conn.execute('''
            SELECT photos.title, photos.selling_img, users.username AS purchaser_name, purchases.purchase_date
            FROM photos
            JOIN purchases ON photos.photo_id = purchases.photo_id
            JOIN users ON purchases.user_id = users.user_id
            WHERE photos.u_id = ?
            ORDER BY purchases.purchase_date DESC
        ''', (user_id,)).fetchall()
        
        conn.close()
        
        # Render the home page with user info, uploaded photos, purchased items, and sold items
        return render_template(
            'home.html', 
            username=user['username'], 
            user=user, 
            photos=photos, 
            purchased_items=purchased_items, 
            sold_items=sold_items
        )
    
    return redirect(url_for('login'))



import os
from werkzeug.utils import secure_filename

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_connection()

    # Retrieve form data
    new_username = request.form.get('username')
    new_bio = request.form.get('bio')
    profile_pic = request.files.get('profile_pic')
    
    # Update username and bio
    conn.execute(
        'UPDATE users SET username = ?, bio = ? WHERE user_id = ?',
        (new_username, new_bio, user_id)
    )
    
    # Update profile picture if a new one is provided
    if profile_pic:
        # Secure the filename and save the image to the profile images directory
        filename = secure_filename(profile_pic.filename)
        profile_pic_path = os.path.join('static/images/profile', filename)
        profile_pic.save(profile_pic_path)
        
        # Update the user's profile picture path in the database
        conn.execute(
            'UPDATE users SET profile_pic = ? WHERE user_id = ?',
            (filename, user_id)
        )
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('home'))

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

@app.route('/delete_photo/<int:photo_id>', methods=['POST'])
def delete_photo(photo_id):
    if 'username' in session:
        conn = get_db_connection()
        
        # Delete the photo only if it belongs to the logged-in user
        conn.execute('DELETE FROM photos WHERE photo_id = ? AND u_id = ?', (photo_id, session['user_id']))
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

@app.route('/view_user_profile/<int:user_id>')
def view_user_profile(user_id):
    conn = get_db_connection()
    
    # Fetch user information based on user_id
    user = conn.execute('SELECT username, bio, profile_pic FROM users WHERE user_id = ?', (user_id,)).fetchone()
    
    # Fetch the photos uploaded by this user
    photos = conn.execute('SELECT title, genre, price, selling_img FROM photos WHERE u_id = ?', (user_id,)).fetchall()
    
    conn.close()
    
    # If the user does not exist, redirect to the home page or show an error
    if user is None:
        return redirect(url_for('home'))
    
    # Render the profile in view-only mode
    return render_template('view_user_profile.html', user=user, photos=photos)

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


from datetime import datetime

@app.route('/payment/<int:photo_id>', methods=['GET', 'POST'])
def payment_page(photo_id):
    if 'user_id' in session:
        conn = get_db_connection()
        
        # Fetch item details along with the uploader's name
        photo = conn.execute('''
            SELECT photos.*, users.username AS uploader_name
            FROM photos
            JOIN users ON photos.u_id = users.user_id
            WHERE photos.photo_id = ?
        ''', (photo_id,)).fetchone()
        
        if request.method == 'POST':
            # Retrieve form data
            payment_method = request.form.get('payment_method')
            
            # Insert the purchase record into the purchases table, including the payment method and date
            conn.execute(
                'INSERT INTO purchases (user_id, photo_id, price, payment_method, purchase_date) VALUES (?, ?, ?, ?, ?)',
                (session['user_id'], photo_id, photo['price'], payment_method, datetime.now())
            )
            
            # Mark the item as sold in the photos table
            conn.execute('UPDATE photos SET sold = 1 WHERE photo_id = ?', (photo_id,))
            conn.commit()
            conn.close()
            
            # Redirect to the success page
            return redirect(url_for('transaction_success'))

        conn.close()
        
        # Render the payment page with item and uploader information
        return render_template('payment.html', photo=photo)
    
    return redirect(url_for('login'))


@app.route('/transaction_success')
def transaction_success():
    return render_template('transaction_success.html')


if __name__ == '__main__':
    app.run(debug=True)
