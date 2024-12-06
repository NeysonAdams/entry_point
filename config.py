import os
# Create dummy secret key so we can use sessions
SECRET_KEY = os.getenv("SECRET_KEY", "qwert1234trewq4321!")

# Specify the database file (SQLite)
DATABASE_FILE = os.getenv("DATABASE_FILE", "app.db")
SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_FILE}'

SQLALCHEMY_POOL_RECYCLE= 299
SQLALCHEMY_TRACK_MODIFICATIONS = False

SQLALCHEMY_ECHO = True

TELEGRAM_TOKEN = "7899648557:AAGIkFpLOByd4af96FtzAxmTI0OJalXu-z0"
TELEGRAM_BOT_NAME = "access_point_generator_bot"