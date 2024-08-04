import sqlite3

def setup_database():
    # Connect to SQLite database
    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()

    # Drop existing tables for a clean setup (optional)
    cursor.execute("DROP TABLE IF EXISTS customers")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS invoices")
    cursor.execute("DROP TABLE IF EXISTS invoice_items")

    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER DEFAULT 0
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY,
        customer_id INTEGER,
        date TEXT NOT NULL,
        total REAL NOT NULL,
        additional_discount REAL DEFAULT 0,  -- Added field
        payment_mode TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invoice_items (
        id INTEGER PRIMARY KEY,
        invoice_id INTEGER,
        product_id INTEGER,
        quantity INTEGER NOT NULL,
        FOREIGN KEY (invoice_id) REFERENCES invoices(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    ''')

    # Insert initial data into products table
    products = [
        ('Product A', 100.0, 10),
        ('Product B', 200.0, 5),
        ('Product C', 300.0, 15)
    ]

    cursor.executemany('''
    INSERT INTO products (name, price, quantity) VALUES (?, ?, ?)
    ''', products)

    # Commit changes and close the connection
    conn.commit()
    conn.close()

    print("Database setup completed successfully.")

if __name__ == '__main__':
    setup_database()
