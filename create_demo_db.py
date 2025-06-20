import sqlite3

conn = sqlite3.connect("sample_demo.db")
cursor = conn.cursor()

# Create table
cursor.execute("""
CREATE TABLE TicketSales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_name TEXT,
    sale_date TEXT,
    amount REAL
)
""")

# Insert sample data
sample_data = [
    ("Wimbledon Finals", "2024-05-02", 120.0),
    ("NBA Playoffs", "2024-05-15", 95.5),
    ("Formula 1", "2024-06-01", 200.0),
]
cursor.executemany("INSERT INTO TicketSales (event_name, sale_date, amount) VALUES (?, ?, ?)", sample_data)
conn.commit()
conn.close()
