"""Script to query and display database tables and data."""
import psycopg2

# Connect to the database
conn = psycopg2.connect(
    host="localhost",
    database="hfrat_db",
    user="hfrat_user",
    password="0000"
)

cur = conn.cursor()

# Get all tables
print("=" * 70)
print("DATABASE TABLES")
print("=" * 70)
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name
""")
tables = cur.fetchall()
for table in tables:
    print(f"  📁 {table[0]}")

print()

# Get data from each table
for table in tables:
    table_name = table[0]
    print("=" * 70)
    print(f"📊 TABLE: {table_name.upper()}")
    print("=" * 70)

    # Get column names
    cur.execute(f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = '{table_name}' 
        ORDER BY ordinal_position
    """)
    columns_info = cur.fetchall()
    columns = [col[0] for col in columns_info]

    print(f"Columns: {', '.join(columns)}")
    print("-" * 70)

    # Get data
    cur.execute(f"SELECT * FROM {table_name}")
    rows = cur.fetchall()

    if rows:
        for row in rows:
            row_dict = dict(zip(columns, row))
            print(row_dict)
    else:
        print("(No data)")
    print()

cur.close()
conn.close()
print("✅ Database query completed successfully!")
