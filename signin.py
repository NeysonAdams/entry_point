from flask import Blueprint, render_template, redirect, request, url_for, jsonify
from models import db, User
from telegram_bot import  telegram_link

signin = Blueprint('signin', __name__)

@signin.route('/signin/teacher', methods=['GET'])
def teacher_signin():
    title = "Welcome to Our Service"
    description = "Please scan the QR code below to continue with the registration process."
    status="teacher"

    return render_template('signin.html', title=title, description=description, status=status)


@signin.route('/signin/student', methods=['GET'])
def student_signin():
    title = "Welcome to Our Service"
    description = "Please scan the QR code below to continue with the registration process."
    status = "student"

    return render_template('signin.html', title=title, description=description, status=status)

@signin.route('/sigin/redirect', methods=['GET'])
def redirect_page():
    status = request.args.get('status')
    link = url_for(f"signin.device_signin", status=status, _external=True)

    return render_template("unique.html", link=link)

@signin.route('/signin/device', methods=['GET'])
def device_signin():
    # Извлекаем параметры status и device_id из query parameters
    status = request.args.get('status')
    device_id = request.args.get('device_id')

    # Формируем ссылку для редиректа
    link = f"{telegram_link}?start={status}_{device_id}"
    # Выполняем редирект на сформированную ссылку
    return redirect(link)


@signin.route('/signin/create', methods=['POST'])
def create_user():
    telegram_id = request.form.get("telegram_id")
    device_id = request.form.get("device_id")
    name = request.form.get ("name")
    role = request.form.get ("role")

    user = db.session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        #bot.send_message(message.chat.id, "Вы уже зарегистрированы!")
        return jsonify(msg="FALSE"), 200
    # Создаем нового пользователя с доступными данными
    new_user = User(
            device_id=device_id,
            telegram_id=telegram_id,
            name=name,
            role=role,
            registration_step='awaiting_phone'
        )
    db.session.add(new_user)
    db.session.commit()

    return jsonify(msg="TRUE"), 200

@signin.route('/signin/contacts', methods=['POST'])
def contacts():
    telegram_id = request.form.get("telegram_id")
    phone_number = request.form.get("phone_number")

    user = db.session.query(User).filter_by(telegram_id=telegram_id).first()

    if not user:
        return jsonify(msg="USER EXIST"), 200

    if user.registration_step == 'completed':
        return jsonify(msg="COMPLETED", role=user.role), 200

    if user.registration_step == 'awaiting_phone':
        user.phone_number = phone_number
        user.registration_step = 'completed'
        db.session.commit()

        return jsonify(msg="SAVED", role=user.role), 200

    return jsonify(msg="UNKNOWN"), 200