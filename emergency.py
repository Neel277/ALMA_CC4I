import asyncio
from telegram import Bot
from gtts import gTTS
import mysql.connector

# --- CONFIG ---
TOKEN = "8385314661:AAFXTjIjPBnD0bBfAPriEM5YQnFytQxz6jU" 
YOUR_CHAT_ID = "7974332351" 

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'alma_cc4i'
}

async def broadcast_evacuation():
    print("🔍 Scanning Database for Active Predictions...")
    
    try:
        # 1. Connect to the Brain (Database)
        conn = mysql.connector.connect(**DB_CONFIG)
        c = conn.cursor(dictionary=True)
        
        # Get the absolute latest predictive threat
        c.execute("SELECT * FROM incidents WHERE severity = 'SATELLITE_VECTOR' ORDER BY id DESC LIMIT 1")
        threat = c.fetchone()
        
        if not threat:
            print("✅ No active satellite threats found. Standing down.")
            return
            
        # 2. Build the Dynamic Script
        lat = threat['location_lat']
        lon = threat['location_lon']
        transcript = threat['transcript'] 
        # Transcript looks like: "VIIRS DETECTED: 367.0K. WIND: 7.6km/h. VECTOR_PRED: 16.0880,78.4926"
        
        # We craft a scary, robotic, but highly informative sentence
        alert_text = (
            f"CRITICAL ALERT. ALMA C4I System has detected a confirmed thermal anomaly "
            f"at Latitude {lat:.2f}, Longitude {lon:.2f}. "
            f"Sensor telemetry reports: {transcript}. "
            f"Evacuate the predicted vector zone immediately. This is an automated warning."
        )
        
        print(f"🗣️ Generating Speech For: \n{alert_text}")
        
        # 3. Synthesize Voice
        tts = gTTS(text=alert_text, lang='en', tld='co.in') # Indian English accent
        tts.save("alert.ogg")
        print("✅ Audio generated: alert.ogg")
        
        # 4. Blast it to Telegram
        print("📡 Transmitting to civilian devices...")
        bot = Bot(token=TOKEN)
        
        with open("alert.ogg", "rb") as voice_file:
            await bot.send_voice(
                chat_id=YOUR_CHAT_ID, 
                voice=voice_file, 
                caption=f"🚨 DYNAMIC EVACUATION ORDER 🚨\n📍 TARGET: {lat}, {lon}"
            )
            
        print("✅ Broadcast Complete.")
        
        c.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ System Error: {e}")

if __name__ == "__main__":
    asyncio.run(broadcast_evacuation())