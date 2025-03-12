#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для инициализации базы данных.
Создает необходимые таблицы, если они не существуют.
"""
import os
import sys
import logging
import sqlite3
from config import DB_PATH

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def init_database():
    """
    Initialize the SQLite database and create necessary tables with enhanced schema
    """
    conn = None
    try:
        # Проверяем, существует ли база данных
        db_exists = os.path.exists(DB_PATH)
        
        # Подключаемся к базе данных (создаем, если не существует)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Создаем таблицу транспортных средств
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY,
            model TEXT NOT NULL,
            reg_number TEXT NOT NULL UNIQUE,
            vin TEXT,
            category TEXT,
            qualification TEXT,
            year INTEGER,
            mileage INTEGER DEFAULT 0,
            tachograph_required BOOLEAN DEFAULT 0,
            osago_valid TEXT,
            tech_inspection_date TEXT,
            tech_inspection_valid TEXT,
            skzi_install_date TEXT,
            skzi_valid_date TEXT,
            next_to INTEGER,
            last_to_date TEXT,
            next_to_date TEXT,
            fuel_type TEXT,
            fuel_tank_capacity REAL,
            avg_fuel_consumption REAL,
            notes TEXT
        )
        ''')
        
        # Создаем таблицу технического обслуживания
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS maintenance (
            id INTEGER PRIMARY KEY,
            vehicle_id INTEGER,
            date TEXT NOT NULL,
            mileage INTEGER NOT NULL,
            works TEXT NOT NULL,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
        )
        ''')
        
        # Создаем таблицу ремонтов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS repairs (
            id INTEGER PRIMARY KEY,
            vehicle_id INTEGER,
            date TEXT NOT NULL,
            mileage INTEGER NOT NULL,
            description TEXT NOT NULL,
            cost REAL,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
        )
        ''')
        
        # Создаем таблицу заправок
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS refueling (
            id INTEGER PRIMARY KEY,
            vehicle_id INTEGER,
            date TEXT NOT NULL,
            mileage INTEGER NOT NULL,
            liters REAL NOT NULL,
            cost_per_liter REAL NOT NULL,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
        )
        ''')
        
        # Создаем таблицу пользователей для Telegram бота
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            full_name TEXT,
            is_admin BOOLEAN DEFAULT 0,
            registration_date TEXT,
            last_activity TEXT
        )
        ''')
        
        # Фиксируем изменения
        conn.commit()
        
        # Добавляем тестовые данные, если база данных была создана только что
        if not db_exists:
            add_sample_data(conn)
            logger.info("Добавлены тестовые данные")
        
        logger.info("Database initialized successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    
    finally:
        if conn:
            conn.close()

def add_sample_data(conn):
    """
    Добавляет тестовые данные в базу данных
    
    Args:
        conn: SQLite connection
    """
    cursor = conn.cursor()
    
    # Добавляем тестовые транспортные средства
    vehicles = [
        (
            "ГАЗ-3295", "Т780ТК96", "X89329527COВR9016", "M2", "Автобусы (9-15 чел.)",
            2025, 50287, 1, "23.03.2026", "16.12.2024", "16.06.2025",
            "11.01.2023", "12.01.2026", 110000, None, "16.06.2025",
            "Дизель", 105, 24.1, "-"
        ),
        (
            "ГАЗ-3295А1", "А442ЕМ186", "XUL3295A1G0000091", "M2", "Автобусы (9-15 чел.)",
            2024, 123400, 1, "24.10.2025", None, "31.12.2024",
            None, "26.04.2026", 110000, "12.03.2025", "31.12.2024",
            "Бензин", 80, 15, "-"
        ),
        (
            "Toyota Land Cruiser", "С001АА96", "JTMHV05J904026031", "B", "Легковые",
            2020, 78500, 0, "15.08.2025", "15.08.2024", "15.08.2025",
            None, None, 15000, "10.02.2025", "15.07.2025",
            "Бензин", 95, 14.5, "Служебный автомобиль директора"
        )
    ]
    
    cursor.executemany('''
    INSERT INTO vehicles (
        model, reg_number, vin, category, qualification,
        year, mileage, tachograph_required, osago_valid, tech_inspection_date, tech_inspection_valid,
        skzi_install_date, skzi_valid_date, next_to, last_to_date, next_to_date,
        fuel_type, fuel_tank_capacity, avg_fuel_consumption, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', vehicles)
    
    # Добавляем тестовые заправки
    refueling = [
        (1, "15.12.2024", 48000, 80, 52.5),
        (1, "20.12.2024", 49000, 75, 53.2),
        (1, "28.12.2024", 50000, 70, 53.5),
        (8, "14.1.2025", 73000, 56, 53.7),
        (8, "19.1.2025", 71000, 56, 53.7),
        (8, "24.1.2025", 69000, 56, 53.7),
    ]
    
    cursor.executemany('''
    INSERT INTO refueling (
        vehicle_id, date, mileage, liters, cost_per_liter
    ) VALUES (?, ?, ?, ?, ?)
    ''', refueling)
    
    # Добавляем тестовые ремонты
    repairs = [
        (1, "10.12.2024", 47800, "Замена передних тормозных колодок", 5000),
        (1, "11.12.2024", 47900, "Замена масла и фильтра", 3500),
        (3, "05.01.2025", 77800, "Замена лобового стекла", 25000)
    ]
    
    cursor.executemany('''
    INSERT INTO repairs (
        vehicle_id, date, mileage, description, cost
    ) VALUES (?, ?, ?, ?, ?)
    ''', repairs)
    
    # Добавляем тестовые ТО
    maintenance = [
        (1, "15.11.2024", 45000, "Плановое ТО-2"),
        (3, "10.12.2024", 75000, "Плановое ТО-5")
    ]
    
    cursor.executemany('''
    INSERT INTO maintenance (
        vehicle_id, date, mileage, works
    ) VALUES (?, ?, ?, ?)
    ''', maintenance)
    
    # Добавляем тестовых пользователей
    users = [
        (123456789, "admin_user", "Администратор", 1, "01.01.2025", "12.03.2025"),
        (987654321, "user1", "Пользователь 1", 0, "01.01.2025", "12.03.2025")
    ]
    
    cursor.executemany('''
    INSERT INTO users (
        telegram_id, username, full_name, is_admin, registration_date, last_activity
    ) VALUES (?, ?, ?, ?, ?, ?)
    ''', users)
    
    # Фиксируем изменения
    conn.commit()

if __name__ == "__main__":
    init_database()