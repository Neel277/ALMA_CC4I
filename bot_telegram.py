import logging
import mysql.connector
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# --- 1. CONFIGURATION ---
TOKEN = "8385314661:AAFXTjIjPBnD0bBfAPriEM5YQnFytQxz6jU" 
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root', # <--- PUT YOUR MYSQL WORKBENCH PASSWORD HERE
    'database': 'alma_cc4i'
}

# --- 2. THE BRAIN (Save to DB) ---
# --- THE SMARTER BRAIN ---
def save_to_db(user, text):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        c = conn.cursor()
        
        # 1. INTELLIGENCE LAYER: Determine Severity
        # If user says "fire", "smoke", "fuego", or "help" -> RED
        triggers = ["fire", "fuego", "smoke", "humo", "help", "ayuda", "sos"]
        
        if any(word in text.lower() for word in triggers):
            severity = "RED"
        else:
            severity = "YELLOW" # Normal chatter is just a warning/info
        
        # 2. SAVE IT
        sql = "INSERT INTO incidents (reporter_name, transcript, severity) VALUES (%s, %s, %s)"
        val = (user, text, severity)
        
        c.execute(sql, val)
        conn.commit()
        print(f"✅ SAVED: {user} | Severity: {severity}")
        
        c.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ DATABASE ERROR: {e}")
        return False


# --- 3. THE EARS (Listen & Act) ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    text = update.message.text
    
    print(f"📩 RECEIVED from {user}: {text}")
    
    # Try to save to DB
    success = save_to_db(user, text)
    
    if success:
        await update.message.reply_text("✅ Report Logged in Command Center.")
    else:
        await update.message.reply_text("⚠ Error: Could not save to database. Check terminal.")
        
# --- 4. THE GPS TRACKER (Real Location) ---
async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    lat = update.message.location.latitude
    lon = update.message.location.longitude
    
    # We assume if they send a location, it's an EMERGENCY
    text = "📍 GPS BEACON ACTIVATED"
    severity = "RED"
    
    print(f"📡 GPS RECEIVED from {user}: {lat}, {lon}")
    
    # Save REAL coordinates to DB
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        c = conn.cursor()
        sql = "INSERT INTO incidents (reporter_name, location_lat, location_lon, severity, transcript) VALUES (%s, %s, %s, %s, %s)"
        val = (user, lat, lon, severity, text)
        c.execute(sql, val)
        conn.commit()
        c.close()
        conn.close()
        
        await update.message.reply_text(f"✅ UNITS DISPATCHED TO: {lat:.4f}, {lon:.4f}")
    except Exception as e:
        print(f"❌ GPS ERROR: {e}")
        

# Add this inside bot.py

async def broadcast_warning(context: ContextTypes.DEFAULT_TYPE, lat, lon, radius_km=10):
    """
    Sends a warning to ALL users (stored in memory/DB) if they are near the fire.
    """
    alert_msg = (
        f"🚨 **SATELLITE WARNING** 🚨\n"
        f"NASA has detected a high-temperature fire near your location.\n"
        f"Distance: < {radius_km}km\n"
        f"Status: **EVACUATE NOW**"
    )
    
    # In a real app, you query the DB for users near (lat, lon).
    # For this DEMO, we just blast everyone in our 'citizens_db'.
    # (Assuming you have a list of user_ids)
    
    # fake_user_list = [123456789, 987654321] 
    
    print(f"📡 BROADCASTING ALERT TO AFFECTED ZONE...")
    # for user_id in fake_user_list:
    #    await context.bot.send_message(chat_id=user_id, text=alert_msg)
    

if __name__ == '__main__':
    print("--- ALMA C4I: SATELLITE LINK ESTABLISHED ---")
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Add these TWO lines:
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location)) # <--- NEW!
    
    print("--- WAITING FOR SIGNALS ---")
    app.run_polling()