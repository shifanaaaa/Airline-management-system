from flask import Flask, request, render_template, redirect, session, flash, url_for
import mysql.connector
import hashlib
import os
import time
import random
from datetime import datetime


app = Flask(__name__)
app.secret_key = "secrets"

db = mysql.connector.connect(
    host='localhost',
    user='root',
    password='shifana123',
    # password=os.getenv("DB_PASSWORD"),
    database='mydbs'
)
cursor = db.cursor(dictionary=True)

# ---------- Helpers ----------
def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_ticket_code() -> str:
    return f"TKT{int(time.time())}{random.randint(100,999)}"

def require_admin():
    if not session.get('admin_logged_in'):
        flash("Admin login required")
        return False
    return True

def require_user():
    if 'cust_id' not in session:
        flash("Please login first")
        return False
    return True
@app.template_filter('datetime_local')
def datetime_local(value):
    """
    Converts a datetime object to a string usable in <input type="datetime-local">
    Format: YYYY-MM-DDTHH:MM
    """
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%dT%H:%M')
    return value  # fallback
#home
@app.route('/')
def home():
    return render_template('index.html')

#admin
@app.route('/admin_login_page')
def admin_login_page():
    return render_template('admin_login.html')

@app.route('/admin_login', methods=['POST'])
def admin_login():
    username = request.form['username']
    password = request.form['password']
    cursor.execute("SELECT * FROM Admin WHERE username = %s AND password = %s", (username, password))
    admin = cursor.fetchone()
    if admin:
        session['admin_logged_in'] = True
        session['admin_username'] = username
        return redirect('/admin_dashboard')
    else:
        flash("Invalid admin credentials")
        return redirect('/admin_login_page')

@app.route('/admin_dashboard')
def admin_dashboard():
    if not require_admin():
        return redirect('/admin_login_page')
    cursor.execute("SELECT COUNT(*) AS total_flights FROM Flight")
    flights_count = cursor.fetchone()['total_flights']
    cursor.execute("SELECT COUNT(*) AS total_customers FROM Customer")
    customers_count = cursor.fetchone()['total_customers']
    cursor.execute("SELECT COUNT(*) AS total_tickets FROM Ticket")
    tickets_count = cursor.fetchone()['total_tickets']
    return render_template('admin_dashboard.html',
                           total_flights=flights_count,
                           total_customers=customers_count,
                           total_tickets=tickets_count)



@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

#customer
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form.get('phone', '')
        address = request.form.get('address', '')
        try:
            cursor.execute("INSERT INTO Customer (name, email, password, phone, address) VALUES (%s,%s,%s,%s,%s)",
                           (name, email, password, phone, address))
            db.commit()
            flash("Registration successful. Please login.")
            return redirect('/customer_login')
        except mysql.connector.Error as err:
            return f"Error: {err}"
    return render_template('register.html')

@app.route('/customer_login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cursor.execute("SELECT * FROM Customer WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        if user:
            session['user_name'] = user['name']
            session['cust_id'] = user['customer_id']
            flash("Logged in")
            return redirect('/customer_dashboard')
        else:
            flash("Invalid login credentials")
            return redirect('/customer_login')
    return render_template('customer_login.html')

@app.route('/customer_dashboard')
def customer_dashboard():
    if not require_user():
        return redirect('/customer_login')
    
    cust_id = session['cust_id']
    
    # Total tickets booked by the user
    cursor.execute("SELECT COUNT(*) AS total FROM Ticket WHERE customer_id = %s", (cust_id,))
    total_tickets = cursor.fetchone()['total']

    # Upcoming flights (future departure) for this user
    cursor.execute("""
        SELECT COUNT(*) AS upcoming
        FROM Ticket t
        JOIN Flight f ON t.flight_id = f.flight_id
        WHERE t.customer_id = %s AND f.departure_time > NOW() AND t.status = 'Booked'
    """, (cust_id,))
    upcoming_flights = cursor.fetchone()['upcoming']

    return render_template(
        'customer_dashboard.html',
        user_name=session.get('user_name'),
        total_tickets=total_tickets,
        upcoming_flights=upcoming_flights
    )


#flight
@app.route('/flights')
def show_flights():
    cursor.execute("SELECT * FROM Flight ORDER BY departure_time ASC")
    flights = cursor.fetchall()
    return render_template('flights.html', flights=flights)
# flight
# ... (other flight routes)

@app.route('/add_flight', methods=['GET', 'POST'])
def add_flight():
    if not require_admin():
        return redirect('/admin_login_page')
    if request.method == 'POST':
        # ... (flight data extraction remains the same)
        flight_name = request.form['flight_name']
        source = request.form['source']
        destination = request.form['destination']
        departure_time = request.form['departure_time']
        arrival_time = request.form['arrival_time']
        total_seats = int(request.form['total_seats'])
        fare = float(request.form['fare'])
        try:
            # 1. Insert Flight Record
            cursor.execute("""
                INSERT INTO Flight (flight_name, source, destination, departure_time, arrival_time, total_seats, available_seats, fare)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (flight_name, source, destination, departure_time, arrival_time, total_seats, total_seats, fare))
            db.commit()
            flight_id = cursor.lastrowid

            # 2. SEAT GENERATION LOGIC (Corrected)
            letters = ['A', 'B', 'C', 'D', 'E', 'F']
            seats_to_insert = []
            
            # Determine the number of rows needed (rounded up)
            num_rows = (total_seats + len(letters) - 1) // len(letters) # Equivalent to math.ceil(total_seats / 6)

            for seat_index in range(total_seats):
                # Calculate the row number (1-indexed)
                row_num = (seat_index // len(letters)) + 1
                # Calculate the column letter
                letter = letters[seat_index % len(letters)]
                
                seat_no = f"{letter}{row_num}"
                seats_to_insert.append((flight_id, seat_no))

            # Batch insert seats
            seat_insert_query = "INSERT INTO Seat (flight_id, seat_no) VALUES (%s, %s)"
            cursor.executemany(seat_insert_query, seats_to_insert)
            
            db.commit()
            flash("Flight added and seats generated")
            return redirect('/flights')
        except mysql.connector.Error as err:
            # IMPORTANT: Rollback if seat insertion fails
            db.rollback() 
            return f"Error: {err}"
    return render_template('add_flight.html')

@app.route('/update_flight/<int:flight_id>', methods=['GET', 'POST'])
def update_flight(flight_id):
    if not require_admin():
        return redirect('/admin_login_page')
    cursor.execute("SELECT * FROM Flight WHERE flight_id = %s", (flight_id,))
    flight = cursor.fetchone()
    if not flight:
        flash("Flight not found")
        return redirect('/flights')
    if request.method == 'POST':
        flight_name = request.form['flight_name']
        source = request.form['source']
        destination = request.form['destination']
        departure_time = request.form['departure_time']
        arrival_time = request.form['arrival_time']
        total_seats = int(request.form['total_seats'])
        fare = float(request.form['fare'])
        status = request.form.get('status', 'Scheduled')
        try:
            
            cursor.execute("""
                UPDATE Flight SET flight_name=%s, source=%s, destination=%s,
                                  departure_time=%s, arrival_time=%s, total_seats=%s, fare=%s, status=%s
                WHERE flight_id=%s
            """, (flight_name, source, destination, departure_time, arrival_time, total_seats, fare, status, flight_id))
            
            cursor.execute("SELECT COUNT(*) AS booked FROM Ticket WHERE flight_id = %s AND status = 'Booked'", (flight_id,))
            booked = cursor.fetchone()['booked']
            available = max(0, total_seats - booked)
            cursor.execute("UPDATE Flight SET available_seats = %s WHERE flight_id = %s", (available, flight_id))
            db.commit()
            flash("Flight updated")
            return redirect('/flights')
        except mysql.connector.Error as err:
            return f"Error: {err}"
    return render_template('update_flight.html', flight=flight)

@app.route('/delete_flight/<int:flight_id>', methods=['POST'])
def delete_flight(flight_id):
    if not require_admin():
        return redirect('/admin_login_page')
    try:
        
        cursor.execute("DELETE FROM Seat WHERE flight_id = %s", (flight_id,))
        cursor.execute("DELETE FROM Ticket WHERE flight_id = %s", (flight_id,))
        cursor.execute("DELETE FROM Flight WHERE flight_id = %s", (flight_id,))
        db.commit()
        flash("Flight deleted")
        return redirect('/flights')
    except mysql.connector.Error as err:
        return f"Error: {err}"

#search flight
@app.route('/search_flights', methods=['GET', 'POST'])
def search_flights():
    if request.method == 'POST':
        source = request.form.get('source')
        destination = request.form.get('destination')
        date = request.form.get('date')
        query = """
            SELECT * FROM Flight
            WHERE source = %s AND destination = %s
              AND DATE(departure_time) = %s
              AND status = 'Scheduled' AND available_seats > 0
            ORDER BY departure_time
        """
        cursor.execute(query, (source, destination, date))
        flights = cursor.fetchall()
        return render_template('search_results.html', flights=flights)
    return render_template('search_flights.html')

# ---------- FLIGHT SCHEDULE ----------
@app.route('/flight_schedule')
def flight_schedule():
    cursor.execute("""
        SELECT flight_id, flight_name, source, destination,
               DATE(departure_time) AS date,
               TIME(departure_time) AS dep_time,
               TIME(arrival_time) AS arr_time,
               status, available_seats, fare
        FROM Flight
        ORDER BY departure_time ASC
    """)
    schedule = cursor.fetchall()
    return render_template('flight_schedule.html', schedule=schedule)

#seat map and booking
@app.route('/select_seat/<int:flight_id>', methods=['GET', 'POST'])
def select_seat(flight_id):
    
    cursor.execute("SELECT * FROM Flight WHERE flight_id = %s", (flight_id,))
    flight = cursor.fetchone()
    if not flight:
        flash("Flight not found")
        return redirect('/search_flights')

    if request.method == 'POST':
        if not require_user():
            return redirect('/customer_login')
        seat_no = request.form['selected_seat']
        travel_class = request.form.get('class', 'Economy')
        cust_id = session['cust_id']
        cursor.execute("SELECT * FROM Seat WHERE flight_id = %s AND seat_no = %s FOR UPDATE", (flight_id, seat_no))
        seat = cursor.fetchone()
        if not seat:
            flash("Selected seat not found")
            return redirect(url_for('select_seat', flight_id=flight_id))
        if seat['is_booked']:
            flash("Seat already booked. Please choose another.")
            return redirect(url_for('select_seat', flight_id=flight_id))
        try:
            cursor.execute("UPDATE Seat SET is_booked = TRUE WHERE seat_id = %s", (seat['seat_id'],))
            # Create ticket
            ticket_code = generate_ticket_code()
            cursor.execute("""
                INSERT INTO Ticket (ticket_code, customer_id, flight_id, seat_no, class, status)
                VALUES (%s, %s, %s, %s, %s, 'Booked')
            """, (ticket_code, cust_id, flight_id, seat_no, travel_class))
            
            cursor.execute("UPDATE Flight SET available_seats = available_seats - 1 WHERE flight_id = %s", (flight_id,))
            db.commit()
            flash("Booking successful. Ticket code: " + ticket_code)
            return redirect('/my_tickets')
        except mysql.connector.Error as err:
            db.rollback()
            return f"Error: {err}"

    cursor.execute("SELECT seat_no, is_booked FROM Seat WHERE flight_id = %s ORDER BY seat_no", (flight_id,))
    seats = cursor.fetchall()
    return render_template('seat_selection.html', seats=seats, flight=flight)

#ticket
@app.route('/my_tickets')
def my_tickets():
    if not require_user():
        return redirect('/customer_login')
    cust_id = session['cust_id']
    cursor.execute("""
        SELECT t.ticket_id, t.ticket_code, t.flight_id, t.seat_no, t.class, t.booking_date, t.status,
               f.flight_name, f.source, f.destination, f.departure_time, f.arrival_time, f.fare
        FROM Ticket t
        JOIN Flight f ON t.flight_id = f.flight_id
        WHERE t.customer_id = %s
        ORDER BY t.booking_date DESC
    """, (cust_id,))
    tickets = cursor.fetchall()
    return render_template('tickets.html', tickets=tickets)

@app.route('/cancel_ticket/<int:ticket_id>', methods=['POST'])
def cancel_ticket(ticket_id):
    if not require_user():
        return redirect('/customer_login')
    cust_id = session['cust_id']
    cursor.execute("SELECT * FROM Ticket WHERE ticket_id = %s AND customer_id = %s", (ticket_id, cust_id))
    ticket = cursor.fetchone()
    if not ticket:
        flash("Ticket not found or unauthorized")
        return redirect('/my_tickets')
    if ticket['status'] == 'Cancelled':
        flash("Ticket already cancelled")
        return redirect('/my_tickets')
    try:
        cursor.execute("UPDATE Ticket SET status = 'Cancelled' WHERE ticket_id = %s", (ticket_id,))
        cursor.execute("UPDATE Seat SET is_booked = FALSE WHERE flight_id = %s AND seat_no = %s",
                       (ticket['flight_id'], ticket['seat_no']))
        
        cursor.execute("UPDATE Flight SET available_seats = available_seats + 1 WHERE flight_id = %s", (ticket['flight_id'],))
        db.commit()
        flash("Ticket cancelled")
    except mysql.connector.Error as err:
        db.rollback()
        return f"Error: {err}"
    return redirect('/my_tickets')

# admin view
@app.route('/admin_tickets')
def admin_tickets():
    if not require_admin():
        return redirect('/admin_login_page')
    cursor.execute("""
        SELECT t.ticket_id, t.ticket_code, t.status, t.booking_date, t.seat_no, t.class,
               c.name AS customer_name, f.flight_name, f.source, f.destination, f.departure_time
        FROM Ticket t
        JOIN Customer c ON t.customer_id = c.customer_id
        JOIN Flight f ON t.flight_id = f.flight_id
        ORDER BY t.booking_date DESC
    """)
    tickets = cursor.fetchall()
    return render_template('admin_tickets.html', tickets=tickets)

@app.route('/admin_cancel_ticket/<int:ticket_id>', methods=['POST'])
def admin_cancel_ticket(ticket_id):
    if not require_admin():
        return redirect('/admin_login_page')
    cursor.execute("SELECT * FROM Ticket WHERE ticket_id = %s", (ticket_id,))
    ticket = cursor.fetchone()
    if not ticket:
        flash("Ticket not found")
        return redirect('/admin_tickets')
    if ticket['status'] == 'Cancelled':
        flash("Ticket already cancelled")
        return redirect('/admin_tickets')
    try:
        cursor.execute("UPDATE Ticket SET status = 'Cancelled' WHERE ticket_id = %s", (ticket_id,))
        cursor.execute("UPDATE Seat SET is_booked = FALSE WHERE flight_id = %s AND seat_no = %s",
                       (ticket['flight_id'], ticket['seat_no']))
        cursor.execute("UPDATE Flight SET available_seats = available_seats + 1 WHERE flight_id = %s", (ticket['flight_id'],))
        db.commit()
        flash("Ticket cancelled by admin")
    except mysql.connector.Error as err:
        db.rollback()
        return f"Error: {err}"
    return redirect('/admin_tickets')

#list customer
@app.route('/customers')
def show_customers():
    if not require_admin():
        return redirect('/admin_login_page')
    cursor.execute("SELECT * FROM Customer")
    customers = cursor.fetchall()
    return render_template("customers.html", customers=customers)

#run
if __name__ == "__main__":
    app.run(debug=True)
