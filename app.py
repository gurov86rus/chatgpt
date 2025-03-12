import os
import logging
from flask import Flask, render_template, jsonify, request, make_response
import db_operations as db
from db_init import init_database

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('web_application.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize the database
init_database()

# Get Replit domain
replit_domain = os.environ.get("REPLIT_DOMAINS", "").split(",")[0]
logger.info(f"Replit domain: {replit_domain}")

# Create Flask app
app = Flask(__name__, 
            static_folder='static',
            static_url_path='/static')
app.secret_key = os.environ.get("SESSION_SECRET", "secret-key-for-flask-app")

# CORS support for all routes
@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    logger.info(f"Request from origin: {origin}")
    
    # Allow all origins for now
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

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