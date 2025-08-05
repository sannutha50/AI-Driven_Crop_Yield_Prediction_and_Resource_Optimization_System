import mysql.connector
import bcrypt

# Get DB connection
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Cpk@02042003",
        database="resource_optimization"
    )

# Register user with hashed password
def register_user(email, password):
    conn = get_connection()
    cursor = conn.cursor()

    # Check if email already exists
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    if cursor.fetchone():
        conn.close()
        return False

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Insert hashed password
    cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, hashed_password))
    conn.commit()
    conn.close()
    return True

# Authenticate user
def login_user(email, password):
    conn = get_connection()
    cursor = conn.cursor()

    # Fetch the hashed password from the DB
    cursor.execute("SELECT password FROM users WHERE email = %s", (email,))
    result = cursor.fetchone()
    conn.close()

    if result:
        stored_hashed_password = result[0].encode('utf-8') if isinstance(result[0], str) else result[0]
        return bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password)
    return False
