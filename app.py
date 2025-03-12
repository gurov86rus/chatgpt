import os
from flask import Flask, render_template, jsonify, request
import db_operations as db
from db_init import init_database

# Initialize the database
init_database()

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "secret-key-for-flask-app")

@app.route('/')
def index():
    """Display vehicle information on web interface"""
    return render_template('index.html')

@app.route('/api/vehicles')
def get_vehicles():
    """API endpoint to get list of all vehicles"""
    vehicles = db.get_all_vehicles()
    return jsonify(vehicles)

@app.route('/api/vehicle/<int:vehicle_id>')
def vehicle_info(vehicle_id):
    """API endpoint to get vehicle information"""
    vehicle = db.get_vehicle(vehicle_id)
    
    if not vehicle:
        return jsonify({"error": "Vehicle not found"}), 404
    
    # Calculate remaining kilometers to next maintenance
    remaining_km = max(0, vehicle['next_to'] - vehicle['mileage']) if vehicle['next_to'] else None
    
    # Add remaining kilometers and format response
    vehicle_info = dict(vehicle)
    vehicle_info['remaining_km'] = remaining_km
    
    return jsonify(vehicle_info)

@app.route('/api/maintenance/<int:vehicle_id>')
def maintenance_history(vehicle_id):
    """API endpoint to get maintenance history"""
    maintenance = db.get_maintenance_history(vehicle_id)
    repairs = db.get_repairs(vehicle_id)
    
    history = {
        'maintenance': maintenance,
        'repairs': repairs
    }
    return jsonify(history)

@app.route('/api/fuel/<int:vehicle_id>')
def fuel_history(vehicle_id):
    """API endpoint to get fuel history and stats"""
    refueling = db.get_refueling_history(vehicle_id)
    stats = db.calculate_fuel_stats(vehicle_id)
    
    data = {
        'refueling': refueling,
        'stats': stats
    }
    return jsonify(data)

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    app.run(host='0.0.0.0', port=5000, debug=True)