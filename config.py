import os

# Считываем данные из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID_RAW = os.getenv("ADMIN_ID")
ADMIN_ID = int(ADMIN_ID_RAW) if ADMIN_ID_RAW else None

# Проверка, что секреты переданы
if not BOT_TOKEN:
    raise ValueError("ОШИБКА: Переменная BOT_TOKEN не найдена!")

if not ADMIN_ID:
    raise ValueError("ОШИБКА: Переменная ADMIN_ID не найдена!")