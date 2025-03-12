#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Основной Flask-модуль системы управления автопарком.
Содержит маршруты и функции для веб-интерфейса.
"""
import os
import logging
import json
import sqlite3
from flask import Flask, render_template, request, jsonify, after_this_request

import db_operations

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Инициализация Flask-приложения
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_autopark")

# Добавление CORS-заголовков
@app.after_request
def add_cors_headers(response):
    """Добавляем заголовки CORS для доступа из браузера"""
    origin = request.headers.get('Origin')
    logger.info(f"Request from origin: {origin}")
    
    if origin:
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/')
def index():
    """Display vehicle information on web interface"""
    return render_template('index.html')

@app.route('/api/vehicles')
def get_vehicles():
    """API endpoint to get list of all vehicles"""
    try:
        vehicles = db_operations.get_all_vehicles()
        return jsonify(vehicles)
    except Exception as e:
        logger.error(f"Error getting vehicles: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/vehicle/<int:vehicle_id>')
def vehicle_info(vehicle_id):
    """API endpoint to get vehicle information"""
    try:
        vehicle = db_operations.get_vehicle(vehicle_id)
        if vehicle:
            return jsonify(vehicle)
        else:
            return jsonify({"error": "Vehicle not found"}), 404
    except Exception as e:
        logger.error(f"Error getting vehicle {vehicle_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/maintenance/<int:vehicle_id>')
def maintenance_history(vehicle_id):
    """API endpoint to get maintenance history"""
    try:
        maintenance = db_operations.get_maintenance_history(vehicle_id)
        repairs = db_operations.get_repairs(vehicle_id)
        return jsonify({
            "maintenance": maintenance,
            "repairs": repairs
        })
    except Exception as e:
        logger.error(f"Error getting maintenance history for vehicle {vehicle_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/fuel/<int:vehicle_id>')
def fuel_history(vehicle_id):
    """API endpoint to get fuel history and stats"""
    try:
        refueling = db_operations.get_refueling_history(vehicle_id)
        stats = db_operations.calculate_fuel_stats(vehicle_id)
        return jsonify({
            "refueling": refueling,
            "stats": stats
        })
    except Exception as e:
        logger.error(f"Error getting fuel history for vehicle {vehicle_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/update_mileage/<int:vehicle_id>', methods=['POST'])
def update_mileage(vehicle_id):
    """API endpoint to update vehicle mileage"""
    try:
        data = request.json
        if not data or 'mileage' not in data:
            return jsonify({"error": "No mileage data provided"}), 400
            
        mileage = int(data['mileage'])
        success = db_operations.update_vehicle_mileage(vehicle_id, mileage)
        
        if success:
            return jsonify({"status": "success", "message": f"Mileage updated to {mileage}"}), 200
        else:
            return jsonify({"error": "Failed to update mileage"}), 500
    except ValueError:
        return jsonify({"error": "Invalid mileage value"}), 400
    except Exception as e:
        logger.error(f"Error updating mileage for vehicle {vehicle_id}: {e}")
        return jsonify({"error": str(e)}), 500

# Обработка ошибок
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)