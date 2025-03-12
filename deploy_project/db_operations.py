#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для операций с базой данных.
Содержит функции для работы с транспортными средствами, ТО, ремонтами и заправками.
"""
import os
import sys
import logging
import sqlite3
import datetime
from typing import List, Dict, Optional, Tuple, Any

from config import DB_PATH

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def get_connection():
    """Get a connection to the SQLite database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def get_all_vehicles() -> List[Dict]:
    """
    Get all vehicles from the database
    
    Returns:
        List of dictionaries with vehicle data
    """
    conn = get_connection()
    vehicles = []
    
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM vehicles ORDER BY model')
        
        for row in cursor.fetchall():
            vehicle = dict(row)
            vehicles.append(vehicle)
            
    except Exception as e:
        logger.error(f"Error getting vehicles: {e}")
    finally:
        if conn:
            conn.close()
            
    return vehicles

def get_vehicle(vehicle_id: int) -> Optional[Dict]:
    """
    Get a vehicle by ID
    
    Args:
        vehicle_id (int): The vehicle ID
        
    Returns:
        Dictionary with vehicle data or None if not found
    """
    conn = get_connection()
    
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM vehicles WHERE id = ?', (vehicle_id,))
        row = cursor.fetchone()
        
        if row:
            vehicle = dict(row)
            
            # Расчет оставшегося пробега до следующего ТО
            if vehicle['mileage'] and vehicle['next_to']:
                vehicle['remaining_km'] = vehicle['next_to'] - vehicle['mileage']
            else:
                vehicle['remaining_km'] = None
                
            return vehicle
            
        return None
    
    except Exception as e:
        logger.error(f"Error getting vehicle {vehicle_id}: {e}")
        return None
    
    finally:
        if conn:
            conn.close()

def update_vehicle_mileage(vehicle_id: int, new_mileage: int) -> bool:
    """
    Update a vehicle's mileage
    
    Args:
        vehicle_id (int): The vehicle ID
        new_mileage (int): The new mileage value
        
    Returns:
        bool: True if updated successfully, False otherwise
    """
    conn = get_connection()
    
    try:
        # Проверяем текущий пробег
        cursor = conn.cursor()
        cursor.execute('SELECT mileage FROM vehicles WHERE id = ?', (vehicle_id,))
        row = cursor.fetchone()
        
        if not row:
            logger.error(f"Vehicle {vehicle_id} not found")
            return False
            
        current_mileage = row['mileage']
        
        # Проверяем, что новый пробег больше текущего
        if new_mileage <= current_mileage:
            logger.error(f"New mileage ({new_mileage}) must be greater than current mileage ({current_mileage})")
            return False
            
        # Обновляем пробег
        cursor.execute('UPDATE vehicles SET mileage = ? WHERE id = ?', (new_mileage, vehicle_id))
        conn.commit()
        
        logger.info(f"Updated mileage for vehicle {vehicle_id} from {current_mileage} to {new_mileage}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating mileage for vehicle {vehicle_id}: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

def add_vehicle(
    model: str, 
    reg_number: str, 
    vin: str = None,
    category: str = None,
    qualification: str = None,
    year: int = None,
    mileage: int = 0,
    tachograph_required: bool = False,
    osago_valid: str = None,
    tech_inspection_date: str = None,
    tech_inspection_valid: str = None,
    skzi_install_date: str = None,
    skzi_valid_date: str = None,
    next_to: int = None,
    last_to_date: str = None,
    next_to_date: str = None,
    fuel_type: str = None,
    fuel_tank_capacity: float = None,
    avg_fuel_consumption: float = None,
    notes: str = None
) -> int:
    """
    Add a new vehicle to the database
    
    Args:
        Multiple vehicle properties with enhanced fields
        
    Returns:
        int: The ID of the new vehicle, or -1 if an error occurred
    """
    conn = get_connection()
    
    try:
        cursor = conn.cursor()
        
        # Проверяем, существует ли ТС с таким же гос. номером
        cursor.execute('SELECT id FROM vehicles WHERE reg_number = ?', (reg_number,))
        if cursor.fetchone():
            logger.error(f"Vehicle with registration number {reg_number} already exists")
            return -1
            
        # Вставляем новое ТС
        cursor.execute('''
        INSERT INTO vehicles (
            model, reg_number, vin, category, qualification,
            year, mileage, tachograph_required, osago_valid, tech_inspection_date,
            tech_inspection_valid, skzi_install_date, skzi_valid_date, next_to,
            last_to_date, next_to_date, fuel_type, fuel_tank_capacity,
            avg_fuel_consumption, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            model, reg_number, vin, category, qualification,
            year, mileage, 1 if tachograph_required else 0, osago_valid, tech_inspection_date,
            tech_inspection_valid, skzi_install_date, skzi_valid_date, next_to,
            last_to_date, next_to_date, fuel_type, fuel_tank_capacity,
            avg_fuel_consumption, notes
        ))
        
        conn.commit()
        vehicle_id = cursor.lastrowid
        
        logger.info(f"Added new vehicle: {model} ({reg_number}) with ID {vehicle_id}")
        return vehicle_id
        
    except Exception as e:
        logger.error(f"Error adding vehicle: {e}")
        if conn:
            conn.rollback()
        return -1
        
    finally:
        if conn:
            conn.close()

def get_maintenance_history(vehicle_id: int) -> List[Dict]:
    """
    Get maintenance history for a vehicle
    
    Args:
        vehicle_id (int): The vehicle ID
        
    Returns:
        List of dictionaries with maintenance records
    """
    conn = get_connection()
    maintenance = []
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT * FROM maintenance 
        WHERE vehicle_id = ? 
        ORDER BY date DESC, mileage DESC
        ''', (vehicle_id,))
        
        for row in cursor.fetchall():
            record = dict(row)
            maintenance.append(record)
            
    except Exception as e:
        logger.error(f"Error getting maintenance history for vehicle {vehicle_id}: {e}")
    finally:
        if conn:
            conn.close()
            
    return maintenance

def get_repairs(vehicle_id: int) -> List[Dict]:
    """
    Get repair records for a vehicle
    
    Args:
        vehicle_id (int): The vehicle ID
        
    Returns:
        List of dictionaries with repair records
    """
    conn = get_connection()
    repairs = []
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT * FROM repairs 
        WHERE vehicle_id = ? 
        ORDER BY date DESC, mileage DESC
        ''', (vehicle_id,))
        
        for row in cursor.fetchall():
            record = dict(row)
            repairs.append(record)
            
    except Exception as e:
        logger.error(f"Error getting repairs for vehicle {vehicle_id}: {e}")
    finally:
        if conn:
            conn.close()
            
    return repairs

def add_repair(vehicle_id: int, date: str, mileage: int, description: str, cost: float = None) -> bool:
    """
    Add a repair record
    
    Args:
        vehicle_id (int): The vehicle ID
        date (str): Date of repair
        mileage (int): Mileage at repair
        description (str): Description of repair
        cost (float): Cost of repair
        
    Returns:
        bool: True if added successfully, False otherwise
    """
    conn = get_connection()
    
    try:
        cursor = conn.cursor()
        
        # Проверяем существование ТС
        cursor.execute('SELECT id FROM vehicles WHERE id = ?', (vehicle_id,))
        if not cursor.fetchone():
            logger.error(f"Vehicle {vehicle_id} not found")
            return False
            
        # Вставляем запись о ремонте
        cursor.execute('''
        INSERT INTO repairs (vehicle_id, date, mileage, description, cost)
        VALUES (?, ?, ?, ?, ?)
        ''', (vehicle_id, date, mileage, description, cost))
        
        conn.commit()
        
        logger.info(f"Added repair record for vehicle {vehicle_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error adding repair for vehicle {vehicle_id}: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

def get_refueling_history(vehicle_id: int) -> List[Dict]:
    """
    Get refueling records for a vehicle
    
    Args:
        vehicle_id (int): The vehicle ID
        
    Returns:
        List of dictionaries with refueling records
    """
    conn = get_connection()
    refueling = []
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT * FROM refueling 
        WHERE vehicle_id = ? 
        ORDER BY date DESC, mileage DESC
        ''', (vehicle_id,))
        
        for row in cursor.fetchall():
            record = dict(row)
            refueling.append(record)
            
    except Exception as e:
        logger.error(f"Error getting refueling history for vehicle {vehicle_id}: {e}")
    finally:
        if conn:
            conn.close()
            
    return refueling

def add_refueling(vehicle_id: int, date: str, mileage: int, liters: float, cost_per_liter: float) -> bool:
    """
    Add a refueling record
    
    Args:
        vehicle_id (int): The vehicle ID
        date (str): Date of refueling
        mileage (int): Mileage at refueling
        liters (float): Liters of fuel
        cost_per_liter (float): Cost per liter
        
    Returns:
        bool: True if added successfully, False otherwise
    """
    conn = get_connection()
    
    try:
        cursor = conn.cursor()
        
        # Проверяем существование ТС
        cursor.execute('SELECT id FROM vehicles WHERE id = ?', (vehicle_id,))
        if not cursor.fetchone():
            logger.error(f"Vehicle {vehicle_id} not found")
            return False
            
        # Вставляем запись о заправке
        cursor.execute('''
        INSERT INTO refueling (vehicle_id, date, mileage, liters, cost_per_liter)
        VALUES (?, ?, ?, ?, ?)
        ''', (vehicle_id, date, mileage, liters, cost_per_liter))
        
        conn.commit()
        
        logger.info(f"Added refueling record for vehicle {vehicle_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error adding refueling for vehicle {vehicle_id}: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

def calculate_fuel_stats(vehicle_id: int) -> Dict:
    """
    Calculate fuel statistics for a vehicle
    
    Args:
        vehicle_id (int): The vehicle ID
        
    Returns:
        Dictionary with fuel statistics
    """
    conn = get_connection()
    stats = {
        'total_fuel_liters': 0,
        'total_fuel_cost': 0,
        'avg_cost_per_liter': 0,
        'avg_consumption': 0
    }
    
    try:
        cursor = conn.cursor()
        
        # Получаем общее количество литров и стоимость
        cursor.execute('''
        SELECT SUM(liters) as total_liters, SUM(liters * cost_per_liter) as total_cost
        FROM refueling
        WHERE vehicle_id = ?
        ''', (vehicle_id,))
        
        row = cursor.fetchone()
        if row and row['total_liters']:
            stats['total_fuel_liters'] = float(row['total_liters'])
            stats['total_fuel_cost'] = float(row['total_cost'])
            stats['avg_cost_per_liter'] = round(stats['total_fuel_cost'] / stats['total_fuel_liters'], 1)
            
        # Получаем записи о заправках для расчета среднего расхода
        cursor.execute('''
        SELECT date, mileage, liters
        FROM refueling
        WHERE vehicle_id = ?
        ORDER BY date, mileage
        ''', (vehicle_id,))
        
        refueling_records = cursor.fetchall()
        
        # Расчет среднего расхода
        if len(refueling_records) >= 2:
            # Берем первую и последнюю запись для расчета расхода
            first_record = refueling_records[0]
            last_record = refueling_records[-1]
            
            # Получаем пробег между заправками
            mileage_diff = abs(last_record['mileage'] - first_record['mileage'])
            
            # Общее количество литров за этот период (кроме последней заправки)
            total_liters = 0
            for i in range(len(refueling_records) - 1):
                total_liters += refueling_records[i]['liters']
                
            # Расчет среднего расхода на 100 км
            if mileage_diff > 0:
                avg_consumption = (total_liters / mileage_diff) * 100
                stats['avg_consumption'] = round(avg_consumption, 1)
            
    except Exception as e:
        logger.error(f"Error calculating fuel stats for vehicle {vehicle_id}: {e}")
        
    finally:
        if conn:
            conn.close()
            
    return stats

def is_user_admin(user_id: int) -> bool:
    """
    Check if a user is an admin
    
    Args:
        user_id (int): Telegram user ID
        
    Returns:
        bool: True if the user is an admin, False otherwise
    """
    conn = get_connection()
    
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT is_admin FROM users WHERE telegram_id = ?', (user_id,))
        row = cursor.fetchone()
        
        if row and row['is_admin']:
            return True
            
        return False
        
    except Exception as e:
        logger.error(f"Error checking admin status for user {user_id}: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

def register_user(user_id: int, username: str, full_name: str, is_admin: bool = False) -> bool:
    """
    Register a new user or update existing user's information
    
    Args:
        user_id (int): Telegram user ID
        username (str): Username
        full_name (str): Full name
        is_admin (bool): Whether the user is an admin
        
    Returns:
        bool: True if registered/updated successfully, False otherwise
    """
    conn = get_connection()
    
    try:
        cursor = conn.cursor()
        
        # Проверяем, существует ли пользователь
        cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (user_id,))
        row = cursor.fetchone()
        
        today = datetime.datetime.now().strftime('%d.%m.%Y')
        
        if row:
            # Обновляем информацию о пользователе
            cursor.execute('''
            UPDATE users 
            SET username = ?, full_name = ?, last_activity = ?
            WHERE telegram_id = ?
            ''', (username, full_name, today, user_id))
            
            logger.info(f"Updated user {username} ({user_id})")
        else:
            # Регистрируем нового пользователя
            cursor.execute('''
            INSERT INTO users (telegram_id, username, full_name, is_admin, registration_date, last_activity)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, username, full_name, 1 if is_admin else 0, today, today))
            
            logger.info(f"Registered new user {username} ({user_id})")
            
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"Error registering/updating user {user_id}: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()