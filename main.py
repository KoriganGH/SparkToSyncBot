import telebot
import db
from os import getenv
from dotenv import load_dotenv


class LocalUserProfile:
    def __init__(self, user_id: int, telegram: str, first_name: str, photo: bytes):
        self.id: int = user_id
        self.telegram: str = telegram
        self.name: str = first_name
        self.photo: bytes = photo
        self.gender: str = None
        self.age: int = None
        self.city: str = None
        self.about: str = None
        self.hobbies: list = None


load_dotenv()
TOKEN = getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
users: dict = {}


@bot.message_handler(commands=['start'])
def start(message: telebot.types.Message) -> None:
    keyboard = telebot.types.InlineKeyboardMarkup()
    if not db.user_exists(message.from_user.id):
        button = telebot.types.InlineKeyboardButton("Создать профиль", callback_data="create_profile")
        keyboard.add(button)

        bot.send_message(message.chat.id, "Добро пожаловать!\nДля продолжения работы с ботом вам необходимо "
                                          "создать профиль", reply_markup=keyboard)
    else:
        button = telebot.types.InlineKeyboardButton("Мой профиль", callback_data="profile")
        keyboard.add(button)
        bot.send_message(message.chat.id, "Добро пожаловать!", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data == 'create_profile')
def create_profile(callback: telebot.types.CallbackQuery) -> None:
    if db.user_exists(callback.message.from_user.id):
        return

    bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                          text="Вы перешли в раздел создания профиля, следуйте инструкциям:")

    user_profile_photos = bot.get_user_profile_photos(callback.from_user.id)
    if user_profile_photos.total_count > 0:
        photo = user_profile_photos.photos[0][-1]
        file_info = bot.get_file(photo.file_id)
        photo = bot.download_file(file_info.file_path)
    else:
        photo = None

    user = LocalUserProfile(callback.from_user.id, callback.from_user.username, callback.from_user.first_name, photo)
    users[callback.from_user.id] = user

    show_name(callback)


@bot.callback_query_handler(func=lambda callback: callback == 'show_name')
def show_name(callback: telebot.types.CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if user is None:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if user is None:
            return

    if user.name is None:
        get_name(callback)
        return

    # todo найти ошибку
    try:
        bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id)
    except:
        pass

    keyboard = telebot.types.InlineKeyboardMarkup()
    edit_button = telebot.types.InlineKeyboardButton("Изменить", callback_data="get_name")
    next_step_button = telebot.types.InlineKeyboardButton("Далее", callback_data="show_gender")
    keyboard.add(edit_button, next_step_button)

    if callback.message.text.startswith("Добро"):
        bot.send_message(callback.message.chat.id, f"Ваше имя: {user.name}", reply_markup=keyboard)
    else:
        try:
            bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                                  text=f"Ваше имя: {user.name}", reply_markup=keyboard)
        except:
            bot.send_message(callback.message.chat.id, f"Ваше имя: {user.name}", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('get_name'))
def get_name(callback: telebot.types.CallbackQuery, error=None) -> None:
    # todo найти ошибку
    try:
        bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id)
    except:
        pass

    if callback.message.text.startswith("Добро"):
        bot.send_message(callback.message.chat.id, "Напишите своё имя:")
    else:
        if not error:
            try:
                bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                                      text="Напишите своё имя:")
            except:
                bot.send_message(callback.message.chat.id, "Напишите своё имя:")

    bot.register_next_step_handler(callback.message, set_name, callback)


def set_name(message: telebot.types.Message, callback: telebot.types.CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if user is None:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if user is None:
            return

    if message.text is None:
        bot.delete_message(callback.message.chat.id, message.message_id)
        get_name(callback, True)
        return
    user.name = message.text
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass
    if callback.data.endswith('once'):
        db.session.commit()
        profile(callback)
        return
    show_name(callback)


@bot.callback_query_handler(func=lambda callback: callback.data == "show_gender")
def show_gender(callback: telebot.types.CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if user is None:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if user is None:
            return

    if user.gender is None:
        choose_gender(callback)
        return

    # todo найти ошибку
    try:
        bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id)
    except:
        pass

    keyboard = telebot.types.InlineKeyboardMarkup()
    edit_button = telebot.types.InlineKeyboardButton("Изменить", callback_data="choose_gender")
    next_step_button = telebot.types.InlineKeyboardButton("Далее", callback_data="show_age")
    keyboard.add(edit_button, next_step_button)

    try:
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                              text=f"Ваш пол: {user.gender}", reply_markup=keyboard)
    except:
        bot.send_message(callback.message.chat.id, f"Ваш пол: {user.gender}", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('choose_gender'))
def choose_gender(callback: telebot.types.CallbackQuery) -> None:
    temp_callback_data = ""
    if callback.data.endswith('once'):
        temp_callback_data = "once"

    keyboard = telebot.types.InlineKeyboardMarkup()
    button = telebot.types.InlineKeyboardButton("Мужчина", callback_data="set_gender_" + temp_callback_data + "m")
    button_2 = telebot.types.InlineKeyboardButton("Женщина", callback_data="set_gender_" + temp_callback_data + "w")
    keyboard.add(button, button_2)
    try:
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                              text=f"Выберете свой пол", reply_markup=keyboard)
    except:
        bot.send_message(callback.message.chat.id, f"Выберете свой пол", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('set_gender'))
def set_gender(callback: telebot.types.CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if user is None:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if user is None:
            return

    if callback.data.endswith('w'):
        user.gender = "Женщина"
    else:
        user.gender = "Мужчина"

    if "once" in callback.data:
        db.session.commit()
        profile(callback)
        return

    show_gender(callback)


@bot.callback_query_handler(func=lambda callback: callback.data == 'show_age')
def show_age(callback: telebot.types.CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if user is None:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if user is None:
            return

    if user.age is None:
        get_age(callback)
        return

    # todo найти ошибку
    try:
        bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id)
    except:
        pass

    keyboard = telebot.types.InlineKeyboardMarkup()
    edit_button = telebot.types.InlineKeyboardButton("Изменить", callback_data="get_age")
    next_step_button = telebot.types.InlineKeyboardButton("Далее", callback_data="show_city")
    keyboard.add(edit_button, next_step_button)

    try:
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                              text=f"Ваш возраст: {user.age}", reply_markup=keyboard)
    except:
        bot.send_message(callback.message.chat.id, f"Ваш возраст: {user.age}", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('get_age'))
def get_age(callback: telebot.types.CallbackQuery, error=None) -> None:
    # todo найти ошибку
    try:
        bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id)
    except:
        pass
    _message_text = "Напишите свой возраст:" if not error else "Напишите свой возраст корректно:"

    try:
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                              text=_message_text)
    except:
        pass

    bot.register_next_step_handler(callback.message, set_age, callback)


def set_age(message: telebot.types.Message, callback: telebot.types.CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if user is None:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if user is None:
            return

    try:
        age = int(message.text)
        if age < 18 or age > 100:
            bot.delete_message(message.chat.id, message.message_id)
            get_age(callback, True)
            return
    except:
        bot.delete_message(message.chat.id, message.message_id)
        get_age(callback, True)
        return
    user.age = age
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    if callback.data.endswith('once'):
        db.session.commit()
        profile(callback)
        return

    show_age(callback)


@bot.callback_query_handler(func=lambda callback: callback.data == 'show_city')
def show_city(callback: telebot.types.CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if user is None:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if user is None:
            return

    if user.city is None:
        get_city(callback)
        return

    # todo найти ошибку
    try:
        bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id)
    except:
        pass

    keyboard = telebot.types.InlineKeyboardMarkup()
    edit_button = telebot.types.InlineKeyboardButton("Изменить", callback_data="get_city")
    next_step_button = telebot.types.InlineKeyboardButton("Далее", callback_data="show_about")
    keyboard.add(edit_button, next_step_button)

    try:
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                              text=f"Ваш город: {user.city}", reply_markup=keyboard)
    except:
        bot.send_message(callback.message.chat.id, f"Ваш город: {user.city}", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('get_city'))
def get_city(callback: telebot.types.CallbackQuery, error=None) -> None:
    # todo найти ошибку
    try:
        bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id)
    except:
        pass

    try:
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                              text="Напишите свой город:")
    except:
        bot.send_message(callback.message.chat.id, "Напишите свой город:")

    bot.register_next_step_handler(callback.message, set_city, callback)


def set_city(message: telebot.types.Message, callback: telebot.types.CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if user is None:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if user is None:
            return

    if not message.text:
        bot.delete_message(message.chat.id, message.message_id)
        get_city(callback, True)
        return

    user.city = message.text
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    if callback.data.endswith('once'):
        db.session.commit()
        profile(callback)
        return

    show_city(callback)


@bot.callback_query_handler(func=lambda callback: callback.data == 'show_about')
def show_about(callback: telebot.types.CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if user is None:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if user is None:
            return

    if user.about is None:
        get_about(callback)
        return

    # todo найти ошибку
    try:
        bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id)
    except:
        pass

    keyboard = telebot.types.InlineKeyboardMarkup()
    edit_button = telebot.types.InlineKeyboardButton("Изменить", callback_data="get_about")
    next_step_button = telebot.types.InlineKeyboardButton("Далее", callback_data="show_hobbies")
    keyboard.add(edit_button, next_step_button)

    try:
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                              text=f"О вас: {user.about}", reply_markup=keyboard)
    except:
        bot.send_message(callback.message.chat.id, f"О вас: {user.about}", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('get_about'))
def get_about(callback: telebot.types.CallbackQuery, error=None) -> None:
    # todo найти ошибку
    try:
        bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id)
    except:
        pass

    try:
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                              text="Расскажите о себе (не менее 5 символов):")
    except:
        bot.send_message(callback.message.chat.id, "Расскажите о себе (не менее 5 символов):")

    bot.register_next_step_handler(callback.message, set_about, callback)


def set_about(message: telebot.types.Message, callback: telebot.types.CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if user is None:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if user is None:
            return

    if len(message.text) < 5:
        bot.send_message(callback.message.chat.id, "Недостаточно символов, попробуйте снова")
        get_about(callback)
        return
    if not message.text:
        bot.delete_message(message.chat.id, message.message_id)
        get_about(callback, True)
        return

    user.about = message.text
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    if callback.data.endswith('once'):
        db.session.commit()
        profile(callback)
        return

    show_about(callback)


@bot.callback_query_handler(func=lambda callback: callback.data == "show_hobbies")
def show_hobbies(callback: telebot.types.CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if user is None:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if user is None:
            return

    if user.hobbies is None:
        choose_hobbies(callback)
        return

    # todo найти ошибку
    try:
        bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id)
    except:
        pass

    keyboard = telebot.types.InlineKeyboardMarkup()
    edit_button = telebot.types.InlineKeyboardButton("Изменить", callback_data="choose_hobbies")
    next_step_button = telebot.types.InlineKeyboardButton("Далее", callback_data="show_photo_registration")
    keyboard.add(edit_button, next_step_button)

    try:
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                              text=f"Ваши хобби: {user.hobbies}", reply_markup=keyboard)
    except:
        bot.send_message(callback.message.chat.id, f"Ваши хобби: {user.hobbies}", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('choose_hobbies'))
def choose_hobbies(callback: telebot.types.CallbackQuery) -> None:
    temp_callback_data = ""
    if callback.data.endswith('once'):
        temp_callback_data = "once"

    keyboard = telebot.types.InlineKeyboardMarkup()
    button = telebot.types.InlineKeyboardButton("Хобби 1", callback_data="set_hobbies_" + temp_callback_data + "/Хобби 1")
    button_2 = telebot.types.InlineKeyboardButton("Хобби 2", callback_data="set_hobbies_" + temp_callback_data + "/Хобби 2")
    button_3 = telebot.types.InlineKeyboardButton("Хобби 3", callback_data="set_hobbies_" + temp_callback_data + "/Хобби 3")
    keyboard.add(button, button_2, button_3)
    try:
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                              text=f"Выберете свои хобби (минимум 2, максимум 5)", reply_markup=keyboard)
    except:
        bot.send_message(callback.message.chat.id, f"Выберете свои хобби (минимум 2, максимум 5)", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('set_hobbies'))
def set_hobbies(callback: telebot.types.CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if user is None:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if user is None:
            return

    if user.hobbies is None:
        user.hobbies = []

    hobby = callback.data.split('/')[1]
    if hobby not in user.hobbies:
        user.hobbies.append(hobby)

    if "once" in callback.data:
        db.session.commit()
        profile(callback)
        return

    show_hobbies(callback)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('show_photo'))
def show_photo(callback: telebot.types.CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if user is None:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if user is None:
            return

    if user.photo is None:
        get_photo(callback)
        return

    # todo найти ошибку
    try:
        bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id)
    except:
        pass

    if callback.data.endswith('registration'):
        user = users.get(callback.from_user.id)
        new_user = db.UserProfile(id=user.id, name=user.name, age=user.age, city=user.city, about=user.about,
                                  telegram=user.telegram, photo=user.photo, gender=user.gender, hobbies=user.hobbies)
        db.session.add(new_user)
        db.session.commit()

    keyboard = telebot.types.InlineKeyboardMarkup()
    edit_button = telebot.types.InlineKeyboardButton("Изменить", callback_data="get_photo")
    next_step_button = telebot.types.InlineKeyboardButton("Далее", callback_data="profile")
    keyboard.add(edit_button, next_step_button)
    bot.send_photo(callback.message.chat.id, user.photo, caption="Фото профиля", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('get_photo'))
def get_photo(callback: telebot.types.CallbackQuery) -> None:
    # todo найти ошибку
    try:
        bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id)
    except:
        pass

    try:
        temp_message = bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                                             text="Отправьте фото")
    except:
        temp_message = bot.send_message(callback.message.chat.id, "Отправьте фото")

    bot.register_next_step_handler(callback.message, set_photo, callback, temp_message)


def set_photo(message: telebot.types.Message, callback: telebot.types.CallbackQuery, temp_message) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if user is None:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if user is None:
            return

    if message.photo is None:
        try:
            bot.delete_message(message.chat.id, message.message_id)
            bot.delete_message(message.chat.id, temp_message.message_id)
            get_photo(callback)
            return
        except:
            pass

    photo = message.photo[-1]
    file_info = bot.get_file(photo.file_id)
    photo_info = bot.download_file(file_info.file_path)

    user.photo = photo_info

    try:
        bot.delete_message(message.chat.id, message.message_id)
        bot.delete_message(message.chat.id, temp_message.message_id)
    except:
        pass

    if callback.data.endswith('once'):
        db.session.commit()
        profile(callback)
        return

    show_photo(callback)


@bot.callback_query_handler(func=lambda callback: callback.data == 'profile')
def profile(callback: telebot.types.CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if user is None:
        return

    try:
        bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id)
    except:
        pass
    try:
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
    except:
        pass
    keyboard = telebot.types.InlineKeyboardMarkup()
    button = telebot.types.InlineKeyboardButton("Изменить", callback_data="edit_profile")
    # button_2 = telebot.types.InlineKeyboardButton("Изменить", callback_data="get_about")
    keyboard.add(button)

    if user.photo is not None:
        bot.send_photo(callback.message.chat.id, user.photo, f"Профиль\n{user}", reply_markup=keyboard)
    else:
        # todo добавить обязательную установку фото
        bot.send_message(callback.message.chat.id, f"У вас нет фото :(\nВаш профиль:\n{user}", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data == 'edit_profile')
def edit_profile(callback: telebot.types.CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if user is None:
        return

    try:
        bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id)
    except:
        pass

    keyboard = telebot.types.InlineKeyboardMarkup()
    name_button = telebot.types.InlineKeyboardButton("Имя", callback_data="get_name_once")
    gender_button = telebot.types.InlineKeyboardButton("Пол", callback_data="choose_gender_once")
    age_button = telebot.types.InlineKeyboardButton("Возраст", callback_data="get_age_once")
    city_button = telebot.types.InlineKeyboardButton("Город", callback_data="get_city_once")
    about_button = telebot.types.InlineKeyboardButton("О себе", callback_data="get_about_once")
    photo_button = telebot.types.InlineKeyboardButton("Фото", callback_data="get_photo_once")
    keyboard.add(name_button, gender_button, age_button, city_button, about_button, photo_button)

    bot.send_message(callback.message.chat.id, 'Выберете поле для редактирования', reply_markup=keyboard)


@bot.message_handler(content_types=['text'])
def text(message: telebot.types.Message) -> None:
    start(message)


if __name__ == '__main__':
    bot.polling()
