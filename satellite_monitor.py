import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
import mysql.connector
import numpy as np
import math
import time
from datetime import datetime, timedelta
from sklearn.cluster import DBSCAN


# --- CONFIG ---
DB_CONFIG = {
    'host': 'localhost',
    'user': '',
    'password': '', 
    'database': 'DB_name'
}

# NASA VIIRS Feed (South Asia)
NASA_URL = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_South_Asia_24h.csv"

# Setup Open-Meteo API Client (Weather Data)
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)



def get_compass_dir(degrees):
    compass_brackets = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW", "N"]
    val = int((degrees / 22.5) + .5)
    return compass_brackets[(val % 16)]

def get_wind_data(lat, lon):
    """
    Fetches real-time wind speed (km/h) and direction (degrees) 
    for a specific fire location.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ["wind_speed_10m", "wind_direction_10m"]
    }
    
    try:
        responses = openmeteo.weather_api(url, params=params)
        current = responses[0].Current()
        speed = current.Variables(0).Value() # Wind Speed
        direction = current.Variables(1).Value() # Wind Direction (Degrees)
        return speed, direction
    except Exception as e:
        print(f"⚠️ Weather Data Failed: {e}")
        return 0, 0

import math

def calculate_spread_vector(lat, lon, speed, direction):
    """
    Calculates 1-hour prediction coordinates using a simplified 
    Rothermel Surface Fire Spread heuristic and spherical Earth adjustments.
    """
    # --- 1. ROTHERMEL FIRE SPREAD HEURISTIC ---
    # R0 = Base spread in zero wind (0.2 km/h for dry forest)
    # phi_w = Wind coefficient (approx 15% of wind speed)
    R0 = 0.2
    phi_w = 0.15 * speed
    
    # Final Rate of Spread (ROS) in km/h
    ros_kmh = R0 * (1 + phi_w)
    
    # --- 2. VECTOR ADVECTION ---
    # Flip direction 180 degrees (Meteorological wind blows FROM, fire blows TO)
    flow_direction = (direction + 180) % 360
    rads = math.radians(flow_direction)
    
    # Distance the fire actually moves in 1 hour
    dist_km = ros_kmh * 1.0 
    
    # --- 3. SPHERICAL EARTH COORDINATE MATH ---
    # 1 degree of latitude is ~111 km everywhere
    delta_lat = (dist_km * math.cos(rads)) / 111.0
    
    # 1 degree of longitude shrinks as you move away from the equator!
    # We must adjust using the cosine of the current latitude.
    delta_lon = (dist_km * math.sin(rads)) / (111.0 * math.cos(math.radians(lat)))
    
    future_lat = lat + delta_lat
    future_lon = lon + delta_lon
    
    return future_lat, future_lon

def process_satellite_data():
    print("🛰️ CONNECTING TO SATELLITE & WEATHER GRIDS...")
    
    # 1. Get Fire Data
    df = pd.read_csv(NASA_URL)
    
    # Filter for Critical Threats (>365K, FRP > 15.0) in your zone
    critical_fires = df[
        (df['latitude'] >= 15.0) & (df['latitude'] <= 20.0) &
        (df['longitude'] >= 77.0) & (df['longitude'] <= 80.0) &
        (df['bright_ti4'] >= 365) & (df['frp'] >= 15.0)
    ].copy() # .copy() prevents Pandas SettingWithCopy warnings later
    
    if critical_fires.empty:
        print("✅ Grid clear. No critical fires detected.")
        return

    print(f"🔥 Found {len(critical_fires)} raw CRITICAL hot pixels.")
    
    # --- 2. DBSCAN ML CLUSTERING (The Fusion Engine) ---
    coords = critical_fires[['latitude', 'longitude']].to_numpy()
    
    # eps=0.05 degrees is roughly a 5km clustering radius.
    clustering = DBSCAN(eps=0.05, min_samples=1).fit(coords)
    critical_fires['cluster_id'] = clustering.labels_
    
    # Group by cluster_id, taking the center coordinate and the worst-case intensity
    grouped_fires = critical_fires.groupby('cluster_id').agg({
        'latitude': 'mean',
        'longitude': 'mean',
        'bright_ti4': 'max',
        'acq_date': 'max',  # Grabs the date of detection
        'acq_time': 'max'   # Grabs the UTC time of detection
    }).reset_index()

    print(f"🧠 ML ACTIVE: Fused into {len(grouped_fires)} Unified Fire Complexes.")
    
    # --- 3. WEATHER & PREDICTION LOOP ---
    conn = mysql.connector.connect(**DB_CONFIG)
    c = conn.cursor()
    
    # 🚨 NOTICE: We now loop through 'grouped_fires' instead of 'critical_fires'
    for index, fire in grouped_fires.iterrows():
        lat = fire['latitude']
        lon = fire['longitude']
        bright = fire['bright_ti4']
        
        # 2. Format the NASA Timestamp
        acq_date = fire['acq_date']
        # acq_time comes as an integer (e.g., 930 or 1345). We pad it to 4 digits and format to HH:MM.
        raw_time = str(int(fire['acq_time'])).zfill(4)
        
        utc_datetime_str = f"{acq_date} {raw_time}"
        utc_time = datetime.strptime(utc_datetime_str, "%Y-%m-%d %H%M")
        
        # Add 5 hours and 30 minutes to get Indian Standard Time
        ist_time = utc_time + timedelta(hours=5, minutes=30)
        
        # Format perfectly for the UI: "YYYY-MM-DD @ HH:MM IST"
        ist_formatted = ist_time.strftime("%Y-%m-%d @ %H:%M IST")
        
        # acq_time_formatted = f"{raw_time[:2]}:{raw_time[2:]} UTC"
        
        speed, direction = get_wind_data(lat, lon)
        speed = round(speed, 1)
        
        pred_lat, pred_lon = calculate_spread_vector(lat, lon, speed, direction)
        
        # Print to terminal with the timestamp!
        print(f"📍 Complex at {lat:.4f}, {lon:.4f}")
        print(f"🕒 SATELLITE TIMESTAMP: {acq_date} at {ist_formatted}")
        print(f"💨 Wind: {speed}km/h @ {direction}° | 🔮 PREDICTION (1hr): {pred_lat:.4f}, {pred_lon:.4f}")
        
        # 3. Add Timestamp to the UI Transcript
        compass_dir = get_compass_dir(direction)
        # We inject the DATE and TIME right into the transcript string for the JS to read
        transcript = f"VIIRS DETECTED: {bright}K ON {acq_date} @ {ist_formatted}. WIND: {speed:.1f}km/h towards {compass_dir}. VECTOR_PRED: {pred_lat:.4f},{pred_lon:.4f}"
        
        sql = "INSERT INTO incidents (reporter_name, location_lat, location_lon, severity, transcript) VALUES (%s, %s, %s, %s, %s)"
        val = ("ALMA_AI_PREDICTOR", lat, lon, "SATELLITE_VECTOR", transcript) 
        
        try:
            c.execute(sql, val)
            conn.commit()
        except:
            pass 
            
    conn.close()
    print("✅ Cycle Complete.")

if __name__ == "__main__":
    process_satellite_data()
