#!/bin/bash

# Остановка всех существующих процессов бота
echo "Останавливаем все процессы бота..."
pkill -f "python.*telegram"
pkill -f "python.*bot"
sleep 2

# Сброс webhook через curl
echo "Сбрасываем webhook..."
TOKEN=$(printenv TELEGRAM_BOT_TOKEN)
curl -s "https://api.telegram.org/bot$TOKEN/deleteWebhook?drop_pending_updates=true"
echo

# Запуск минимального тестового бота
echo "Запускаем минимальный тестовый бот..."
python minimal_test_bot.py