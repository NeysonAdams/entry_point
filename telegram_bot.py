from datetime import datetime
import telebot
from telebot import types

from config import TELEGRAM_TOKEN, TELEGRAM_BOT_NAME
from models import db, User, AccessPoint

bot = telebot.TeleBot(TELEGRAM_TOKEN)

telegram_link = f"https://t.me/{TELEGRAM_BOT_NAME}"  # Замените 'YourBotUsername' на имя вашего бота

@bot.message_handler(commands=['start'])
def send_welcome(message):
    args = message.text.split()
    if len(args) < 3:
        # Если не указаны все необходимые аргументы
        bot.reply_to(message, "Пожалуйста, используйте формат: /start <role> <device_id>")
        return

    role = args[1]
    device_id = args[2]

    telegram_id = str(message.from_user.id)
    name = message.from_user.first_name

    # Проверяем, есть ли пользователь в базе данных
    user = db.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        bot.send_message(message.chat.id, "Вы уже зарегистрированы!")
    else:
        # Создаем нового пользователя с доступными данными
        new_user = User(
            device_id=device_id,
            telegram_id=telegram_id,
            name=name,
            role=role,
            registration_step='awaiting_phone'
        )
        db.add(new_user)
        db.commit()

        # Запрашиваем номер телефона
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        button = types.KeyboardButton('📞 Поделиться номером телефона', request_contact=True)
        markup.add(button)

        bot.send_message(
            message.chat.id,
            "Пожалуйста, поделитесь вашим номером телефона для завершения регистрации.",
            reply_markup=markup
        )

@bot.message_handler(content_types=['contact', 'text'])
def handle_contact_or_text(message):
    telegram_id = str(message.from_user.id)
    user = db.query(User).filter_by(telegram_id=telegram_id).first()

    if not user:
        bot.send_message(
            message.chat.id,
            "Пожалуйста, начните регистрацию"
        )
        return

    if user.registration_step == 'awaiting_phone':
        if message.contact and message.contact.phone_number:
            # Обновляем номер телефона пользователя
            user.phone_number = message.contact.phone_number
            user.registration_step = 'completed'
            db.commit()

            bot.send_message(message.chat.id, "Регистрация прошла успешно!")

            if user.role == 'teacher':
                # Если роль преподаватель, показываем меню с кнопкой "Создать точку доступа"
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                create_access_point_btn = types.KeyboardButton("Создать точку входа")
                markup.add(create_access_point_btn)
                bot.send_message(message.chat.id, "Вы вошли как преподаватель. Выберите действие:", reply_markup=markup)
            else:
                # Если роль не "teacher", просто убираем клавиатуру и завершаем процесс
                markup = types.ReplyKeyboardRemove()
                bot.send_message(message.chat.id, "Спасибо за регистрацию!", reply_markup=markup)

        else:
            bot.send_message(
                message.chat.id,
                "Пожалуйста, поделитесь вашим номером телефона, нажав на кнопку ниже."
            )
    elif user.registration_step == 'completed':
        bot.send_message(message.chat.id, "Вы уже завершили регистрацию!")
    else:
        bot.send_message(message.chat.id, "Неизвестный этап регистрации. Пожалуйста, начните заново")


@bot.message_handler(func=lambda message: message.text == "Создать точку доступа")
def request_location_for_access_point(message):
    telegram_id = str(message.from_user.id)
    user = db.query(User).filter_by(telegram_id=telegram_id).first()

    if not user:
        bot.send_message(message.chat.id, "Пользователь не найден. Пожалуйста, пройдите регистрацию.")
        return

    if user.role != 'teacher':
        bot.send_message(message.chat.id, "Вы не являетесь преподавателем!")
        return

    user.registration_step = 'awaiting_ap_location'
    db.commit()

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    location_button = types.KeyboardButton("Отправить мою локацию", request_location=True)
    markup.add(location_button)

    bot.send_message(
        message.chat.id,
        "Пожалуйста, поделитесь вашей геопозицией для создания точки доступа.",
        reply_markup=markup
    )

# Хэндлер для получения локации
@bot.message_handler(content_types=['location'])
def handle_location(message):
    telegram_id = str(message.from_user.id)
    user = db.query(User).filter_by(telegram_id=telegram_id).first()

    if not user:
        bot.send_message(message.chat.id, "Пользователь не найден. Пожалуйста, начните регистрацию заново.")
        return

    if user.role != 'teacher':
        bot.send_message(message.chat.id, "Вы не можете создать точку доступа, так как вы не преподаватель.")
        return

    if user.registration_step == 'awaiting_ap_location':
        longitude = message.location.longitude
        latitude = message.location.latitude

        new_access_point = AccessPoint(
            creation_date=datetime.utcnow(),
            longitude=str(longitude),
            latitude=str(latitude),
            creator_id=user.id
        )
        db.add(new_access_point)
        db.commit()

        user.registration_step = 'completed'
        db.commit()

        markup = types.ReplyKeyboardRemove()
        bot.send_message(
            message.chat.id,
            f"Точка доступа успешно создана!",
            reply_markup=markup
        )
    else:
        bot.send_message(message.chat.id, "Мы не запрашивали у вас локацию для точки доступа.")