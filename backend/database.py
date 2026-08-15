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
            report_type TEXT DEFAULT 'Unspecified',
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

def add_ngo(org_name, email, phone, region):
    """Inserts an NGO registration. Returns {"success": True, "id": ...} or
    {"success": False, "error": ...} on a duplicate email or other failure."""
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
        return {"success": True, "id": cur.lastrowid}
    except sqlite3.IntegrityError:
        return {"success": False, "error": "An organization with this email is already registered."}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def add_report(report_type, location, description):
    """Inserts a citizen debris report and returns its new row id."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO citizen_reports (report_type, location, description) 
        VALUES (?, ?, ?);
        """,
        (report_type or "Unspecified", location, description)
    )
    conn.commit()
    report_id = cur.lastrowid
    conn.close()
    return report_id

def get_pollution_hotspots():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, severity, confidence, area_name, lat, lng, detected_at FROM pollution_hotspots")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_ngos_by_region(location):
    """Returns NGOs whose registered region matches (loosely) the alert location —
    e.g. an NGO registered for 'Visakhapatnam' matches an alert for
    'RK Beach, Visakhapatnam'."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT org_name, email, phone, region FROM ngos
        WHERE ? LIKE '%' || region || '%' OR region LIKE '%' || ? || '%'
        """,
        (location, location)
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def record_detections(geojson):
    """Persists freshly detected plastic hotspots (from the UNet++ inference pipeline)
    into pollution_hotspots so they show up on the dashboard. Assumes the source
    raster's CRS is already WGS84 lat/lng — reproject with pyproj first if your
    Sentinel-2 tiles use a projected CRS (e.g. UTM)."""
    conn = get_db_connection()
    cur = conn.cursor()
    inserted = 0
    for feature in geojson.get("features", []):
        geom = feature.get("geometry") or {}
        coords = geom.get("coordinates")
        if not coords:
            continue
        lng, lat = _centroid_from_geometry(geom.get("type"), coords)
        confidence = feature.get("properties", {}).get("confidence", 0.0)
        if confidence >= 0.85:
            severity = "Critical"
        elif confidence >= 0.65:
            severity = "High"
        elif confidence >= 0.4:
            severity = "Moderate"
        else:
            severity = "Low"
        cur.execute(
            """
            INSERT INTO pollution_hotspots (severity, confidence, area_name, lat, lng)
            VALUES (?, ?, ?, ?, ?)
            """,
            (severity, confidence, "AI-detected hotspot", lat, lng)
        )
        inserted += 1
    conn.commit()
    conn.close()
    return inserted


def _centroid_from_geometry(geom_type, coordinates):
    """Naive centroid for Polygon/MultiPolygon geometry (averages exterior-ring
    vertices) — good enough for placing a marker, not for precise area math."""
    if geom_type == "Polygon":
        ring = coordinates[0]
    elif geom_type == "MultiPolygon":
        ring = coordinates[0][0]
    else:
        ring = coordinates
    xs = [pt[0] for pt in ring]
    ys = [pt[1] for pt in ring]
    return sum(xs) / len(xs), sum(ys) / len(ys)