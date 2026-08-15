# backend/database.py
import sqlite3

DB_FILE = "coastsentinel.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 1. Registered NGOs Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ngos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            region TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. Pollution Hotspots Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pollution_hotspots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            severity TEXT CHECK (severity IN ('Low', 'Moderate', 'High', 'Critical')),
            confidence REAL NOT NULL,
            area_name TEXT NOT NULL,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. Citizen Debris Reports Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS citizen_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT NOT NULL,
            description TEXT NOT NULL,
            reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Pre-populate sample hotspot telemetry if empty
    cur.execute("SELECT COUNT(*) FROM pollution_hotspots")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO pollution_hotspots (severity, confidence, area_name, lat, lng) 
            VALUES 
            ('High', 0.92, 'RK Beach, Visakhapatnam', 17.6868, 83.2185),
            ('Moderate', 0.78, 'Alappuzha Coastline', 9.4981, 76.3388)
        """)
        conn.commit()
        
    conn.close()

def insert_ngo(org_name, email, phone, region):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO ngos (org_name, email, phone, region) 
            VALUES (?, ?, ?, ?);
            """,
            (org_name, email, phone, region)
        )
        conn.commit()
        user_id = cur.lastrowid
        return {"success": True, "user_id": user_id}
    except sqlite3.IntegrityError:
        return {"success": False, "error": "An organization with this email is already registered."}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def get_pollution_hotspots():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, severity, confidence, area_name, lat, lng, detected_at FROM pollution_hotspots")
    rows = cur.fetchall()
    conn.close()
    return rows