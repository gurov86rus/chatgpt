#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

# Данные из документа
vehicle_data = [
    # Госномер, ОСАГО пройден, ОСАГО действителен, Техосмотр пройден, Техосмотр действителен
    ("О607АС196", "23.01.2025", "22.01.2026", None, "31.12.2024"),
    ("А442ЕМ186", "23.10.2024", "24.10.2025", None, "31.12.2024"),
    ("О874ЕУ196", "24.02.2025", "23.02.2026", "18.10.2024", "18.10.2025"),
    ("Т780ТК96", "24.03.2025", "23.03.2026", "16.12.2024", "16.06.2025"),
    ("Х445ОЕ96", "24.02.2025", "23.02.2026", "15.11.2024", "15.05.2025"),
    ("О535ЕО196", "23.03.2025", "22.03.2026", "25.10.2024", "25.10.2025"),
    ("М823ВМ186", "10.11.2024", "09.11.2025", "08.10.2024", "08.10.2026"),
    ("О610АС196", "23.01.2025", "22.01.2026", "19.02.2025", "19.02.2027"),
    ("Н728МЕ196", "23.01.2025", "22.01.2026", "19.02.2025", "19.02.2027"),
    ("Т796УА96", "23.05.2024", "22.05.2025", "19.02.2025", "19.02.2026"),
    ("Х117СК96", "28.03.2025", "27.03.2026", "04.02.2021", "05.08.2021"),
    ("5772ЕВ66", "09.12.2024", "08.12.2025", "13.08.2024", "31.08.2025")
]

def update_vehicle_data():
    conn = sqlite3.connect('vehicles.db')
    cursor = conn.cursor()
    
    # Получаем список всех автомобилей с их ID и госномерами
    cursor.execute("SELECT id, reg_number FROM vehicles")
    current_vehicles = {reg_number: vehicle_id for vehicle_id, reg_number in cursor.fetchall()}
    
    print(f"Найдено {len(current_vehicles)} автомобилей в базе данных")
    
    # Счетчики для статистики
    updated_count = 0
    skipped_count = 0
    not_found_count = 0
    error_count = 0
    
    for reg_number, osago_date, osago_valid, tech_date, tech_valid in vehicle_data:
        if reg_number in current_vehicles:
            try:
                vehicle_id = current_vehicles[reg_number]
                
                # Обновляем данные для этого автомобиля
                cursor.execute(
                    "UPDATE vehicles SET osago_valid = ?, tech_inspection_date = ?, tech_inspection_valid = ? WHERE id = ?",
                    (osago_valid, tech_date, tech_valid, vehicle_id)
                )
                
                print(f"✅ Обновлен автомобиль {reg_number} (ID: {vehicle_id}):")
                print(f"   ОСАГО до: {osago_valid}")
                print(f"   Техосмотр пройден: {tech_date or 'не указано'}")
                print(f"   Техосмотр до: {tech_valid}")
                print()
                
                updated_count += 1
            except Exception as e:
                print(f"❌ Ошибка при обновлении автомобиля {reg_number}: {e}")
                error_count += 1
        else:
            print(f"⚠️ Автомобиль с госномером {reg_number} не найден в базе данных")
            not_found_count += 1
    
    # Сохраняем изменения
    conn.commit()
    conn.close()
    
    # Выводим итоговую статистику
    print("\n=== Итоги обновления ===")
    print(f"✅ Обновлено автомобилей: {updated_count}")
    print(f"⚠️ Не найдено автомобилей: {not_found_count}")
    print(f"❌ Ошибок при обновлении: {error_count}")
    
    return updated_count, not_found_count, error_count

if __name__ == "__main__":
    print("Запуск обновления данных автомобилей...")
    update_vehicle_data()
    print("Обновление завершено!")