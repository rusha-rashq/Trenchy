import sqlite3

conn = sqlite3.connect("orders.db")

# cursor object to execute SQL commands
c = conn.cursor()


# Using TEXT for all fields
# PRIMARY KEY ensures the order ID is unique
c.execute(
    """
CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    status TEXT,
    item_name TEXT,
    estimated_delivery TEXT
)"""
)

print("Table 'orders' created successfully.")


orders_to_add = [
    ("OD12345", "Shipped", "Red T-Shirt", "October 25th"),
    ("OD67890", "Processing", "Blue Jeans", "October 27th"),
]

# insert all orders, ignoring if they already exist
try:
    c.executemany("INSERT INTO orders VALUES (?,?,?,?)", orders_to_add)
    print("Sample data inserted successfully.")
except sqlite3.IntegrityError:
    print("Data already exists, skipping insertion.")


conn.commit()

conn.close()
