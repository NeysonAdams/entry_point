from flask import Flask
from models import db
from threading import Thread
from telegram_bot import bot

from signin  import signin
from qrgenerate import qrblueprint
from entry_point import entry_point_blueprint

app = Flask(__name__)
app.config.from_pyfile('config.py')
db.init_app(app)

app.register_blueprint(signin)
app.register_blueprint(qrblueprint)
app.register_blueprint(entry_point_blueprint)

@app.route("/")
def home():
    return "Entry Point! Wellcome"

if __name__ == '__main__':


    with app.app_context():
        db.drop_all()
        db.create_all()

    server_thread = Thread(target=lambda: app.run(host='0.0.0.0', port=4444))
    server_thread.start()

    bot.polling()

