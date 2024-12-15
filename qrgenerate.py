from flask import Blueprint, url_for, request, jsonify
from entry_point import create_key_token

import qrcode
import base64
import os

qrblueprint = Blueprint('qrblueprint', __name__)

@qrblueprint.route("/qr", methods=['GET'])
def get_qr():
    status = request.args.get('status')

    # Предположим, что эндпоинт для редиректа называется redirect_to_device
    # в блюпринте signin
    link = url_for("signin.redirect_page", status=status, _external=True)

    img = qrcode.make(link)

    img_dir = os.path.join('static', 'images')
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)

    img_filename = f'qr_code_{status}.png'
    img_path = os.path.join(img_dir, img_filename)
    img.save(img_path)

    img_url = url_for('static', filename=f'images/{img_filename}', _external=True)

    return jsonify(qr_code_url= img_url, redirect_url=link), 200

@qrblueprint.route("/qr/key/<point_id>", methods=['GET'])
def get_key(point_id):
    token = create_key_token()
    link = url_for('entry_point_blueprint.key', token=token, point_id=point_id, _external=True)
    print(link)
    img = qrcode.make(link)

    # Убедимся, что директория 'static/images' существует
    img_dir = os.path.join('static', 'images')
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)

    # Сохраняем изображение в 'static/images/qr_code.png'
    img_filename = f'qr_code_entry_point_{token}.png'
    img_path = os.path.join(img_dir, img_filename)
    img.save(img_path)

    # Генерируем URL к сохраненному изображению
    img_url = url_for('static', filename=f'images/{img_filename}', _external=True)

    return jsonify(qr_code_url= img_url, redirect_url=link), 200