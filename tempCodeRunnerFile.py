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