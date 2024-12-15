import requests
from flask import Blueprint, render_template, redirect, request, url_for, jsonify
from models import Accesspoint, db, User
from telegram_bot import telegram_link

from datetime import datetime, timedelta
import time
import secrets
import math


entry_point_blueprint = Blueprint('entry_point_blueprint', __name__)

valid_tokens = {}
entry_data = {}


def is_within_radius(lat1, lon1, lat2, lon2, radius_meters=50):
    # Радиус Земли в метрах
    R = 6371000

    # Преобразуем градусы в радианы
    lat1_rad = math.radians(float(lat1))
    lon1_rad = math.radians(float(lon1))
    lat2_rad = math.radians(float(lat2))
    lon2_rad = math.radians(float(lon2))

    # Разница координат
    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    # Формула Гаверсина
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    distance = R * c  # расстояние в метрах

    return distance <= radius_meters


# Пример использования в контексте бота:
def verify_user_location(user_lat, user_lon, ap_lat, ap_lon):
    if is_within_radius(ap_lat, ap_lon, user_lat, user_lon, 50):
        return True
    else:
        return False

@entry_point_blueprint.route("/entry/create", methods=['GET'])
def create():
    point_id = request.args.get('id')

    entry_point = Accesspoint.query.filter_by(id=point_id).first()

    if not entry_point:
        return render_template("error.html", caption="Точка входа не найдена")

    token = secrets.token_urlsafe(16)
    valid_tokens[token] = time.time()

    link = url_for('entry_point_blueprint.page', token=token, point_id=point_id, _external=True)

    return redirect(link)

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

    entry_point = Accesspoint.query.filter_by(id=point_id).first()

    if not entry_point:
        return render_template("error.html", caption="Точка входа не найдена")

    title = "Точка Входа"
    description = "Просканируйте QR код"

    end_time = entry_point.creation_date + timedelta(minutes=5)
    now = datetime.utcnow()
    remaining_timedelta = end_time - now
    remaining_seconds = int(remaining_timedelta.total_seconds())

    qr_link =url_for("qrblueprint.get_key", point_id=point_id, _external=True)

    error_url = url_for("entry_point_blueprint.error", _external=True)

    # Если время не истекло, отдаём доступ
    return render_template("entry.html",
                           title=title,
                           description=description,
                           total_time=remaining_seconds,
                           qr_link=qr_link,
                           error_url=error_url)

@entry_point_blueprint.route("/entry/key/<token>/<point_id>", methods=['GET'])
def key(token, point_id):
    if token not in valid_tokens:
        return render_template("error.html", caption="Ключ дэактивирован попробуйте снова")

    creation_time = valid_tokens[token]
    current_time = time.time()

    if current_time - creation_time > 30:
        del valid_tokens[token]
        return render_template("error.html", caption="Время действия ссылки истекло")

    link = url_for(f"entry_point_blueprint.enter", token=token, point_id=point_id, _external=True)

    return render_template("unique.html", link=link)

@entry_point_blueprint.route("/entry/get/<token>/<point_id>",methods=['GET'])
def enter(token, point_id):
    if token not in valid_tokens:
        return render_template("error.html", caption="Ключ дэактивирован попробуйте снова")

    device_id = request.args.get('device_id')
    link = f"{telegram_link}?entry={device_id}_{point_id}"

    return redirect(link)

@entry_point_blueprint.route("/entry/error", methods=['GET'])
def error():
    render_template("error.html", caption="Время действия ссылки истекло")


@entry_point_blueprint.route("/entry/valudate", methods=['POST'])
def validate():
    telegram_id = request.form.get("telegram_id")

    user = db.session.query(User).filter_by(telegram_id=telegram_id).first()

    if not user:
        return jsonify(msg="USER EXIST"), 200

    if user.role != 'teacher':
        return jsonify(msg="NOT TEACHER"), 200

    user.registration_step = 'awaiting_ap_location'
    db.session.commit()

    return jsonify(msg="SUCCESS"), 200

@entry_point_blueprint.route("/entry/location", methods=['POST'])
def location():
    telegram_id = request.form.get("telegram_id")
    longitude = request.form.get("longitude")
    latitude = request.form.get("latitude")

    user = db.session.query(User).filter_by(telegram_id=telegram_id).first()

    if not user:
        return jsonify(msg="USER EXIST"), 200

    if user.registration_step == 'awaiting_ap_location':
        # Создание точки доступа
        if user.role != 'teacher':
            return jsonify(msg="NOT TEACHER"), 200

        new_access_point = Accesspoint(
            creation_date=datetime.utcnow(),
            longitude=str(longitude),
            latitude=str(latitude),
            creator_id=user.id
        )
        db.session.add(new_access_point)
        db.session.commit()

        user.registration_step = 'completed'
        db.session.commit()

        link = url_for("entry_point_blueprint.create", id=new_access_point.id, _external=True)

        return jsonify(msg="ENTRYPOINT", link=link), 200

    elif user.registration_step == 'awaiting_entry_location':
        # Проверка геоданных для входа
        if telegram_id not in entry_data:
            user.registration_step = 'completed'
            db.session.commit()
            return jsonify(msg="NOENTRYDATA"), 200

        point_id = entry_data[telegram_id]
        access_point = db.session.query(Accesspoint).filter_by(id=point_id).first()
        if not access_point:
            user.registration_step = 'completed'
            db.session.commit()
            del entry_data[telegram_id]
            return jsonify(msg="NOENTRYDATA"), 200

        if is_within_radius(access_point.latitude, access_point.longitude, longitude, longitude, 50):
            # Добавляем пользователя в список студентов точки доступа
            if user in access_point.students:
                return jsonify(msg="ALREADYENTERED"), 200
            user.registration_step = 'completed'
            access_point.students.append(user)
            db.session.commit()
            creator = db.session.query(User).filter_by(id=access_point.creator_id).first()
            return jsonify(msg="ENTERED", creator_tid=creator.telegram_id, user_name=user.name), 200
        else:
            user.registration_step = 'awaiting_entry_location'
            db.session.commit()
            return jsonify(msg="TOOFAR"), 200

    return jsonify(msg="NOLOCATION"), 200

@entry_point_blueprint.route("/entry/start", methods=['POST'])
def get_entry():
    telegram_id = request.form.get("telegram_id")
    device_id = request.form.get("device_id")
    point_id = request.form.get("point_id")

    user = db.session.query(User).filter_by(telegram_id=telegram_id).first()

    if not user:
        return jsonify(msg="USER EXIST"), 200

    if user.device_id != device_id:
        return jsonify(msg="WRONDEVICE"), 200

    access_point = db.session.query(Accesspoint).filter_by(id=point_id).first()
    if not access_point:
        return jsonify(msg="NOENTRYPOINT"), 200

    user.registration_step = 'awaiting_entry_location'
    db.session.commit()

    # Сохраняем point_id для дальнейшей проверки
    entry_data[telegram_id] = point_id

    return jsonify(msg="SUCCESS"), 200





