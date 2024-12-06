from flask import Blueprint, render_template, redirect, request, url_for
from models import AccessPoint

from datetime import datetime, timedelta
import time
import secrets


entry_point_blueprint = Blueprint('entry_point_blueprint', __name__)

valid_tokens = {}

@entry_point_blueprint.route("/entry/create", methods=['GET'])
def create():
    point_id = request.args.get('id')

    entry_point = AccessPoint.query.filter_by(id=point_id).first()

    if not entry_point:
        return render_template("error.html", caption="Точка входа не найдена")

    token = secrets.token_urlsafe(16)
    valid_tokens[token] = time.time()

    link = url_for('entry/page', token=token, _external=True)

    return link

def create_key_token():
    token = secrets.token_urlsafe(16)
    valid_tokens[token] = time.time()
    return token

@entry_point_blueprint.route("/entry/page/<token>/<point_id>", methods=['GET'])
def page(token, point_id):
    if token not in valid_tokens:
        return render_template("error.html", caption="Время действия ссылки истекло")


    creation_time = valid_tokens[token]
    current_time = time.time()
    if current_time - creation_time > 300:
        del valid_tokens[token]
        return render_template("error.html", caption="Время действия ссылки истекло")

    entry_point = AccessPoint.query.filter_by(id=point_id).first()

    if not entry_point:
        return render_template("error.html", caption="Точка входа не найдена")

    title = "Точка Входа"
    description = "Просканируйте QR код"

    end_time = entry_point.creation_date + timedelta(minutes=5)
    now = datetime.utcnow()
    remaining_timedelta = end_time - now
    remaining_seconds = int(remaining_timedelta.total_seconds())

    qr_link =url_for("qr/key", point_id=point_id, _external=True)

    error_url = url_for("entry/error", _external=True)

    # Если время не истекло, отдаём доступ
    return render_template("entry.html",
                           title=title,
                           description=description,
                           total_time=remaining_seconds,
                           qr_link=qr_link,
                           error_url=error_url)

@entry_point_blueprint.route("/entry/key/<token>/<point_id>", methods=['GET'])
def key(token):
    if token not in valid_tokens:
        return render_template("error.html", caption="Ключ дэактивирован попробуйте снова")

    creation_time = valid_tokens[token]
    current_time = time.time()

    if current_time - creation_time > 30:
        del valid_tokens[token]
        return render_template("error.html", caption="Время действия ссылки истекло")

    # Если время не истекло, отдаём доступ
    return "Доступ разрешён! Вы успели перейти по ссылке."

@entry_point_blueprint.route("/entry/error", methods=['GET'])
def error():
    render_template("error.html", caption="Время действия ссылки истекло")