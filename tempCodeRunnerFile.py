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
    
    # Sort the genres alphabetically
    genres.sort()

    conn = get_db_connection()
    photos = conn.execute('''
        SELECT photos.*, users.username AS uploader_name
        FROM photos
        JOIN users ON photos.u_id = users.user_id
        WHERE photos.sold = 0
    ''').fetchall()
    conn.close()
    return render_template('buy.html', photos=photos, genres=genres)
