from flask import Flask, render_template, jsonify
import mysql.connector

app = Flask(__name__)

# --- MYSQL CONFIGURATION ---
db_config = {
    'host': 'localhost',
    'user': '',
    'password': '',
    'database': 'DB_name'
}

def get_incidents():
    try:
        conn = mysql.connector.connect(**db_config)
        # dictionary=True makes it return JSON-ready data automatically
        c = conn.cursor(dictionary=True) 
        
        c.execute("SELECT * FROM incidents ORDER BY timestamp DESC")
        rows = c.fetchall()
        return rows
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []
    finally:
        if 'conn' in locals() and conn.is_connected():
            c.close()
            conn.close()

@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/api/incidents')
def api_incidents():
    data = get_incidents()
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
    
