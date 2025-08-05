import mysql.connector

# Step 1: Connect to MySQL server (no DB yet) to create the database
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Cpk@02042003"
)
cursor = conn.cursor()
cursor.execute("CREATE DATABASE IF NOT EXISTS resource_optimization")
conn.close()

# Step 2: Connect to the newly created (or existing) database
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Cpk@02042003",
    database="resource_optimization"
)
cursor = conn.cursor()

# Step 3: Now safe to run DB-specific queries
cursor.execute("DROP TABLE IF EXISTS resources")

# Create user table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    email VARCHAR(255) PRIMARY KEY,
    password VARCHAR(255)
)
""")

# Create resources table
cursor.execute("""
CREATE TABLE IF NOT EXISTS resources (
    resource VARCHAR(255) PRIMARY KEY,
    quantity INT
)
""")

# Insert default resources
cursor.executemany("INSERT IGNORE INTO resources (resource, quantity) VALUES (%s, %s)", [
    ("Water (liters)", 100),
    ("Fertilizer (kg)", 50),
    ("Seeds (kg)", 50),
    ("Pesticides (liters)", 70),
    ("Labour (workers)", 60),
    ("Machinery (units)", 15)
])

# Create resource_updates table
cursor.execute("""
CREATE TABLE IF NOT EXISTS resource_updates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resource VARCHAR(255),
    old_quantity INT,
    new_quantity INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Create request logs table
cursor.execute("""
CREATE TABLE IF NOT EXISTS resource_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    requested_data TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()
print("✅ Database initialized successfully.")
