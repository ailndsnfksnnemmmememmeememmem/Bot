import sqlite3

DATABASE_NAME = 'bot_database.db'

def init_db():
    """Initialize the database and create tables if they do not exist."""
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                balance REAL DEFAULT 0
            )
        ''')
        # Create products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                product_id TEXT PRIMARY KEY,
                name TEXT,
                category TEXT,
                description TEXT,
                price REAL,
                image TEXT
            )
        ''')
        # Create orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                user_id INTEGER,
                product_id TEXT,
                address TEXT,
                notes TEXT,
                status TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            )
        ''')
        # Create ads table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ads (
                ad_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad_code TEXT,
                ad_status INTEGER DEFAULT 1
            )
        ''')
        # Create buttons table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS buttons (
                button_id INTEGER PRIMARY KEY AUTOINCREMENT,
                button_name TEXT,
                button_callback TEXT
            )
        ''')
        conn.commit()

def get_user_balance(user_id):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 0

def update_user_balance(user_id, amount):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, ?)', (user_id, 0))
        cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
        conn.commit()

def subtract_user_balance(user_id, amount):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, ?)', (user_id, 0))
        cursor.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (amount, user_id))
        conn.commit()

def add_product(product_id, name, category, description, price, image):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO products (product_id, name, category, description, price, image)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (product_id, name, category, description, price, image))
        conn.commit()

def get_all_products():
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products')
        products = cursor.fetchall()
        return products

def add_order(order_id, user_id, product_id, address, notes, status):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (order_id, user_id, product_id, address, notes, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (order_id, user_id, product_id, address, notes, status))
        conn.commit()

def get_order(order_id):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,))
        order = cursor.fetchone()
        return order

def update_order_status(order_id, status):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE orders SET status = ? WHERE order_id = ?', (status, order_id))
        conn.commit()

def get_all_users():
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users')
        users = cursor.fetchall()
        return [user[0] for user in users]

def get_all_orders():
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM orders')
        orders = cursor.fetchall()
        return orders

def get_product(product_id):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE product_id = ?', (product_id,))
        product = cursor.fetchone()
        return product

def delete_product(product_id):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM products WHERE product_id = ?', (product_id,))
        conn.commit()

def add_ad(ad_code):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO ads (ad_code) VALUES (?)', (ad_code,))
        conn.commit()

def get_ad():
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT ad_code FROM ads WHERE ad_status = 1 ORDER BY ad_id DESC LIMIT 1')
        result = cursor.fetchone()
        return result[0] if result else None

def update_ad_status(ad_status):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE ads SET ad_status = ?', (ad_status,))
        conn.commit()

def change_ad_code(new_ad_code):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE ads SET ad_code = ? WHERE ad_id = (SELECT MAX(ad_id) FROM ads)', (new_ad_code,))
        conn.commit()

def add_button(button_name, button_callback):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO buttons (button_name, button_callback) VALUES (?, ?)', (button_name, button_callback))
        conn.commit()

def get_all_buttons():
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM buttons')
        buttons = cursor.fetchall()
        return buttons
