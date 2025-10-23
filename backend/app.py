from flask import Flask,request,render_template,redirect,session,jsonify
from flask_cors import CORS
import mysql.connector
import hashlib
import os
from dotenv import load_dotenv 

load_dotenv()
app=Flask(__name__)
CORS(app) #Enabling the cors

app.secret_key=os.getenv("SECRET_KEY")
db=mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)
cursor=db.cursor(dictionary=True)

#Home
@app.route('/')
def home():
    return jsonify({"message":"Welcome to the flight booking API"}),200

#user login
@app.route('/user_login',methods=['POST'])
def user_login():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid JSON data"}), 400
        
    username = data.get('username')
    password = data.get('password')
    
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute("select id from users where username = %s and password = %s", (username, hashed_pw))
    user = cursor.fetchone()

    if user:
        session['user_id'] = user['id']
        return jsonify({"message": "Login successful", "user_id": user['id']}), 200
    else:
        return jsonify({"message": "Invalid username or password. Try again!"}), 401
    

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' in session:
        return jsonify({"message": "Access granted"}), 200
    else:
        return jsonify({"message": "Unauthorized access."}), 401
    
@app.route('/admins', methods=['GET'])
def show_admins_api():
    cursor.execute("SELECT Admin_Id, Username, Email, Phone_No FROM Admin")
    admins = cursor.fetchall()
    admin_list = [
        {"id": a['Admin_Id'], "username": a['Username'], "email": a['Email'], "phoneNo": a['Phone_No']}
        for a in admins
    ]
    return jsonify(admin_list)
@app.route('/admins', methods=['POST'])
def add_admin_api():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid JSON data"}), 400        
    username = data.get('username')
    password = data.get('password')
    email = data.get('email', '')
    phone = data.get('phoneNo', '')
    
    if not username or not password:
        return jsonify({"message": "Error: Username and Password are required."}), 400

    try:
        hashed_pass = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("""
            INSERT INTO Admin (Username, Password, Email, Phone_No)
            VALUES (%s, %s, %s, %s)
        """, (username, hashed_pass, email, phone))
        db.commit()
        return jsonify({"message": "Admin added successfully", "id": cursor.lastrowid}), 201
    except mysql.connector.Error as err:
        db.rollback()
        return jsonify({"message": f"Database Error: {err}"}), 500
#Admin login and logout
@app.route('/admin_login', methods=['POST'])
def admin_login_api():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid JSON data"}), 400

    username = data.get('username')
    password = data.get('password')
    
    hashed_pass = hashlib.sha256(password.encode()).hexdigest()

    cursor.execute("SELECT * FROM Admin WHERE Username=%s AND Password=%s", 
                   (username, hashed_pass))
    admin = cursor.fetchone()
    if admin:
        session['admin'] = admin['Admin_Id']
        return jsonify({"message": "Admin login successful", "admin_id": admin['Admin_Id']}), 200
    else:
        return jsonify({"message": "Invalid username or password"}), 401

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)
    return jsonify({"message": "Logged out successfully"}), 200


#Customer
@app.route('/customers',methods=['GET'])
def show_customers_api():
    cursor.execute("select * from Customer")
    customers=cursor.fetchall()
    customer_list=[
        {
            "id": c['Custid'],
            "firstName": c['First_Name'],
            "lastName": c['Last_name'],
            "email": c['Email_Address'],
            "tel": c['Tel_No'],
            "nationality": c['Nationality'],
            "residence": c['Residence'],
        }
        for c in customers
    ]
    return jsonify(customer_list),200

@app.route('/customers',methods=['POST'])
def add_customer_api():
    data=request.get_json()
    if not data:
        return jsonify({'message':'Invalid JSON data'}),400
    if request.methods=='POST':
        fname = data.get('firstName')
        lname = data.get('lastName')
        nationality = data.get('nationality', '')
        residence = data.get('residence', '')
        tel = data.get('tel','')
        password = data.get('password')
        email = data.get('email', '')
        other = data.get('otherInfo', '')

        if not fname or not lname or not password:
            return jsonify({'message':"Error: First Name, Last Name. and password are required."}),400
        
        try:
            hashed_pass=hashlib.sha256(password.encode()).hexdigest()

            cursor.execute(""" INSERT INTO Customer(First_Name, Last_name, Nationality, Residence, Tel_No, Password, Email_Address, Other_info)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",(fname,lname,nationality,residence,tel,hashed_pass,email,other))
            
            db.commit()
            return jsonify({"message":"Customer added successfully","custid":cursor.lastrowid}),201
        except mysql.connector.Error as err:
            db.rollback()
            return jsonify({"message":f"database error: {err}"}),500

@app.route('/customers/<int:custid>', methods=['PUT'])
def update_customer_api(custid):
    data=request.get_json()
    if not data:
        return jsonify({'message':'Invalid JSON data'}),400
    
    fname = data.get('firstName')
    lname = data.get('lastName')
    fname = data.get('firstName')
    nationality = data.get('nationality', '')
    residence = data.get('residence', '')
    tel = data.get('tel','')
    email = data.get('email', '')
    if not fname or not lname:
        return jsonify({"message": "Error: First name and last name are required."}), 400

    try:
        cursor.execute("""
            UPDATE Customer 
            SET First_Name=%s, Last_name=%s, Email_Address=%s, Tel_No=%s, Nationality=%s, Residence=%s
            WHERE Custid=%s
        """, (fname, lname, email, tel, nationality, residence, custid))
        db.commit()
        return jsonify({"message": f"Customer {custid} updated successfully"}), 200
        
    except mysql.connector.Error as err:
        db.rollback()
        return jsonify({"message": f"Database Error: {err}"}), 500
    
@app.route('/customers/<int:custid>', methods=['DELETE'])
def delete_customer_api(custid):
    try:
        cursor.execute("delete from Customer where Custid=%s", (custid,))
        db.commit()
        return jsonify({"message":f'Customer {custid} deleted successfully'}),200
    except mysql.connector.Error as err:
        db.rollback()
        return jsonify({"message": f"Database Error: {err}"}), 500
    


#Journey
@app.route('/journeys',methods=['GET'])
def show_jouneys():
    cursor.execute("select * from Journey")
    journeys=cursor.fetchall()

    journey_list=[
        {
            'id': j['Journ_Id'],
            'sourse': j['Source'],
            'destination':j['Destination'],
            'cost':float(j['Cost']),
            'route':j['Route']
        }
        for j in journeys
    ]
    return jsonify(journey_list),200

@app.route('/journeys', methods=['POST'])
def add_journey_api():
    data = request.get_json()
    if not data:
            return jsonify({"message": "Invalid JSON data"}), 400
    source =data.get('source')
    dest = data.get('destination')
    cost = data.get('cost', 0)
    route = data.get('route', '')
   
    if not source or not dest:
        return  jsonify({"message":"Error: Source and Destination are required"}),400
    try:
         cost=float(cost)
    except ValueError:
        return jsonify({"message":"Error: Cost must be a number" }),400 
    try:

        cursor.execute("""
            INSERT INTO Journey (Source, Destination, Cost, Route)
            VALUES (%s, %s, %s, %s)
        """, (source, dest, cost, route))
        db.commit()
        return jsonify({"message": "Journey added successfully", "id": cursor.lastrowid}), 201
    except mysql.connector.Error as err:
        db.rollback()
        return jsonify({"message": f"Database error: {err}"}), 500
    
@app.route('/journeys/<int:journey_id>', methods=['PUT'])
def update_journey_api(journey_id):
    data = request.get_json()
    if not data:
            return jsonify({"message": "Invalid JSON data"}), 400
    source =data.get('source')
    dest = data.get('destination')
    cost = data.get('cost', 0)
    route = data.get('route', '')
    if not source or not dest:
        return  jsonify({"message":"Error: Source and Destination are required"}),400
    try:
         cost=float(cost)
    except ValueError:
        return jsonify({"message":"Error: Cost must be a number" }),400    
    try:
        cursor.execute("""
            UPDATE Journey SET Source=%s, Destination=%s, Cost=%s, Route=%s
            WHERE Journ_Id=%s
        """, (source, dest, cost, route, journey_id))
        db.commit()
        if cursor.rowcount == 0:
            return jsonify({"message": f"Journey {journey_id} not found."}), 404
        return jsonify({"message": f"Journey {journey_id} updated successfully"}), 200
    except mysql.connector.Error as err:
        db.rollback()
        return jsonify({"message": f"Database Error: {err}"}), 500
     
@app.route('/journeys/<int:journey_id>', methods=['DELETE'])
def delete_journey_api(journey_id):
    try:
        cursor.execute("DELETE FROM Journey WHERE Journ_Id=%s", (journey_id,))
        db.commit()
        if cursor.rowcount==0:
            return jsonify({"message":f"Journey{journey_id} not found"}),404
        return jsonify({"messaage":f"journey{journey_id} deleted successfully"}),200
    except mysql.connector.Error as err:
        db.rollback()
        return jsonify({"message":f"Database Error:{err}"}),500 

#schedule
@app.route('/schedules',methods=['GET'])
def show_schedules_api():
    cursor.execute("select * from Schedule")
    schedules = cursor.fetchall()
    schedule_list = [
        {
            "id": s['Sche_Id'],
            "journeyId": s['Journ_Id'],
            "date": str(s['Ddate']),       
            "depTime": str(s['Deptime']),  
            "arrTime": str(s['Arritime']),
            "delay": s['Delay_Minutes'],
            "reason": s['Delay_Reason']
        }
        for s in schedules
    ]
    return jsonify(schedule_list), 200
@app.route('/schedules', methods=['POST'])
def add_schedule_api():
    data = request.get_json()
    if not data:
            return jsonify({"message": "Invalid JSON data"}), 400
    journ_id = data.get('journeyId')
    ddate = data.get('date') #YYYY-MM-DD
    deptime = data.get('depTime')#HH:MM:SS
    arrtime = data.get('arrTime')
    delay = data.get('delay', 0)
    reason = data.get('reason', '')
    if not journ_id or not ddate or not deptime:
        return jsonify({"message": "Error: Journey ID, Date, and Departure Time are required"}), 400
    
    try:
        journ_id = int(journ_id)
        delay = int(delay)
    except ValueError:
        return jsonify({"message": "Error: Journey ID and Delay must be numbers"}), 400

    try:    
        cursor.execute("""
            INSERT INTO Schedule (Journ_Id, Ddate, Deptime, Arritime, Delay_Minutes, Delay_Reason)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (journ_id, ddate, deptime, arrtime, delay, reason))
        db.commit()
        return jsonify({"message": "Schedule added successfully", "id": cursor.lastrowid}), 201
    except mysql.connector.Error as err:
        db.rollback()
        return jsonify({"message": f"Database Error: {err}"}), 500

@app.route('/schedules/<int:schedule_id>', methods=['DELETE'])
def delete_schedule_api(schedule_id):
    try:
        cursor.execute("DELETE FROM Schedule WHERE Sche_Id=%s", (schedule_id,))
        db.commit()
        if cursor.rowcount == 0:
            return jsonify({"message": f"Schedule {schedule_id} not found."}), 404
        return jsonify({"message": f"Schedule {schedule_id} deleted successfully"}), 200
    except mysql.connector.Error as err:
        db.rollback()
        return jsonify({"message": f"Database Error: {err}"}), 500 
#tickets
@app.route('/tickets',methods=['GET'])
def show_tickets_api():
    cursor.execute("select * from Ticket")
    tickets = cursor.fetchall()
    ticket_list = [
        {
            "id": t['Ticket_Id'],
            "code": t['Ticket_code'],
            "custId": t['Custid'],
            "scheduleId": t['Sche_Id'],
            "journeyId": t['Journ_Id'],
            "fair": float(t['Fair']), # Ensure fair is a number
            "class": t['Class'],
            "status": t['Status'],
        }
        for t in tickets
    ]
    return jsonify(ticket_list), 200

@app.route('/tickets', methods=['POST'])
def add_ticket():
    data = request.get_json()
    if not data:
            return jsonify({"message": "Invalid JSON data"}), 400
    ticket_code = data.get('code')
    custid = data.get('custId')
    sche_id = data.get('scheduleId')
    journ_id = data.get('journeyId')
    fair = data.get('fair', 0)
    tclass = data.get('class', '')
    status = data.get('status', 'Booked')

    if not ticket_code or not custid  or not sche_id or not journ_id:
        return jsonify({"message": "Error: Ticket code, Customer ID, Schedule ID, and Journey ID are required"}), 400
    
    try:
        custid = int(custid)
        sche_id = int(sche_id)
        journ_id = int(journ_id)
        fair = float(fair)
    except ValueError:
        return jsonify({"message": "Error: IDs must be integers and Fair must be a number."}), 400    

    try:
        cursor.execute("""
            INSERT INTO Ticket (Ticket_code, Custid, Sche_Id, Journ_Id, Fair, Class, Status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (ticket_code, custid, sche_id, journ_id, fair, tclass, status))
        db.commit()
        return jsonify({"message": "Ticket added successfully", "id": cursor.lastrowid}), 201
    except mysql.connector.Error as err:
        db.rollback()
        return jsonify({"message": f"Database Error: {err}"}), 500


@app.route('/tickets/<int:ticket_id>', methods=['DELETE'])
def delete_ticket_api(ticket_id):
    try:
        cursor.execute("DELETE FROM Ticket WHERE Ticket_Id=%s", (ticket_id,))
        db.commit()
        if cursor.rowcount == 0:
            return jsonify({"message": f"Ticket {ticket_id} not found."}), 404
        return jsonify({"message": f"Ticket {ticket_id} deleted successfully"}), 200
    except mysql.connector.Error as err:
        db.rollback()
        return jsonify({"message": f"Database Error: {err}"}), 500

#flight
@app.route('/flights',methods=['GET'])
def show_flights_api():
    cursor.execute("select * from Flight")
    flights = cursor.fetchall()
    flight_list=[
        {
            "id": f['Book_no'],
            "custId": f['Custid'],
            "scheduleId": f['Sche_Id'],
            "journeyId": f['Journ_Id']
        }
        for f in flights
    ]
    return jsonify(flight_list),200
#add flight
@app.route('/add_flight', methods=['POST'])
def add_flight_api():
    data = request.get_json()
    if not data:
            return jsonify({"message": "Invalid JSON data"}), 400
    custid = data.get('custId')
    sche_id = data.get('scheduleId')
    journ_id = data.get('journeyId')

    if not custid or not sche_id or not journ_id:
        return jsonify({"message": "Error: Customer ID, Schedule ID, and Journey ID are required"}), 400
        
    try:
        cursor.execute("""
            INSERT INTO Flight (Custid, Sche_Id, Journ_Id)
            VALUES (%s, %s, %s)
        """, (custid, sche_id, journ_id))
        db.commit()
        return jsonify({"message": "Flight added successfully", "id": cursor.lastrowid}), 201
    except mysql.connector.Error as err:
        db.rollback()
        return jsonify({"message": f"Database Error: {err}"}), 500
    
@app.route('/flights/<int:flight_id>', methods=['DELETE'])
def delete_flight_api(flight_id):
    book_no = flight_id 
    try:
        cursor.execute("DELETE FROM Flight WHERE Book_no=%s", (book_no,))
        db.commit()
        if cursor.rowcount == 0:
            return jsonify({"message": f"Flight with ID {book_no} not found"}), 404
        
        return jsonify({"message": f"Flight {book_no} deleted successfully"}), 200
    except mysql.connector.Error as err:
        db.rollback()
        return jsonify({"message": f"Database Error: {err}"}), 500   
if __name__=="__main__":
    app.run(debug=True)
