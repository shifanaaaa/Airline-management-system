 ✈️ Airline Management System (DBMS Project)

 📌 Overview

This project is a Database Management System-based Airline Management System developed using Python (Flask) and  MySQL .
It allows users to search flights, book tickets, select seats, and manage bookings, while admins can manage flights, customers, and tickets.

---

 🎯 Features

👤 Customer Features

* User registration and login
* Search flights by source, destination, and date
* Seat selection system
* Ticket booking with unique ticket code
* View booked tickets
* Cancel tickets

 🛠️ Admin Features

* Admin login
* Add, update, and delete flights
* Automatic seat generation
* View total flights, customers, and tickets
* Manage all bookings
* Cancel tickets

---

🧠 DBMS Concepts Used

* Relational Database (MySQL)
* Primary & Foreign Keys
* Joins (Ticket, Flight, Customer tables)
* Transactions (commit & rollback)
* Data integrity constraints

---

 🛠️ Tech Stack

* Backend: Python, Flask
* Frontend: HTML, CSS
* Database: MySQL

---

📁 Project Structure

```
airline-dbms/
│
├── backend/
│   └── app.py
|   └──databases.txt
|   └──requirements.txt
│
├── frontend/ (or templates if Flask)
│   ├── index.html
│   ├── register.html
│   └──add_fight.html
|   └──admin_dashboard.html
|   └──admin_login.html
|   └──admin_tickets.html
|   └──customer_dashboard.html
|   └──customer_login.html
|   └──customers.html
|   └──search_flights.html
|   └──search_results.html
|   └──seat)_selection.html
|   └──tickets.html
|   └──update_fights.html
│
|
│
├── README.md
└── .gitignore
```

---

 ▶️ How to Run

1. Install dependencies:

```
pip install flask mysql-connector-python
```

2. Setup MySQL database:

* Create database (e.g., `mydbs`)
* Import tables (Flight, Customer, Ticket, Seat, Admin)

3. Update database credentials in `app.py`

4. Run the application:

```
python app.py
```

5. Open browser:

```
http://127.0.0.1:5000/
```

---

🔐 Key Functionalities

* Secure session handling for users and admin
* Real-time seat availability tracking
* Ticket generation using unique ticket codes
* Flight scheduling and filtering
* Booking and cancellation system

---

 👥 Team Members

* Shifana Parveen
* Joann Elizabeth Joseph
* Khalid Mohamed M
* Kundan Kumar              

---

 🚀 Future Enhancements

* Online payment integration
* Email/SMS ticket confirmation
* Advanced analytics dashboard
* Mobile application support

---
