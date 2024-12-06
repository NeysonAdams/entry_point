from flask import Blueprint, render_template, redirect, request, url_for

from telegram_bot import  telegram_link
import base64

signin = Blueprint('signin', __name__)

@signin.route('/signin/teacher', methods=['GET'])
def teacher_signin():
    title = "Welcome to Our Service"
    description = "Please scan the QR code below to continue with the registration process."
    status="teacher"

    return render_template('signin.html', title=title, description=description, status=status)


@signin.route('/signin/student', methods=['GET'])
def teacher_signin():
    title = "Welcome to Our Service"
    description = "Please scan the QR code below to continue with the registration process."
    status = "student"

    return render_template('signin.html', title=title, description=description, status=status)

@signin.route('/sigin/redirect', methods=['GET'])
def redirect():
    status = request.args.get('status')
    link = url_for(f"signin/device?status={status}")

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
