import mysql.connector
import time

# YOUR CONFIG
DB_CONFIG = {
    'host': 'localhost',
    'user': '',
    'password': '', 
    'database': 'DB_name'
}

# COORDS: Pick a spot slightly away from your "User" location to show proximity
# Example: If you are at 17.385, 78.486, put the fire at 17.390, 78.490
FAKE_FIRE_LAT = 17.3900 
FAKE_FIRE_LON = 78.4900

def trigger_fake_satellite():
    conn = mysql.connector.connect(**DB_CONFIG)
    c = conn.cursor()
    
    print("🛰️ [SIMULATION] CONNECTING TO NASA VIIRS FEED...")
    time.sleep(2)
    print("... Downloading Chunk 1/4 ...")
    time.sleep(1)
    print("... Analyzying Thermal Signatures ...")
    time.sleep(1)
    
    print(f"🔥 MATCH FOUND! High Confidence Anomaly at {FAKE_FIRE_LAT}, {FAKE_FIRE_LON}")
    
    # Insert into DB
    sql = "INSERT INTO incidents (reporter_name, location_lat, location_lon, severity, transcript) VALUES (%s, %s, %s, %s, %s)"
    val = ("NASA_SATELLITE", FAKE_FIRE_LAT, FAKE_FIRE_LON, "SATELLITE_RED", "VIIRS ALERT: High Confidence Fire (380K)")
    
    c.execute(sql, val)
    conn.commit()
    print("✅ ALERT SENT TO GOVERNMENT DASHBOARD.")
    print("📡 BROADCASTING EVACUATION ORDER TO 12,400 CITIZENS...")
    
    c.close()
    conn.close()

if __name__ == "__main__":
    trigger_fake_satellite()
