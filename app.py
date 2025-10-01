from flask import Flask, request, jsonify, render_template, redirect
import pandas as pd
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# Password for upload page
UPLOAD_PASSWORD = "admin123"  # Change this to your desired password

# Database setup
DB_FILE = os.path.join(os.path.dirname(__file__), 'campus_data.db')

def init_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS campus_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                academic_year TEXT NOT NULL,
                campus_name TEXT NOT NULL,
                strength INTEGER,
                onroll INTEGER,
                present INTEGER,
                absent INTEGER,
                nso INTEGER,
                paid INTEGER,
                unpaid INTEGER,
                admission INTEGER,
                tc INTEGER,
                cheques INTEGER,
                using_bus INTEGER,
                using_rickshaw INTEGER,
                using_cycle_moped_stand INTEGER,
                conc_50 INTEGER,
                conc_40 INTEGER,
                conc_30 INTEGER,
                conc_20 INTEGER,
                conc_10 INTEGER,
                tw INTEGER,
                mw INTEGER,
                sec INTEGER,
                avg_std_sec INTEGER
            )
        ''')
        conn.commit()
        print(f"Database initialized at {DB_FILE}")
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
    finally:
        conn.close()

# Check if table exists
def table_exists():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='campus_data'")
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        print(f"Error checking table existence: {str(e)}")
        return False

# Initialize DB on startup
try:
    if not os.path.exists(DB_FILE) or not table_exists():
        print(f"No database or table found at {DB_FILE}, creating new one")
        init_db()
    else:
        print(f"Database and table found at {DB_FILE}")
except Exception as e:
    print(f"Error checking database existence: {str(e)}")

# ---------- NEW: Redirect root URL to /show ----------
@app.route('/')
def index():
    return redirect('/show')

@app.route('/upload', methods=['GET', 'POST'])
def upload_page():
    if request.method == 'GET':
        return render_template('upload.html')
    else:
        password = request.form.get('password')
        if password != UPLOAD_PASSWORD:
            return jsonify({'message': 'Incorrect password.'}), 401
        
        date_str = request.form.get('date')
        academic_year = request.form.get('academic_year', '2025-26')
        if not date_str:
            return jsonify({'message': 'Date is required.'}), 400
        
        try:
            date_str = datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
        except ValueError:
            return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD.'}), 400
        
        if 'file' not in request.files:
            return jsonify({'message': 'No file uploaded.'}), 400
        
        file = request.files['file']
        if not file.filename.endswith('.xlsx'):
            return jsonify({'message': 'File must be .xlsx.'}), 400
        
        try:
            df = pd.read_excel(file)
            required_columns = [
                'Campus Name', 'Strength', 'OnRoll', 'Present', 'Absent', 'NSO', 
                'Paid', 'Unpaid', 'Admission', 'TC', 'Cheques', 'Using Bus', 
                'Using Rickshaw', 'Using Cycle/Moped Stand', 'Conces. 50%', 
                'Conces. 40%', 'Conces. 30%', 'Conces. 20%', 'Conces. 10%', 
                "Teacher's Wards", 'Menial Ward', 'Sections', 'Avg. Student Per Section'
            ]
            if not all(col in df.columns for col in required_columns):
                return jsonify({'message': 'Missing required columns in XLSX.'}), 400
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM campus_data WHERE date = ? AND academic_year = ?', (date_str, academic_year))
            for _, row in df.iterrows():
                cursor.execute('''
                    INSERT INTO campus_data (
                        date, academic_year, campus_name, strength, onroll, present, absent, nso, 
                        paid, unpaid, admission, tc, cheques, using_bus, using_rickshaw, 
                        using_cycle_moped_stand, conc_50, conc_40, conc_30, conc_20, 
                        conc_10, tw, mw, sec, avg_std_sec
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    date_str, academic_year, row['Campus Name'], row['Strength'], row['OnRoll'], 
                    row['Present'], row['Absent'], row['NSO'], row['Paid'], row['Unpaid'], 
                    row['Admission'], row['TC'], row['Cheques'], row['Using Bus'], 
                    row['Using Rickshaw'], row['Using Cycle/Moped Stand'], row['Conces. 50%'], 
                    row['Conces. 40%'], row['Conces. 30%'], row['Conces. 20%'], 
                    row['Conces. 10%'], row["Teacher's Wards"], row['Menial Ward'], 
                    row['Sections'], row['Avg. Student Per Section']
                ))
            conn.commit()
            conn.close()
            return jsonify({'message': 'Data uploaded successfully!'}), 200
        except Exception as e:
            return jsonify({'message': f'Error processing file: {str(e)}'}), 500

@app.route('/show', methods=['GET'])
def show_page_or_data():
    date_str = request.args.get('date')
    academic_year = request.args.get('academic_year', '2025-26')
    if date_str:
        print(f"Querying data for date: {date_str} and academic_year: {academic_year}")
        try:
            date_str = datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM campus_data WHERE date = ? AND academic_year = ?', (date_str, academic_year))
            rows = cursor.fetchall()
            print(f"Rows found for {date_str} and {academic_year}: {len(rows)} rows")
            conn.close()
            
            if not rows:
                return jsonify({'error': 'Data not available for selected date and academic year.'}), 404
            
            columns = [
                'id', 'date', 'academic_year', 'campus_name', 'strength', 'onroll', 'present', 'absent', 
                'nso', 'paid', 'unpaid', 'admission', 'tc', 'cheques', 'using_bus', 
                'using_rickshaw', 'using_cycle_moped_stand', 'conc_50', 'conc_40', 
                'conc_30', 'conc_20', 'conc_10', 'tw', 'mw', 'sec', 'avg_std_sec'
            ]
            data = [dict(zip(columns, row)) for row in rows]
            for item in data:
                del item['id']
                del item['date']
            
            return jsonify(data), 200
        except Exception as e:
            return jsonify({'error': f'Error querying data: {str(e)}'}), 500
    else:
        print("Serving show page")
        return render_template('show.html', academic_year=academic_year)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), debug=True)
