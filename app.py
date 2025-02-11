from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed for session management
CORS(app)  # Enable CORS for all routes

# Database connection function
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Root123#",
            database="gas_system"
        )
        if conn.is_connected():
            print("Database connected successfully!")
        return conn
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None

# Allowed consumer types
VALID_CONSUMER_TYPES = {"household", "business", "industry", "enterprises"}

@app.route('/')
def home():
    return render_template('welcome.html')

@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()  # Use .get_json() to parse JSON body
        nic = data.get("nic")  # Change to lowercase to match the React app

        # Validate NIC is not empty
        if not nic:
            return jsonify({"error": "NIC is required"}), 400

        # Continue with the rest of the registration logic
        email = data.get("email")
        fname = data.get("fname")
        lname = data.get("lname")
        username = data.get("username")
        password = generate_password_hash(data.get("password"))
        consumer_type = data.get("consumer_type", "household").strip().lower()  # Ensure this is sent from React
        enterprise_name = data.get("enterprise_name")
        enterprise_type = data.get("enterprise_type")
        enterprise_email = data.get("enterprise_email")
        enterprise_contact_number = data.get("enterprise_contact_number")
        street_line1 = data.get("street_line1")
        street_line2 = data.get("street_line2")
        city = data.get("city")
        phone_no = data.get("contact_no")  # Ensure this matches the React app

        # Ensure valid consumer_type
        if consumer_type not in VALID_CONSUMER_TYPES:
            return jsonify({"error": f"Invalid consumer type: {consumer_type}"}), 400

        # Handle fields based on consumer_type
        if consumer_type == "household":
            enterprise_name = None
            enterprise_type = None
            enterprise_email = None
            enterprise_contact_number = None
        elif consumer_type == "enterprises":  # Ensure this matches the React app
            if not enterprise_name or not enterprise_type:
                return jsonify({"error": "Enterprise name and type are required for business consumers."}), 400
        elif consumer_type == "industry":
            enterprise_name = None
            enterprise_type = None
            enterprise_email = None
            enterprise_contact_number = None

        # Establish a connection to the database
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        try:
            cursor = conn.cursor()

            # SQL query to insert new consumer
            query = '''
                INSERT INTO consumers (NIC, phone_no, email, fname, lname, username, password, consumer_type,
                enterprise_name, enterprise_type, enterprise_email, enterprise_contact_number,
                street_line1, street_line2, city, role)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            '''
            role = 'user'  # Default role is 'user'

            # Parameters to insert
            params = (
                nic, phone_no, email, fname, lname, username, password, consumer_type,
                enterprise_name, enterprise_type, enterprise_email, enterprise_contact_number,
                street_line1, street_line2, city, role
            )

            cursor.execute(query, params)
            conn.commit()

            return jsonify({"message": "Registration successful"}), 201

        except Error as e:
            print(f"Error during database operation: {e}")
            return jsonify({"error": f"Error: {str(e)}"}), 500
        finally:
            cursor.close()
            conn.close()

    return render_template('register.html')

@app.route("/insert_stock", methods=["POST"])
def insert_stock():
    data = request.get_json()  # Get JSON data from the request
    product = data.get("product")
    quantity = data.get("quantity")
    expiry_date = data.get("expiry")
    last_restock_date = data.get("restock")
    availability = data.get("availability")

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO gasStock (product, quantity, expiry_date, last_restock_date, availability)
        VALUES (%s, %s, %s, %s, %s)
    """
    values = (product, quantity, expiry_date, last_restock_date, availability)

    try:
        cursor.execute(query, values)
        conn.commit()
        return jsonify({"message": "Stock updated successfully!"}), 201
    except Error as e:
        print(f"Error during database operation: {e}")
        return jsonify({"error": f"Error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()
@app.route('/get_stock', methods=['GET'])
def get_stock():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM gasStock")
        stock_data = cursor.fetchall()
        return jsonify(stock_data), 200
    except Error as e:
        print(f"Error fetching stock data: {e}")
        return jsonify({"error": "Error fetching stock data"}), 500
    finally:
        cursor.close()
        conn.close()
        
@app.route('/register_outlet', methods=['POST'])
def register_outlet():
    if request.method == "POST":
        data = request.get_json()  # Get JSON data from the request
        outlet_name = data.get("outlet_name")
        email = data.get("email")
        location = data.get("location")
        password = data.get("password")

        if not outlet_name or not email or not location or not password:
            return jsonify({"error": "All fields are required"}), 400

        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed!"}), 500

        try:
            cursor = conn.cursor()
            query = "INSERT INTO outlets (outlet_name, email, location, password) VALUES (%s, %s, %s, %s)"
            values = (outlet_name, email, location, hashed_password)

            cursor.execute(query, values)
            conn.commit()

            return jsonify({"message": "Outlet registered successfully!"}), 201
        except Error as e:
            print(f"Error during database operation: {e}")
            return jsonify({"error": f"Error: {str(e)}"}), 500
        finally:
            cursor.close()
            conn.close()

    return jsonify({"error": "Invalid request method"}), 405
@app.route('/get_outlets', methods=['GET'])
def get_outlets():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed!"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT outlet_ID, outlet_name, location, email FROM outlets")
        outlets = cursor.fetchall()
        return jsonify(outlets), 200
    except Error as e:
        print(f"Error fetching outlets: {e}")
        return jsonify({"error": "Error fetching outlets"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/edit_outlet/<int:outlet_id>', methods=['PUT'])
def edit_outlet(outlet_id):
    data = request.get_json()
    outlet_name = data.get("outlet_name")
    email = data.get("email")
    location = data.get("location")

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed!"}), 500

    try:
        cursor = conn.cursor()
        query = "UPDATE outlets SET outlet_name = %s, email = %s, location = %s WHERE outlet_ID = %s"
        values = (outlet_name, email, location, outlet_id)

        cursor.execute(query, values)
        conn.commit()

        return jsonify({"message": "Outlet updated successfully!"}), 200
    except Error as e:
        print(f"Error during database operation: {e}")
        return jsonify({"error": f"Error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/outlet_login", methods=["GET", "POST"])
def outlet_login():
    if request.method == "POST":
        outlet_name = request.form["outlet_name"]
        password = request.form["password"]

        conn = get_db_connection()

        # Open a new cursor for the query
        cursor = conn.cursor()

        # Execute the query to fetch outlet details based on outlet name
        query = "SELECT outlet_ID, password FROM outlets WHERE outlet_name = %s"
        cursor.execute(query, (outlet_name,))

        # Fetch the result (it should be a single row, hence using fetchone())
        result = cursor.fetchone()

        # Always fetch before closing the cursor
        if result:
            outlet_ID, stored_password = result
            # Check if the password matches the stored hashed password
            if bcrypt.checkpw(password.encode("utf-8"), stored_password.encode("utf-8")):
                session["outlet_ID"] = outlet_ID
                session["outlet_name"] = outlet_name
                return redirect(url_for("outlet_dashboard"))  # Redirect to outlet dashboard
            else:
                return render_template("outlet_login.html", error="Invalid password")
        else:
            return render_template("outlet_login.html", error="Outlet not found")

        # Close the cursor
        cursor.close()

    return render_template("outlet_login.html")

@app.route("/outlet_dashboard", methods=["GET", "POST"])
def outlet_dashboard():
    if "outlet_ID" not in session:
        return redirect("/outlet_login")

    outlet_ID = session["outlet_ID"]
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch gas stock data
    cursor.execute("SELECT stock_ID, quantity, status, date FROM gasStock")
    gas_stock_data = cursor.fetchall()

    # Fetch delivery data (including newly added delivery)
    cursor.execute("SELECT Delivery_ID, Status, stock_ID, outlet_ID FROM delivery WHERE outlet_ID = %s", (outlet_ID,))
    deliveries = cursor.fetchall()

    # Handle adding a new delivery
    if request.method == "POST":
        stock_ID = request.form.get("stock_ID")

        if not stock_ID:
            return "Stock ID is required", 400

        try:
            # Ensure the stock exists for the given outlet
            cursor.execute("SELECT * FROM gasStock WHERE stock_ID = %s", (stock_ID,))
            stock = cursor.fetchone()

            if not stock:
                return f"Stock ID {stock_ID} does not exist", 400

            # Insert the delivery record
            cursor.execute("""
                INSERT INTO delivery (Delivery_date, Status, stock_ID, outlet_ID)
                VALUES (NOW(), %s, %s, %s)
            """, ('pending', stock_ID, outlet_ID))

            conn.commit()
            return redirect(url_for('outlet_dashboard'))  # Redirect to the same page to show updated deliveries

        except Error as e:
            return f"Error occurred while adding delivery: {e}", 500
        finally:
            cursor.close()
            conn.close()

    cursor.close()
    conn.close()

    # Pass updated deliveries to the template
    return render_template("outlet_dashboard.html", gas_stock_data=gas_stock_data, deliveries=deliveries, outlet_ID=outlet_ID)

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed!"}), 500

    cursor = conn.cursor()

    # Check if the username exists in the outlets table
    query = "SELECT password, 'outlet' AS role FROM outlets WHERE outlet_name = %s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()

    if result:
        stored_password = result[0]
        # Check if the stored password matches the one provided
        if bcrypt.checkpw(password.encode("utf-8"), stored_password.encode("utf-8")):
            return jsonify({"message": "Login successful", "role": "outlet"}), 200
        else:
            return jsonify({"error": "Invalid password"}), 401
    else:
        # Check if the username exists in the consumers table
        query = "SELECT password, role FROM consumers WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()

        if result:
            stored_password, role = result
 # Check if the stored password matches the one provided
            if check_password_hash(stored_password, password):
                return jsonify({"message": "Login successful", "role": role}), 200
            else:
                return jsonify({"error": "Invalid password"}), 401
        else:
            return jsonify({"error": "User  not found"}), 404

    cursor.close()
    conn.close()

@app.route("/user_dashboard")
def user_dashboard():
    if "username" not in session:
        return redirect("/login")

    username = session["username"]

    conn = get_db_connection()
    cursor = conn.cursor()

    # Example query to fetch user-specific data
    cursor.execute("SELECT * FROM consumers WHERE username = %s", (username,))

    user_data = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("user_dashboard.html", user_data=user_data)

@app.route("/admin_dashboard", methods=["GET", "POST"])
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM delivery")
    deliveries = cursor.fetchall()

    if request.method == "POST":
        delivery_id = request.form['id']
        new_status = request.form['status']

        try:
            cursor.execute("UPDATE delivery SET Status = %s WHERE Delivery_ID = %s", (new_status, delivery_id))
            conn.commit()
            print(f"Delivery ID {delivery_id} updated to status {new_status}")
        except Error as e:
            print(f"Error during database operation: {e}")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('admin_dashboard'))

    cursor.close()
    conn.close()

    return render_template("admin_dashboard.html", deliveries=deliveries)

@app.route("/edit_delivery/<int:id>", methods=["GET", "POST"])
def edit_delivery(id):
    if request.method == "POST":
        # Get the new delivery details from the form
        status = request.form["status"]

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Update the delivery record in the database
            cursor.execute("""
                UPDATE delivery
                SET Status = %s
                WHERE Delivery_ID = %s
            """, (status, id))

            conn.commit()
        except Error as e:
            print(f"Error during database operation: {e}")
        finally:
            cursor.close()
            conn.close()

        # After updating, redirect to the admin dashboard to show the updated list
        return redirect(url_for("admin_dashboard"))

    # Fetch the current delivery details for pre-populating the form
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM delivery WHERE Delivery_ID = %s", (id,))
    delivery = cursor.fetchone()
    cursor.close()
    conn.close()

    if not delivery:
        return "Delivery not found", 404

    return render_template("edit_delivery.html", delivery=delivery)

@app.route("/logout")
def logout():
    # Remove the session information
    session.clear()

    # Redirect to the welcome page after logging out
    return redirect(url_for("home"))

# Add Delivery route
@app.route('/add_delivery', methods=['POST'])
def add_delivery():
    stock_ID = request.form.get("stock_ID")
    outlet_ID = session.get("outlet_ID")  # Get outlet_ID from the session

    if not stock_ID:
        return "Stock ID is required", 400
    if not outlet_ID:
        return "You need to be logged in to add a delivery", 403

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Ensure the stock exists for the given outlet
        cursor.execute("SELECT * FROM gasStock WHERE stock_ID = %s", (stock_ID,))
        stock = cursor.fetchone()

        if not stock:
            return f"Stock ID {stock_ID} does not exist", 400

        # Insert the delivery record
        cursor.execute(""" 
            INSERT INTO delivery (Delivery_date, Status, stock_ID, outlet_ID)
            VALUES (NOW(), %s, %s, %s)
        """, ('pending', stock_ID, outlet_ID))

        # Update the stock status to 'Delivered' after delivery
        cursor.execute(""" 
            UPDATE gasStock 
            SET status = %s 
            WHERE stock_ID = %s
        """, ('Delivered', stock_ID))

        conn.commit()

        # Instead of redirecting to delivery records page, stay on the current page
        return redirect(url_for('outlet_dashboard'))  # Redirect to the outlet dashboard to show updated deliveries

    except Error as e:
        return f"Error occurred while adding delivery: {e}", 500
    finally:
        cursor.close()
        conn.close()

@app.route('/gas_stock')
def view_gas_stock():
    outlet_ID = session.get("outlet_ID")
    if not outlet_ID:
        return "You need to be logged in to view stock", 403

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch available gas stock for the specific outlet
        cursor.execute("SELECT * FROM gasstock WHERE outlet_ID = %s AND status != 'Delivered'", (outlet_ID,))
        gas_stock = cursor.fetchall()

        return render_template('gas_stock.html', gas_stock=gas_stock)
    
    except Error as e:
        return f"Error occurred while fetching gas stock: {e}", 500
    finally:
        cursor.close()
        conn.close()

@app.route('/delivery_records')
def view_delivery_records():
    outlet_ID = session.get("outlet_ID")
    if not outlet_ID:
        return "You need to be logged in to view delivery records", 403

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch delivery records for the specific outlet
        cursor.execute("SELECT * FROM delivery WHERE outlet_ID = %s", (outlet_ID,))
        delivery_records = cursor.fetchall()

        return render_template('outlet_dashboard.html', deliveries=delivery_records, success_message="Delivery added successfully!")

    except Error as e:
        return f"Error occurred while fetching delivery records: {e}", 500
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    app.run(debug=True)