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
    try:
        if not os.path.exists(os.path.dirname(DB_PATH)) and os.path.dirname(DB_PATH):
            os.makedirs(os.path.dirname(DB_PATH))
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Создаем расширенную таблицу для транспортных средств
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT NOT NULL,
            reg_number TEXT NOT NULL UNIQUE,
            vin TEXT,
            category TEXT,
            qualification TEXT,
            year INTEGER,
            mileage INTEGER DEFAULT 0,
            tachograph_required INTEGER DEFAULT 0,
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
        
        # Создаем таблицу для истории технического обслуживания
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS maintenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            mileage INTEGER NOT NULL,
            works TEXT NOT NULL,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
        )
        ''')
        
        # Создаем таблицу для истории ремонтов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS repairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            mileage INTEGER NOT NULL,
            description TEXT NOT NULL,
            cost REAL,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
        )
        ''')
        
        # Создаем таблицу для истории заправок
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS refueling (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            mileage INTEGER NOT NULL,
            liters REAL NOT NULL,
            cost_per_liter REAL NOT NULL,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
        )
        ''')
        
        # Создаем таблицу для пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            full_name TEXT,
            is_admin INTEGER DEFAULT 0,
            registration_date TEXT,
            last_activity TEXT
        )
        ''')
        
        conn.commit()
        
        # Проверка, пуста ли таблица vehicles
        cursor.execute("SELECT COUNT(*) FROM vehicles")
        count = cursor.fetchone()[0]
        
        # Если таблица пуста, добавляем тестовые данные
        if count == 0:
            logger.info("База данных пуста, добавляем демонстрационные данные")
            add_sample_data(conn)
        
        logger.info("Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

def add_sample_data(conn):
    """
    Добавляет тестовые данные в базу данных
    
    Args:
        conn: SQLite connection
    """
    try:
        cursor = conn.cursor()
        
        # Добавляем несколько тестовых автомобилей
        vehicles = [
            # ID = 1
            (
                'ГАЗ-3302', 'А123ВС96', 'X96330200M2746007', 'N1',
                'Грузовые до 3,5 тонн', 2021, 45000, 1,
                '12.09.2025', '15.03.2024', '15.09.2024',
                '10.01.2022', '10.01.2025', 65000,
                '10.01.2024', '10.05.2024', 'Бензин',
                75.0, 13.5, 'Тестовый автомобиль'
            ),
            # ID = 2
            (
                'Лада Веста', 'В456АВ66', 'XTA21129010123456', 'M1',
                'Легковые', 2020, 28000, 0,
                '05.06.2025', '01.12.2023', '01.06.2024',
                None, None, 38000,
                '01.12.2023', '01.06.2024', 'Бензин',
                55.0, 8.2, 'Тестовый легковой автомобиль'
            ),
            # ID = 3
            (
                'КамАЗ-5320', 'О789НП96', 'X895320CDNR12345', 'N3',
                'Грузовые свыше 12 тонн', 2019, 120500, 1,
                '18.11.2024', '20.10.2023', '20.04.2024',
                '20.11.2021', '20.11.2024', 140500,
                '20.10.2023', '20.04.2024', 'Дизель',
                350.0, 32.0, 'Тестовый грузовик'
            ),
            # ID = 4
            (
                'УАЗ Патриот', 'У321МК96', 'X7J3163300K123456', 'M1G',
                'Легковые повышенной проходимости', 2022, 15000, 0,
                '30.07.2025', '05.02.2024', '05.08.2024',
                None, None, 25000,
                '05.02.2024', '05.08.2024', 'Бензин',
                68.0, 11.5, 'Тестовый внедорожник'
            ),
            # ID = 5
            (
                'Toyota Camry', 'К777КК96', 'JT153BEA100123456', 'M1',
                'Легковые', 2023, 8500, 0,
                '15.05.2026', '10.01.2025', '10.07.2025',
                None, None, 18500,
                '10.01.2025', '10.07.2025', 'Бензин',
                60.0, 7.5, 'Тестовый автомобиль представительского класса'
            ),
            # ID = 6
            (
                'ГАЗ-3295А1', 'А442ЕМ186', 'XUL3295A1G0000091', 'M2',
                'Автобусы (9-15 чел.)', 2024, 123400, 1,
                '24.10.2025', None, '31.12.2024',
                None, '26.04.2026', 110000,
                '12.03.2025', '31.12.2024', 'Бензин',
                80.0, 15.0, '-'
            ),
            # ID = 7
            (
                'ПАЗ-32053', 'А583ТС66', 'XIM320539T0000067', 'M3',
                'Автобусы (>15 чел.)', 2025, 192500, 1,
                '25.04.2026', None, '16.01.2025',
                '12.06.2023', '12.06.2026', 140000,
                None, '11.05.2025', 'Дизель',
                120.0, 19.0, '-'
            ),
            # ID = 8
            (
                'ГАЗ-3295', 'Т780ТК96', 'X89329527COВR9016', 'M2',
                'Автобусы (9-15 чел.)', 2025, 50287, 1,
                '23.03.2026', '16.12.2024', '16.06.2025',
                '11.01.2023', '12.01.2026', 110000,
                None, '16.06.2025', 'Дизель',
                105.0, 24.1, '-'
            )
        ]
        
        for vehicle in vehicles:
            cursor.execute('''
            INSERT INTO vehicles (
                model, reg_number, vin, category, qualification, year, mileage,
                tachograph_required, osago_valid, tech_inspection_date,
                tech_inspection_valid, skzi_install_date, skzi_valid_date,
                next_to, last_to_date, next_to_date, fuel_type,
                fuel_tank_capacity, avg_fuel_consumption, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', vehicle)
            
        # Добавляем тестовые записи ТО
        maintenance = [
            (1, '10.01.2023', 15000, 'Замена масла, фильтров'),
            (1, '15.07.2023', 30000, 'Полное ТО, замена технических жидкостей'),
            (1, '10.01.2024', 45000, 'Замена масла, фильтров, свечей зажигания'),
            (2, '10.06.2023', 10000, 'Плановое ТО'),
            (2, '01.12.2023', 20000, 'Полное ТО, замена тормозных колодок'),
            (3, '20.04.2023', 100000, 'Полное ТО'),
            (3, '20.10.2023', 120000, 'Замена масла, фильтров, ремонт тормозной системы')
        ]
        
        for record in maintenance:
            cursor.execute('''
            INSERT INTO maintenance (vehicle_id, date, mileage, works)
            VALUES (?, ?, ?, ?)
            ''', record)
            
        # Добавляем тестовые записи ремонтов
        repairs = [
            (1, '05.03.2023', 20000, 'Замена лобового стекла', 15000.00),
            (1, '20.09.2023', 35000, 'Ремонт коробки передач', 35000.00),
            (2, '15.08.2023', 15000, 'Замена тормозных дисков', 12000.00),
            (3, '10.06.2023', 110000, 'Ремонт двигателя', 150000.00)
        ]
        
        for record in repairs:
            cursor.execute('''
            INSERT INTO repairs (vehicle_id, date, mileage, description, cost)
            VALUES (?, ?, ?, ?, ?)
            ''', record)
            
        # Добавляем тестовые записи заправок
        refueling = [
            (1, '01.01.2024', 40000, 50.0, 51.5),
            (1, '15.01.2024', 41000, 45.0, 51.8),
            (1, '30.01.2024', 42000, 55.0, 52.0),
            (2, '05.01.2024', 25000, 35.0, 51.5),
            (2, '20.01.2024', 26000, 40.0, 51.8),
            (3, '10.01.2024', 115000, 200.0, 56.2),
            (3, '25.01.2024', 117000, 250.0, 56.5),
            (8, '14.1.2025', 73000, 56.0, 53.7),
            (8, '19.1.2025', 71000, 56.0, 53.7),
            (8, '24.1.2025', 69000, 56.0, 53.7)
        ]
        
        for record in refueling:
            cursor.execute('''
            INSERT INTO refueling (vehicle_id, date, mileage, liters, cost_per_liter)
            VALUES (?, ?, ?, ?, ?)
            ''', record)
            
        # Добавляем тестовых пользователей
        users = [
            (12345, 'admin', 'Администратор Системы', 1, '01.01.2023', '01.03.2023'),
            (67890, 'user1', 'Петр Иванов', 0, '10.01.2023', '05.03.2023'),
            (54321, 'user2', 'Иван Петров', 0, '15.01.2023', '05.03.2023')
        ]
        
        for user in users:
            cursor.execute('''
            INSERT INTO users (telegram_id, username, full_name, is_admin, registration_date, last_activity)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', user)
            
        conn.commit()
        logger.info("Sample data added successfully")
        
    except Exception as e:
        logger.error(f"Error adding sample data: {e}")
        conn.rollback()

if __name__ == "__main__":
    init_database()