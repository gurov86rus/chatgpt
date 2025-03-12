import os
from flask import Flask, render_template, jsonify
from vehicle_data import get_vehicle_card, get_maintenance_history, vehicle_data

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "secret-key-for-flask-app")

@app.route('/')
def index():
    """Display vehicle information on web interface"""
    return render_template('index.html')

@app.route('/api/vehicle-info')
def vehicle_info():
    """API endpoint to get vehicle information"""
    info = {
        'model': vehicle_data['model'],
        'number': vehicle_data['number'],
        'vin': vehicle_data['vin'],
        'mileage': vehicle_data['mileage'],
        'next_to': vehicle_data['next_to'],
        'last_to': vehicle_data['last_to'],
        'next_to_date': vehicle_data['next_to_date'],
        'osago_valid': vehicle_data['osago_valid'],
        'tachograph_required': vehicle_data['tachograph_required'],
        'remaining_km': max(0, vehicle_data['next_to'] - vehicle_data['mileage'])
    }
    return jsonify(info)

@app.route('/api/maintenance-history')
def maintenance_history():
    """API endpoint to get maintenance history"""
    history = {
        'to_history': vehicle_data['to_history'],
        'repairs': vehicle_data['repairs']
    }
    return jsonify(history)

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    app.run(host='0.0.0.0', port=5000, debug=True)