
import telebot
from telebot import types
import requests

from config import TELEGRAM_TOKEN, TELEGRAM_BOT_NAME
from local_loader import JSONLoader

bot = telebot.TeleBot(TELEGRAM_TOKEN)

telegram_link = f"https://t.me/{TELEGRAM_BOT_NAME}"  # Замените 'YourBotUsername' на имя вашего бота

API_CREATE_USER_URL = 'http://10.0.0.4:4444/signin/create'
API_SAVE_CONTACT = 'http://10.0.0.4:4444/signin/contacts'
API_USER_VALIDATE = 'http://10.0.0.4:4444/entry/valudate'
API_USER_LOCATION = 'http://10.0.0.4:4444/entry/location'
API_USER_ENTRY = 'http://10.0.0.4:4444/entry/start'

loader = JSONLoader('data.json')

# Временное хранилище данных для /entry

def send_message_to_user(telegram_id, text):
    try:
        bot.send_message(chat_id=telegram_id, text=text)
        print(f"Сообщение отправлено пользователю {telegram_id}: {text}")
    except Exception as e:
        print(f"Ошибка при отправке сообщения пользователю {telegram_id}: {e}")


def menu_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    create_access_point_btn = types.KeyboardButton("Создать точку входа")
    markup.add(create_access_point_btn)
    return markup

def geodata_markap():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    location_button = types.KeyboardButton("Отправить локацию", request_location=True)
    markup.add(location_button)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    m_args = message.text.split()
    args = m_args[1].split('_')
    if len(args) < 2:
        # Если не указаны все необходимые аргументы
        bot.reply_to(message, loader.get_value("warning_registration_not_pasible"))
        return

    role = args[0]
    device_id = args[1]

    telegram_id = str(message.from_user.id)
    name = message.from_user.first_name

    payload = {
        'telegram_id': telegram_id,
        'device_id': device_id,
        'name': name,
        'role': role
    }

    response = requests.post(API_CREATE_USER_URL, data=payload)

    if response.status_code == 200:
        data = response.json()
        if data.get('msg') == "TRUE":
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            button = types.KeyboardButton(loader.get_value("message_user_phone"), request_contact=True)
            markup.add(button)

            bot.send_message(
                message.chat.id,
                loader.get_value("message_user_phone_get"),
                reply_markup=markup
            )
        else:
            bot.send_message(message.chat.id, loader.get_value("warning_allredy_registred"))
            if role == 'teacher':
                # Если роль преподаватель, показываем меню с кнопкой "Создать точку доступа"
                markup = menu_markup()
                bot.send_message(message.chat.id, loader.get_value("message_reg_as_teacher"), reply_markup=markup)
    else:
        print(f"Ошибка API: {response.status_code} - {response.text}")
        bot.send_message(message.chat.id, loader.get_value("error_reg_error"))


@bot.message_handler(content_types=['contact', 'text'])
def handle_contact_or_text(message):
    telegram_id = str(message.from_user.id)

    if message.text is not None and  message.text == "Создать точку входа":
        request_location_for_access_point(message)
        return

    if not message.contact or not message.contact.phone_number:
        return

    payload = {
        'telegram_id': telegram_id,
        'phone_number': message.contact.phone_number
    }

    response = requests.post(API_SAVE_CONTACT, data=payload)

    if response.status_code == 200:
        data = response.json()

        if data.get('msg') == "USER EXIST":
            bot.send_message(
                message.chat.id,
                loader.get_value("warning_start_reg")
            )
            return

        if data.get('msg') == "COMPLETEDT":
            if data.get('role') == 'teacher':
                markup = menu_markup()
            else:
                markup = types.ReplyKeyboardRemove()
            bot.send_message(message.chat.id,
                             loader.get_value("message_reg_complete"),
                             reply_markup=markup)

            return

        if data.get('msg') == "UNKNOWN":
            bot.send_message(message.chat.id, loader.get_value("error_unknown_reg"))
            return

        if data.get('msg') == "SAVED":
            bot.send_message(message.chat.id, loader.get_value("message_reg_success"))

            if data.get('role') == 'teacher':
                # Если роль преподаватель, показываем меню с кнопкой "Создать точку доступа"
                markup = menu_markup()
                bot.send_message(message.chat.id,
                                 loader.get_value("message_reg_as_teacher"),
                                 reply_markup=markup)
            else:
                # Если роль не "teacher", просто убираем клавиатуру и завершаем процесс
                markup = types.ReplyKeyboardRemove()
                bot.send_message(message.chat.id,
                                 loader.get_value("message_reg_thanks"),
                                 reply_markup=markup)
    else:
        print(f"Ошибка API: {response.status_code} - {response.text}")
        bot.send_message(message.chat.id,
                         loader.get_value("error_get_location"))





#@bot.message_handler(func=lambda message: message.text == "Создать точку входа")
def request_location_for_access_point(message):
    telegram_id = str(message.from_user.id)

    payload = {
        'telegram_id': telegram_id
    }

    response = requests.post(API_USER_VALIDATE, data=payload)

    if response.status_code == 200:
        data = response.json()
        if data.get('msg') == "USER EXIST":
            bot.send_message(message.chat.id,
                             loader.get_value("warning_user_not_found"))
            return

        if data.get('msg') == "NOT TEACHER":
            bot.send_message(message.chat.id,
                             loader.get_value("error_not_teacher"))
            return

        if data.get('msg') == "SUCCESS":
            markup = geodata_markap()

            bot.send_message(
                message.chat.id,
                loader.get_value("message_get_location"),
                reply_markup=markup
            )

    else:
        print(f"Ошибка API: {response.status_code} - {response.text}")
        bot.send_message(message.chat.id,
                         loader.get_value("error_get_location"))


# Хэндлер для получения локации
@bot.message_handler(content_types=['location'])
def handle_location(message):
    telegram_id = str(message.from_user.id)

    payload = {
        'telegram_id': telegram_id,
        'longitude' : message.location.longitude,
        'latitude' :message.location.latitude
    }

    response = requests.post(API_USER_LOCATION, data=payload)

    if response.status_code == 200:
        data = response.json()

        if data.get('msg') == "USER EXIST":
            bot.send_message(message.chat.id,
                             loader.get_value("warning_user_not_found"))
            return

        if data.get('msg') == "NOT TEACHER":
            bot.send_message(message.chat.id,
                             loader.get_value("error_cant_create_ep"))
            return

        if data.get('msg') == "ENTRYPOINT":
            markup = menu_markup()
            bot.send_message(message.chat.id,
                             f"{loader.get_value('message_ep_created')} \n {data.get('link')}",
                             reply_markup=markup)
            return

        if data.get('msg') == "NOENTRYDATA":
            bot.send_message(message.chat.id,
                             loader.get_value("error_no_ep_data"))
            return

        if data.get('msg') == "ALREADYENTERED":
            bot.send_message(message.chat.id,
                             loader.get_value("warning_already_entered"))

        if data.get('msg') == "ENTERED":
            bot.send_message(message.chat.id,
                             loader.get_value("message_entered"))
            message = f"{data.get('user_name')} Entered"
            send_message_to_user(data.get("creator_tid"), message)
            return

        if data.get('msg') == "TOOFAR":
            markup = geodata_markap()

            bot.send_message(message.chat.id,
                             loader.get_value("warning_too_far"),
                             reply_markup=markup)
            return

        if data.get('msg') == "NOLOCATION":
            markup = geodata_markap()
            bot.send_message(message.chat.id,
                             loader.get_value("error_get_location_drop"),
                             reply_markup=markup)
            return
    else:
        print(f"Ошибка API: {response.status_code} - {response.text}")
        bot.send_message(message.chat.id, loader.get_value("error_api"))

###################################
# Новый хэндлер для команды /entry #
###################################
@bot.message_handler(commands=['entry'])
def handle_entry(message):
    m_args = message.text.split()
    args = m_args[1].split('_')
    if len(args) < 2:
        # Если не указаны все необходимые аргументы
        bot.reply_to(message,
                     loader.get_value("error_only_qr"))
        return

    device_id = args[0]
    point_id = args[1]
    telegram_id = str(message.from_user.id)

    payload = {
        'telegram_id': telegram_id,
        'device_id': device_id,
        'point_id': point_id
    }

    response = requests.post(API_USER_VALIDATE, data=payload)

    if response.status_code == 200:
        data = response.json()

        if data.get('msg') == "USER EXIST":
            bot.send_message(message.chat.id,
                             loader.get_value("warning_user_not_found"))
            return

        if data.get('msg') == "WRONDEVICE":
            bot.send_message(message.chat.id,
                             loader.get_value("error_device"))
            return

        if data.get('msg') == "NOENTRYPOINT":
            bot.send_message(message.chat.id,
                             loader.get_value("error_no_point"))
            return

        markup = geodata_markap()

        bot.send_message(
            message.chat.id,
            loader.get_value("message_get_ep"),
            reply_markup=markup
        )

    else:
        print(f"Ошибка API: {response.status_code} - {response.text}")
        bot.send_message(message.chat.id,
                         loader.get_value("error_api"))




