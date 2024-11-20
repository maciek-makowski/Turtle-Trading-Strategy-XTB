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
# status is integer but 0 - active, 1 - not active (waiting for purchase), 2 - expired 
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

    def to_dict(self):
        return vars(self)
    
    def compare(self, other_signal):
        if not isinstance(other_signal, Signal):
            raise ValueError("Cannot compare Signal with non-Signal object")
        
        differences = {}
        for self_val, field in self.to_dict().items():
            other_val = getattr(other_signal, field, None)           
            if self_val != other_val:
                differences[field] = other_val
        return differences



# Endpoint to get all active signals
@app.route('/get_active_signals', methods=['GET'])
def get_active_signals():
    conn = sqlite3.connect('data/signals.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM signals WHERE status == 0')
    signals = cursor.fetchall()
    conn.close()

    columns = ['id', 'ticker', 'opening_price', 'generation_price', 'stop_loss', 'take_profit', 'risk', 
               'no_stocks', 'most_recent_price', 'status', 'date_of_gen', 
               'date_of_purchase', 'date_of_expiry']
    signals_list = [dict(zip(columns, signal)) for signal in signals]
    
    return jsonify({'signals': signals_list})

# Endpoint to get all active signals
@app.route('/get_considered_signals', methods=['GET'])
def get_considered_signals():
    conn = sqlite3.connect('data/signals.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM signals WHERE status == 1 ORDER BY risk ASC')
    signals = cursor.fetchall()
    conn.close()

    columns = ['id', 'ticker', 'opening_price', 'generation_price', 'stop_loss', 'take_profit', 'risk', 
               'no_stocks', 'most_recent_price', 'status', 'date_of_gen', 
               'date_of_purchase', 'date_of_expiry']
    signals_list = [dict(zip(columns, signal)) for signal in signals]
    
    return jsonify({'signals': signals_list})
# Endpoint to modify all signal params
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
        cursor.execute('SELECT * FROM users WHERE id = ?', (id,))
        old_signal_data = cursor.fetchone()

        if not old_signal_data:
            return jsonify({'error': 'Signal not found'}), 404
        
        old_signal = Signal(old_signal_data)
        updates = new_signal.compare(old_signal)
        string_of_fields = ', '.join([f"{field} = ?" for field in updates.keys()])

        cursor.execute(f'''
            UPDATE signals SET {string_of_fields} WHERE id = {new_signal.id} 
        ''', updates.values())

        conn.commit()
        conn.close()

        return jsonify({'message': 'Signal modified successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

        signal_values = signal.to_dict().values()
        # Insert signal data into the database
        conn = sqlite3.connect('data/signals.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO signals (ticker, opening_price, generation_price, stop_loss, take_profit, risk, no_stocks, 
                               most_recent_price, status, date_of_gen, date_of_purchase, date_of_expiry)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', signal_values)
        conn.commit()
        conn.close()

        return jsonify({'message': 'Signal added successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
