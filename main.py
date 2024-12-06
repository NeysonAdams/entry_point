from flask import Flask
from models import db
from telegram_bot import bot
from flask_security import Security, SQLAlchemyUserDatastore
import asyncio

from signin  import signin
from qrgenerate import qrblueprint
from entry_point import entry_point_blueprint

app = Flask(__name__)
app.config.from_pyfile('config.py')
db.init_app(app)

app.register_blueprint(signin)
app.register_blueprint(qrblueprint)
app.register_blueprint(entry_point_blueprint)

if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=4444, debug=True)
    bot.polling()
