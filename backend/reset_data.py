# backend/reset_data.py
"""
Dev/testing utility — clears registered NGOs, citizen reports, and any
AI-detected pollution hotspots so you can re-run registration/detection
flows repeatedly without hitting duplicate-email conflicts or having old
test data clutter the dashboard.

Run from the backend/ folder (with the Flask server stopped, so nothing
else is writing to the database at the same time):

    python reset_data.py

Only clears rows in coastsentinel.db — no code or model files are touched.
"""
import database

conn = database.get_db_connection()
cur = conn.cursor()

cur.execute("DELETE FROM ngos")
ngo_count = cur.rowcount

cur.execute("DELETE FROM citizen_reports")
report_count = cur.rowcount

cur.execute("DELETE FROM pollution_hotspots")
hotspot_count = cur.rowcount

conn.commit()
conn.close()

print(f"Cleared {ngo_count} NGOs, {report_count} citizen reports, {hotspot_count} pollution hotspots.")
print("Note: the two sample hotspots seeded by init_db() will reappear the next")
print("time app.py starts, since init_db() only re-inserts them when the table is empty.")