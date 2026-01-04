"""Script to add monitor user and African facilities to the database."""
import psycopg2
from werkzeug.security import generate_password_hash

# Connect to the database
conn = psycopg2.connect(
    host="localhost",
    database="hfrat_db",
    user="hfrat_user",
    password="0000"
)
conn.autocommit = True
cur = conn.cursor()

print("=" * 70)
print("Adding Monitor User")
print("=" * 70)

# Check if monitor already exists
cur.execute("SELECT id FROM users WHERE email = 'monitor@hfrat.com'")
if cur.fetchone():
    print("Monitor user already exists!")
else:
    password_hash = generate_password_hash("Monitor@2026!")
    cur.execute("""
        INSERT INTO users (email, password_hash, role, created_at, updated_at)
        VALUES (%s, %s, %s, NOW(), NOW())
    """, ('monitor@hfrat.com', password_hash, 'MONITOR'))
    print("✅ Monitor user created: monitor@hfrat.com / Monitor@2026!")

print()
print("=" * 70)
print("Adding African Facilities")
print("=" * 70)

african_facilities = [
    ("Kenyatta National Hospital", "Kenya", "Nairobi"),
    ("Muhimbili National Hospital", "Tanzania", "Dar es Salaam"),
    ("Mulago National Referral Hospital", "Uganda", "Kampala"),
    ("King Faisal Hospital", "Rwanda", "Kigali"),
    ("Chris Hani Baragwanath Hospital", "South Africa", "Johannesburg"),
    ("Korle Bu Teaching Hospital", "Ghana", "Accra"),
    ("Lagos University Teaching Hospital", "Nigeria", "Lagos"),
    ("Centre Hospitalier Universitaire", "Senegal", "Dakar"),
    ("Moi Teaching and Referral Hospital", "Kenya", "Eldoret"),
    ("Groote Schuur Hospital", "South Africa", "Cape Town"),
]

for name, country, city in african_facilities:
    # Check if facility already exists
    cur.execute("SELECT id FROM facilities WHERE name = %s", (name,))
    if cur.fetchone():
        print(f"  ⚠️  {name} already exists")
    else:
        cur.execute("""
            INSERT INTO facilities (name, country, city, created_at)
            VALUES (%s, %s, %s, NOW())
        """, (name, country, city))
        print(f"  ✅ Added: {name} ({city}, {country})")

print()
print("=" * 70)
print("Current Database Summary")
print("=" * 70)

cur.execute("SELECT COUNT(*) FROM users")
print(f"Total Users: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM facilities")
print(f"Total Facilities: {cur.fetchone()[0]}")

print()
print("Users:")
cur.execute("SELECT email, role FROM users ORDER BY id")
for email, role in cur.fetchall():
    print(f"  - {email} ({role})")

print()
print("African Facilities:")
cur.execute("SELECT name, city, country FROM facilities WHERE country IN ('Kenya', 'Tanzania', 'Uganda', 'Rwanda', 'South Africa', 'Ghana', 'Nigeria', 'Senegal') ORDER BY country, name")
for name, city, country in cur.fetchall():
    print(f"  - {name} ({city}, {country})")

cur.close()
conn.close()
print()
print("✅ Done!")
