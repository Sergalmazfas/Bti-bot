# Импортируем все из main (рабочая версия с Росреестром)
from main import app

# app уже определен в main.py с правильным webhook
# Просто экспортируем его для gunicorn
