from flask import Flask, jsonify, request
import sqlite3
import os

app = Flask(__name__)

# Create a SQLite database and table
conn = sqlite3.connect('data/signals.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker VARCHAR,
        opening_price REAL,
        generation_price REAL,
        stop_loss REAL,
        take_profit REAL,
        risk REAL,
        no_stocks INT,
        most_recent_price REAL,
        status INTEGER,
        date_of_gen TIMESTAMP,
        date_of_purchase TIMESTAMP,
        date_of_expiry TIMESTAMP
    )
''')
# status is integer but 1 - active, 2 - not active (waiting for purchase), 3 - expired 
conn.commit()
conn.close()

class Signal:
    def __init__(self, signal_data):
        self.ticker = signal_data.get('ticker', None)
        self.opening_price = signal_data.get('opening_price', None)
        self.generation_price = signal_data.get('generation_price', None)
        self.stop_loss = signal_data.get('stop_loss', None)
        self.take_profit = signal_data.get('take_profit', None)
        self.risk = signal_data.get('risk', None)
        self.no_stocks = signal_data.get('no_stocks', None)
        self.most_recent_price = signal_data.get('most_recent_price', None)
        self.status = signal_data.get('status', None)
        self.date_of_gen = signal_data.get('date_of_gen', None)
        self.date_of_purchase = signal_data.get('date_of_purchase', None)
        self.date_of_expiry = signal_data.get('date_of_expiry', None)
        self.id = signal_data.get('id',None)

    def to_dict(self):
        return vars(self)
    
    def compare(self, other_signal):
        if not isinstance(other_signal, Signal):
            raise ValueError("Cannot compare Signal with non-Signal object")
        
        differences = {}
        for field, self_val in self.to_dict().items():
            other_val = getattr(other_signal, field, None)           
            if self_val != other_val:
                differences[field] = self_val
        return differences



# Endpoint to get all active signals
@app.route('/get_active_signals', methods=['GET'])
def get_active_signals():
    conn = sqlite3.connect('data/signals.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM signals WHERE status == 1')
    signals = cursor.fetchall()
    conn.close()

    columns = ['id', 'ticker', 'opening_price', 'generation_price', 'stop_loss', 'take_profit', 'risk', 
               'no_stocks', 'most_recent_price', 'status', 'date_of_gen', 
               'date_of_purchase', 'date_of_expiry']
    signals_list = [dict(zip(columns, signal)) for signal in signals]
    
    return jsonify({'signals': signals_list})

# Endpoint to get all considered signals
@app.route('/get_considered_signals', methods=['GET'])
def get_considered_signals():
    conn = sqlite3.connect('data/signals.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM signals WHERE status == 2 ORDER BY risk ASC')
    signals = cursor.fetchall()
    conn.close()

    columns = ['id', 'ticker', 'opening_price', 'generation_price', 'stop_loss', 'take_profit', 'risk', 
               'no_stocks', 'most_recent_price', 'status', 'date_of_gen', 
               'date_of_purchase', 'date_of_expiry']
    signals_list = [dict(zip(columns, signal)) for signal in signals]
    
    return jsonify({'signals': signals_list})
# Endpoint to modify signal params
@app.route('/modify_signal', methods=['POST'])
def modify_signal():
    try:
        # Get the signal data from the request (which should be in JSON format)
        new_signal_data = request.get_json()

        # Extract individual values from the incoming signal data
        new_signal = Signal(new_signal_data)
        conn = sqlite3.connect('data/signals.db')
        cursor = conn.cursor()

        #Get the old data of the signal before the updates
        cursor.execute('SELECT * FROM signals WHERE id = ?', (new_signal.id,))
        old_signal_tuple = cursor.fetchone()
        columns = ['id', 'ticker', 'opening_price', 'generation_price', 'stop_loss', 'take_profit', 'risk',
                   'no_stocks', 'most_recent_price', 'status', 'date_of_gen', 'date_of_purchase', 'date_of_expiry']
        old_signal_dict = dict(zip(columns, old_signal_tuple))

        old_signal = Signal(old_signal_dict)
        updates = new_signal.compare(old_signal)
        if 'most_recent_price' in updates.keys() and old_signal.status == 2:
            updates['risk'] = (new_signal.most_recent_price - new_signal.stop_loss)/new_signal.most_recent_price

        if updates: 
            string_of_fields = ', '.join([f"{field} = ?" for field in updates.keys()])
            

            cursor.execute(f'''
                UPDATE signals SET {string_of_fields} WHERE id = ? 
            ''', (*updates.values(), new_signal.id))

            conn.commit()
        conn.close()

        return jsonify({'message': 'Signal modified successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

#Endpoint to flush database
@app.route('/flush_database', methods=['POST'])
def flush_database():
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect('data/signals.db')
        cursor = conn.cursor()

        # Fetch all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        # Truncate each table (delete all rows)
        for table in tables:
            table_name = table[0]
            if table_name != 'sqlite_sequence':  # Skip SQLite's internal table
                cursor.execute(f"DELETE FROM {table_name};")
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}';")  # Reset AUTOINCREMENT

        # Commit and close connection
        conn.commit()
        conn.close()

        return jsonify({'message': 'Database successfully flushed'}), 200

    except sqlite3.Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    
# Endpoint to add a signal
@app.route('/add_signal', methods=['POST'])
def add_signal():
    try:
        # Get the signal data from the request (which should be in JSON format)
        signal_data = request.get_json()
        
        signal = Signal(signal_data)

        # Validate input (optional)
        if not all([signal.ticker, signal.generation_price, signal.stop_loss, signal.take_profit, signal.risk, 
                    signal.no_stocks, signal.status, signal.date_of_gen]):
            return jsonify({'error': 'One of the signal parameters is missing'}), 400

        signal_dict = signal.to_dict()

        columns = [key for key, value in signal_dict.items() if value is not None] 
        values = [value for value in signal_dict.values() if value is not None]

        conn = sqlite3.connect('data/signals.db')
        cursor = conn.cursor()

        # Check for duplicate (ticker and status)
        cursor.execute('''
            SELECT COUNT(*) FROM signals WHERE ticker = ? AND status = ?
        ''', (signal.ticker, signal.status))
        duplicate_count = cursor.fetchone()[0]

        if duplicate_count > 0:
            conn.close()
            return jsonify({'error': 'A signal with the same ticker and status already exists'}), 400

        sql = f'''
            INSERT INTO signals ({', '.join(columns)}) 
            VALUES ({', '.join(['?' for _ in values])})
        '''

        # Insert signal data into the database
        
        cursor.execute(sql, values)
        conn.commit()
        conn.close()

        return jsonify({'message': 'Signal added successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
