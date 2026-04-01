# ALMA CC4I: Autonomous Logistic & Monitoring Architecture 🛰️🌍

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![NASA FIRMS](https://img.shields.io/badge/Data-NASA_VIIRS-red.svg)
![Geospatial](https://img.shields.io/badge/Mapping-Leaflet.js-brightgreen.svg)
![Status](https://img.shields.io/badge/Status-Active_Prototype-success.svg)

## 📌 Executive Summary
**ALMA C4I** is a proactive geospatial monitoring and predictive framework designed to detect, model, and broadcast environmental threat vectors (specifically wildfires) in real-time. Moving beyond reactive disaster management, this system fuses live satellite thermal telemetry with live meteorological APIs to calculate forward-burn trajectories and autonomously broadcast AI-synthesized evacuation orders to at-risk civilian populations.

This project was developed as an applied computational model for climate adaptation and proactive disaster resilience.

---

## ⚙️ Core Architecture

The system operates on a four-tier architecture:

1. **The Sky Hook (Data Ingestion):** * Autonomously pulls military-grade thermal anomaly data from the **NASA FIRMS VIIRS (375m) satellite feed**.
   * Implements a strict Brightness Temperature filter (>350 Kelvin) to isolate critical threats from background agricultural noise.
2. **The Intelligence Core (Data Fusion):**
   * Pings the **Open-Meteo API** to extract real-time wind speed and atmospheric direction vectors for the exact coordinates of the confirmed thermal anomaly.
3. **The Predictive Engine (Mathematical Modeling):**
   * Utilizes a baseline spread model derived from wildland fire behavior heuristics. The algorithm transposes meteorological wind directions (where wind originates) by 180 degrees to calculate the forward burn vector, projecting a 1-hour "Kill Zone" trajectory.
4. **The Autonomous Broadcaster (Civilian Alerting):**
   * Parses the database for the newest predictive vector.
   * Utilizes Google Text-to-Speech (`gTTS`) to dynamically synthesize an emergency audio warning with specific geographic coordinates.
   * Transmits the voice note directly to civilian devices via the **Telegram Bot API**.

---

## 🧮 The Predictive Model (Physics & Vector Math)
The core of the prediction relies on converting standard meteorological coordinates into action-oriented geospatial paths. 

```python
# Extract of the directional 180-degree transposition
flow_direction = (direction + 180) % 360
rads = math.radians(flow_direction)


Prerequisites
Python 3.8+

MySQL Server (Running locally or hosted)

API Keys: NASA FIRMS API (for VIIRS thermal data), Open-Meteo API, and Telegram Bot API.

1. Clone the repository

2. Install Python dependencies:
  pip install pandas scikit-learn requests mysql-connector-python gTTS

3. Database Configuration:

Ensure your MySQL server is running.
Execute the SQL schema provided in database_setup.sql to create the required tables for storing advection coordinates and timestamp data.
Update the database credentials (user, password, host) inside the Python script

4. API Configuration:

Insert your NASA FIRMS API key into the designated variable in the backend script.
Insert your Telegram Bot token if utilizing the Autonomous Broadcaster.

5. Start the Core Engine:

Run the backend Python script to begin orbital ingestion, ML clustering, and advection calculations.
python satellite_monitor.py

Note: The terminal will output live logs detailing the raw pixel count, DBSCAN fusion results, and predictive coordinates.

6. Launch the Tactical Dashboard: run python app.py


📂 File Structure & Architecture Breakdown
satellite_monitor.py The core Python backend engine. This script handles the multi-stage processing pipeline: pulling raw telemetry from NASA, applying the bivariate noise filter, executing DBSCAN clustering to fuse overlapping pixels, running the modified Rothermel physics equations, and pushing to the MySQL database.

index.html (and associated JS/CSS)
The frontend Tactical Web Dashboard. Built utilizing Leaflet.js, this dark-mode UI pulls the processed coordinate data from the database. It dynamically renders the origin clusters, draws the predictive threat-cones (cyan polygons), and assigns Tiered Behavioural Action levels based on wind thresholds.

database_setup.sql
The structural blueprint for the MySQL database, ensuring the correct formatting for timestamped coordinate arrays and wind vectors.
Open the frontend UI to visualize the real-time threat matrix. You can serve it using a simple local server:

# Spherical Earth Coordinate Projection
delta_lat = (dist_km * math.cos(rads)) / 111.0
delta_lon = (dist_km * math.sin(rads)) / 111.0
