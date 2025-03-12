#!/bin/bash

# Убиваем все запущенные экземпляры бота
pkill -f "python.*bot" || true
echo "Все запущенные боты остановлены"
sleep 2

# Запускаем новый бот
echo "Запускаем самый простой бот..."
python simplest_bot.py