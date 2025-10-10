import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

def create_database(db_path):
    # Remove existing database for a fresh start
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create customer table
    cursor.execute('''
    CREATE TABLE customer (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        gender Char(1), is_active BOOLEAN DEFAULT 1
    );
    ''')
    
    # Insert sample customers
    sample_data = [
        ('Alice Smith', 'alice@example.com', 'F', True),
        ('Bob Johnson', 'bob@example.com', 'M', False),
        ('Carol Lee', 'carol@example.com', 'F', True)
    ]
    cursor.executemany('INSERT INTO customer (name, email, gender, is_active) VALUES (?, ?, ?, ?)', sample_data)

    # Create products table
    cursor.execute('''
    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL
    );
    ''')

    
    products_data = [
        ('Laptop', 999.99),
        ('Smartphone', 499.49),
        ('Tablet', 299.99),
        ('Head and Shoulders', 89.99)
    ]
    cursor.executemany('INSERT INTO products (name, price) VALUES (?, ?)', products_data)

    cursor.execute('''
    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        product_id INTEGER,
        order_date TEXT,
        FOREIGN KEY(customer_id) REFERENCES customer(customer_id),
        FOREIGN KEY(product_id) REFERENCES products(product_id)
    );
    ''')

    # Insert sample orders
    orders_data = [
        (1, 1, '2023-10-01'),
        (2, 2, '2023-10-02'),
        (3, 3, '2023-10-03'),
        (1, 4, '2023-10-04'),
        (2, 1, '2023-10-05'),
        (3, 2, '2023-10-06'),
        (1, 3, '2023-10-07')
    ]
    cursor.executemany('INSERT INTO orders (customer_id, product_id, order_date) VALUES (?, ?, ?)', orders_data)

    conn.commit()
    conn.close()

def run_query(db_path, query):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results

if __name__ == "__main__":
    create_database('data/data.db')
    print(f"Database created successfully at: {'data/data.db'}")
