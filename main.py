from telebot import TeleBot
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from os import getenv
from dotenv import load_dotenv
import db

# Загрузка переменных окружения
load_dotenv()
TOKEN = getenv("BOT_TOKEN")
bot = TeleBot(TOKEN)


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


users: dict = {}
current_user_index: dict = {}


def delete_message_with_except(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass


def edit_message_markup_with_except(message):
    try:
        bot.edit_message_reply_markup(message.chat.id, message.message_id)
    except:
        pass


@bot.message_handler(commands=['start'])
def start(message: Message) -> None:
    edit_message_markup_with_except(message)

    keyboard = InlineKeyboardMarkup()
    if not db.user_exists(message.from_user.id):
        button = InlineKeyboardButton("Создать профиль", callback_data="create_profile")
        keyboard.add(button)

        bot.send_message(message.chat.id, "Добро пожаловать!\nДля продолжения работы с ботом вам необходимо "
                                          "создать профиль", reply_markup=keyboard)
    else:
        button = InlineKeyboardButton("Мой профиль", callback_data="profile")
        keyboard.add(button)
        bot.send_message(message.chat.id, "Добро пожаловать!", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data == 'create_profile')
def create_profile(callback: CallbackQuery) -> None:
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
def show_name(callback: CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if not user:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if not user:
            return

    if not user.name:
        get_name(callback)
        return

    edit_message_markup_with_except(callback.message)

    keyboard = InlineKeyboardMarkup()
    edit_button = InlineKeyboardButton("Изменить", callback_data="get_name")
    next_step_button = InlineKeyboardButton("Далее", callback_data="show_gender")
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
def get_name(callback: CallbackQuery, error=None) -> None:
    edit_message_markup_with_except(callback.message)

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


def set_name(message: Message, callback: CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if not user:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if not user:
            return

    if not message.text:
        delete_message_with_except(callback.message)
        get_name(callback, True)
        return

    user.name = message.text
    delete_message_with_except(message)

    if callback.data.endswith('once'):
        db.update_user(user)
        profile(callback)
        return

    show_name(callback)


@bot.callback_query_handler(func=lambda callback: callback.data == "show_gender")
def show_gender(callback: CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if not user:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if not user:
            return

    if not user.gender:
        choose_gender(callback)
        return

    edit_message_markup_with_except(callback.message)

    keyboard = InlineKeyboardMarkup()
    edit_button = InlineKeyboardButton("Изменить", callback_data="choose_gender")
    next_step_button = InlineKeyboardButton("Далее", callback_data="show_age")
    keyboard.add(edit_button, next_step_button)

    try:
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                              text=f"Ваш пол: {user.gender}", reply_markup=keyboard)
    except:
        bot.send_message(callback.message.chat.id, f"Ваш пол: {user.gender}", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('choose_gender'))
def choose_gender(callback: CallbackQuery) -> None:
    temp_callback_data = ""
    if callback.data.endswith('once'):
        temp_callback_data = "once"

    keyboard = InlineKeyboardMarkup()
    button = InlineKeyboardButton("Мужчина", callback_data="set_gender_" + temp_callback_data + "m")
    button_2 = InlineKeyboardButton("Женщина", callback_data="set_gender_" + temp_callback_data + "w")
    keyboard.add(button, button_2)
    try:
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                              text=f"Выберете свой пол", reply_markup=keyboard)
    except:
        bot.send_message(callback.message.chat.id, f"Выберете свой пол", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('set_gender'))
def set_gender(callback: CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if not user:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if not user:
            return

    if callback.data.endswith('w'):
        user.gender = "Женщина"
    else:
        user.gender = "Мужчина"

    if "once" in callback.data:
        db.update_user(user)
        profile(callback)
        return

    show_gender(callback)


@bot.callback_query_handler(func=lambda callback: callback.data == 'show_age')
def show_age(callback: CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if not user:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if not user:
            return

    if not user.age:
        get_age(callback)
        return

    edit_message_markup_with_except(callback.message)

    keyboard = InlineKeyboardMarkup()
    edit_button = InlineKeyboardButton("Изменить", callback_data="get_age")
    next_step_button = InlineKeyboardButton("Далее", callback_data="show_city")
    keyboard.add(edit_button, next_step_button)

    try:
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                              text=f"Ваш возраст: {user.age}", reply_markup=keyboard)
    except:
        bot.send_message(callback.message.chat.id, f"Ваш возраст: {user.age}", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('get_age'))
def get_age(callback: CallbackQuery, error=None) -> None:
    edit_message_markup_with_except(callback.message)

    _message_text = "Напишите свой возраст:" if not error else "Напишите свой возраст корректно:"

    try:
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                              text=_message_text)
    except:
        bot.send_message(callback.message.chat.id, _message_text)

    bot.register_next_step_handler(callback.message, set_age, callback)


def set_age(message: Message, callback: CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if not user:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if not user:
            return

    try:
        age = int(message.text)
        if age < 18 or age > 100:
            delete_message_with_except(message)
            get_age(callback, True)
            return
    except:
        delete_message_with_except(message)
        get_age(callback, True)
        return

    user.age = age
    delete_message_with_except(message)

    if callback.data.endswith('once'):
        db.update_user(user)
        profile(callback)
        return

    show_age(callback)


@bot.callback_query_handler(func=lambda callback: callback.data == 'show_city')
def show_city(callback: CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if not user:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if not user:
            return

    if not user.city:
        get_city(callback)
        return

    edit_message_markup_with_except(callback.message)

    keyboard = InlineKeyboardMarkup()
    edit_button = InlineKeyboardButton("Изменить", callback_data="get_city")
    next_step_button = InlineKeyboardButton("Далее", callback_data="show_about")
    keyboard.add(edit_button, next_step_button)

    try:
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                              text=f"Ваш город: {user.city}", reply_markup=keyboard)
    except:
        bot.send_message(callback.message.chat.id, f"Ваш город: {user.city}", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('get_city'))
def get_city(callback: CallbackQuery, error=None) -> None:
    edit_message_markup_with_except(callback.message)

    try:
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                              text="Напишите свой город:")
    except:
        bot.send_message(callback.message.chat.id, "Напишите свой город:")

    bot.register_next_step_handler(callback.message, set_city, callback)


def set_city(message: Message, callback: CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if not user:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if not user:
            return

    if not message.text:
        delete_message_with_except(message)
        get_city(callback, True)
        return

    user.city = message.text
    delete_message_with_except(message)

    if callback.data.endswith('once'):
        db.update_user(user)
        profile(callback)
        return

    show_city(callback)


@bot.callback_query_handler(func=lambda callback: callback.data == 'show_about')
def show_about(callback: CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if not user:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if not user:
            return

    if not user.about:
        get_about(callback)
        return

    edit_message_markup_with_except(callback.message)

    keyboard = InlineKeyboardMarkup()
    edit_button = InlineKeyboardButton("Изменить", callback_data="get_about")
    next_step_button = InlineKeyboardButton("Далее", callback_data="show_hobbies")
    keyboard.add(edit_button, next_step_button)

    try:
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                              text=f"О вас: {user.about}", reply_markup=keyboard)
    except:
        bot.send_message(callback.message.chat.id, f"О вас: {user.about}", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('get_about'))
def get_about(callback: CallbackQuery, error=None) -> None:
    edit_message_markup_with_except(callback.message)

    try:
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                              text="Расскажите о себе (не менее 5 символов):")
    except:
        bot.send_message(callback.message.chat.id, "Расскажите о себе (не менее 5 символов):")

    bot.register_next_step_handler(callback.message, set_about, callback)


def set_about(message: Message, callback: CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if not user:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if not user:
            return

    if len(message.text) < 5:
        bot.answer_callback_query(callback.id, "Недостаточно символов, попробуйте снова")
        get_about(callback)
        return

    if not message.text:
        delete_message_with_except(message)
        get_about(callback, True)
        return

    user.about = message.text
    delete_message_with_except(message)

    if callback.data.endswith('once'):
        db.update_user(user)
        profile(callback)
        return

    show_about(callback)


@bot.callback_query_handler(func=lambda callback: callback.data == "show_hobbies")
def show_hobbies(callback: CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if not user:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if not user:
            return

    if not user.hobbies:
        choose_hobbies(callback)
        return

    edit_message_markup_with_except(callback.message)

    keyboard = InlineKeyboardMarkup()
    edit_button = InlineKeyboardButton("Добавить/Удалить", callback_data="choose_hobbies")
    next_step_button = InlineKeyboardButton("Далее", callback_data="show_photo_registration")
    keyboard.add(edit_button, next_step_button)

    try:
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                              text=f"Ваши хобби: {', '.join(str(item) for item in user.hobbies)}",
                              reply_markup=keyboard)
    except:
        bot.send_message(callback.message.chat.id, f"Ваши хобби: {', '.join(str(item) for item in user.hobbies)}",
                         reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('choose_hobbies'))
def choose_hobbies(callback: CallbackQuery) -> None:
    temp_callback_data = ""
    if callback.data.endswith('once'):
        temp_callback_data = "once"

    keyboard = InlineKeyboardMarkup()
    hobbies = ["Спорт", "Творчество", "Природа", "Кулинария", "Гейминг", "Путешествия", "Технологии", "Духовность",
               "Коллекционирование"]
    buttons = []
    for hobby in hobbies:
        button = InlineKeyboardButton(hobby, callback_data=f"set_hobbies_{temp_callback_data}/{hobby}")
        buttons.append(button)
    keyboard.add(*buttons)

    try:
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                              text=f"Выберете свои хобби", reply_markup=keyboard)
    except:
        bot.send_message(callback.message.chat.id, f"Выберете свои хобби",
                         reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('set_hobbies'))
def set_hobbies(callback: CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if not user:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if not user:
            return

    if user.hobbies is None:
        user.hobbies = []

    hobby = callback.data.split('/')[1]
    if hobby not in user.hobbies:
        user.hobbies.append(hobby)
    else:
        user.hobbies.remove(hobby)

    # if len(user.hobbies) < 2:
    #     choose_hobbies(callback)
    #     return

    if "once" in callback.data:
        db.update_user(user)
        profile(callback)
        return

    show_hobbies(callback)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('show_photo'))
def show_photo(callback: CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if not user:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if not user:
            return

    if not user.photo:
        get_photo(callback)
        return

    edit_message_markup_with_except(callback.message)

    if callback.data.endswith('registration'):
        user = users.get(callback.from_user.id)
        if user:
            response = db.add_user(user)
            if response is False:
                start(callback.message)
        else:
            start(callback.message)

    keyboard = InlineKeyboardMarkup()
    edit_button = InlineKeyboardButton("Изменить", callback_data="get_photo")
    next_step_button = InlineKeyboardButton("Далее", callback_data="profile")
    keyboard.add(edit_button, next_step_button)
    bot.send_photo(callback.message.chat.id, user.photo, caption="Фото профиля", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('get_photo'))
def get_photo(callback: CallbackQuery) -> None:
    edit_message_markup_with_except(callback.message)

    try:
        temp_message = bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                                             text="Отправьте фото")
    except:
        temp_message = bot.send_message(callback.message.chat.id, "Отправьте фото")

    bot.register_next_step_handler(callback.message, set_photo, callback, temp_message)


def set_photo(message: Message, callback: CallbackQuery, temp_message) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if not user:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if not user:
            return

    if not message.photo:
        delete_message_with_except(message)
        delete_message_with_except(temp_message)
        get_photo(callback)
        return

    photo = message.photo[-1]
    file_info = bot.get_file(photo.file_id)
    photo_info = bot.download_file(file_info.file_path)

    user.photo = photo_info

    delete_message_with_except(message)
    delete_message_with_except(temp_message)

    if callback.data.endswith('once'):
        db.update_user(user)
        profile(callback)
        return

    show_photo(callback)


@bot.callback_query_handler(func=lambda callback: callback.data == 'profile')
def profile(callback: CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if not user:
        return

    edit_message_markup_with_except(callback.message)
    delete_message_with_except(callback.message)

    keyboard = InlineKeyboardMarkup()
    edit_button = InlineKeyboardButton("Изменить ✏️️", callback_data="edit_profile")
    tests_button = InlineKeyboardButton("Тесты 📝", callback_data="tests")
    match_button = InlineKeyboardButton("Мэтчи 🙋", callback_data="matches")
    search_button = InlineKeyboardButton("Поиск 🔍", callback_data="search")
    keyboard.add(edit_button, tests_button, match_button, search_button)

    if user.photo:
        bot.send_photo(callback.message.chat.id, user.photo, f"{user}", reply_markup=keyboard, parse_mode="HTML")
    else:
        callback.data = 'get_photo_once'
        get_photo(callback)
        # bot.send_message(callback.message.chat.id, f"У вас нет фото :(\nВаш профиль:\n{user}", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data == 'edit_profile')
def edit_profile(callback: CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if not user:
        return

    edit_message_markup_with_except(callback.message)
    delete_message_with_except(callback.message)

    keyboard = InlineKeyboardMarkup()
    name_button = InlineKeyboardButton("Имя", callback_data="get_name_once")
    gender_button = InlineKeyboardButton("Пол", callback_data="choose_gender_once")
    age_button = InlineKeyboardButton("Возраст", callback_data="get_age_once")
    city_button = InlineKeyboardButton("Город", callback_data="get_city_once")
    about_button = InlineKeyboardButton("О себе", callback_data="get_about_once")
    hobbies_button = InlineKeyboardButton("Хобби", callback_data="choose_hobbies_once")
    photo_button = InlineKeyboardButton("Фото", callback_data="get_photo_once")
    keyboard.add(name_button, gender_button, age_button, city_button, about_button, hobbies_button, photo_button)

    bot.send_message(callback.message.chat.id, 'Выберете поле для редактирования', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('search'))
def search(callback: CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if not user:
        return
    edit_message_markup_with_except(callback.message)
    keyboard = InlineKeyboardMarkup(row_width=1)
    if callback.data == 'search':
        basic_mode_button = InlineKeyboardButton("Обычный", callback_data="search_basic_mode")
        extended_mode_button = InlineKeyboardButton("Расширенный", callback_data="!search_extended_mode")
        business_mode_button = InlineKeyboardButton("Премиум 💎 [недоступен]",
                                                                  callback_data="!search_premium_mode")
        keyboard.add(basic_mode_button, extended_mode_button, business_mode_button)
        try:
            bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                                  text="Выберете режим поиска", reply_markup=keyboard)
        except:
            delete_message_with_except(callback.message)
            bot.send_message(callback.message.chat.id, 'Выберете режим поиска', reply_markup=keyboard)

    elif callback.data == 'search_basic_mode':
        basic_search(callback)
    elif callback.data == 'search_extended_mode':
        extended_search(callback)
    elif callback.data == 'search_premium_mode':
        premium_search(callback)


def basic_search(callback: CallbackQuery) -> None:
    available_users = db.get_users_who_liked_first(callback.from_user.id)
    if not available_users:
        available_users = db.get_users_with_no_interactions(callback.from_user.id)

    if available_users:
        current_user_index[callback.from_user.id] = (available_users, 0)
        send_next_profile(callback)
    else:
        bot.answer_callback_query(callback.id, "На данный момент для вас нет подходящих профилей")
        profile(callback)


def extended_search(callback: CallbackQuery) -> None:
    pass


def premium_search(callback: CallbackQuery) -> None:
    pass


def send_next_profile(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    if not current_user_index.get(user_id):
        basic_search(callback)
        return
    edit_message_markup_with_except(callback.message)
    delete_message_with_except(callback.message)

    available_users, index = current_user_index[user_id]

    if index < len(available_users):
        user = available_users[index]
        keyboard = InlineKeyboardMarkup(row_width=2)
        like_button = InlineKeyboardButton(text="👍", callback_data=f'reaction_{user.id}_like')
        dislike_button = InlineKeyboardButton(text="👎", callback_data=f'reaction_{user.id}_dislike')
        stop_button = InlineKeyboardButton(text="Выход", callback_data='profile')
        keyboard.add(like_button, dislike_button, stop_button)

        if user.photo:
            bot.send_photo(callback.message.chat.id, user.photo, f"{user}", reply_markup=keyboard, parse_mode="HTML")
        else:
            current_user_index[user_id] = (available_users, index + 1)
            send_next_profile(callback)
    else:
        basic_search(callback)


@bot.callback_query_handler(func=lambda call: call.data.startswith('reaction_'))
def handle_reaction(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    target_user_id = int(callback.data.split('_')[1])
    reaction_type = callback.data.split('_')[2]

    response = db.add_reaction(user_id, target_user_id, reaction_type)

    if response is True:
        if reaction_type == 'like' and db.check_match(user_id, target_user_id):
            delete_message_with_except(callback.message)
            bot.answer_callback_query(callback.id, "У вас МЭТЧ!", show_alert=True)
            db.add_match(user_id, target_user_id)
            db.add_match(target_user_id, user_id)
            send_match_info(user_id, target_user_id)
            send_match_info(target_user_id, user_id)
            return
        else:
            bot.answer_callback_query(callback.id, "Вы успешно оценили профиль!")
    else:
        bot.answer_callback_query(callback.id, "Произошла ошибка, попробуйте перезапустить поиск")

    delete_message_with_except(callback.message)
    if not current_user_index.get(user_id):
        basic_search(callback)
        return

    available_users, index = current_user_index[user_id]
    current_user_index[user_id] = (available_users, index + 1)
    send_next_profile(callback)


def send_match_info(user_id, target_user_id) -> None:
    try:
        keyboard = InlineKeyboardMarkup()
        accept_button = InlineKeyboardButton(text="Отправить контакт",
                                                           callback_data=f"match_{target_user_id}_accept")
        decline_button = InlineKeyboardButton(text="Отложить", callback_data="match_decline")
        keyboard.add(accept_button, decline_button)
        user = db.return_user_profile(target_user_id)
        bot.send_photo(user_id, user.photo, f"У вас новый мэтч!\n{user}", parse_mode="HTML", reply_markup=keyboard)
    except Exception as e:
        print(e)


@bot.callback_query_handler(func=lambda call: call.data.startswith('match_'))
def handle_match_reaction(callback: CallbackQuery) -> None:
    delete_message_with_except(callback.message)
    target_user_id = callback.data.split('_')[1]
    if callback.data.endswith('accept'):
        if callback.from_user.username:
            user = db.return_user_profile(callback.from_user.id)
            bot.send_photo(target_user_id, user.photo,
                           f"{user}\n\nВам пришло приглашение в ЛС\nhttps://t.me/{callback.from_user.username}",
                           parse_mode="HTML")
            bot.answer_callback_query(callback.id, "Вы успешно отправили свой контакт")
            db.delete_user_first_match(user)
        else:
            bot.answer_callback_query(callback.id, "Ошибка, у вас нет telegram username", show_alert=True)
    elif callback.data.endswith('match_decline'):
        bot.answer_callback_query(callback.id, "Вы сможете вернуться к ответу позже в своём профиле")

    if not current_user_index.get(callback.from_user.id):
        basic_search(callback)
        return

    available_users, index = current_user_index[callback.from_user.id]
    current_user_index[callback.from_user.id] = (available_users, index + 1)
    send_next_profile(callback)


@bot.callback_query_handler(func=lambda call: call.data.startswith('matches'))
def show_matches(callback: CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if not user:
        return
    match = db.get_user_first_match(user)
    if not match:
        bot.answer_callback_query(callback.id, "У вас пока нет новый мэтчей")
        return
    matched_user = match
    if not matched_user or callback.data == "matches_delete":
        db.delete_user_first_match(user)
        show_matches(callback)
        return
    if callback.data == "matches_send":
        # todo fix DRY
        if callback.from_user.username:
            user = db.return_user_profile(callback.from_user.id)
            bot.send_photo(matched_user.id, user.photo,
                           f"{user}\n\nВам пришло приглашение в ЛС\nhttps://t.me/{callback.from_user.username}",
                           parse_mode="HTML")
            bot.answer_callback_query(callback.id, "Вы успешно отправили свой контакт")
            db.delete_user_first_match(user)
            show_matches(callback)
            return
        else:
            bot.answer_callback_query(callback.id, "Ошибка, у вас нет telegram username", show_alert=True)
            profile(callback)
            return

    keyboard = InlineKeyboardMarkup()
    send_button = InlineKeyboardButton(text="Отправить контакт 👋", callback_data="matches_send")
    delete_button = InlineKeyboardButton(text="Удалить навсегда ❌", callback_data="matches_delete")
    keyboard.add(send_button, delete_button)
    bot.send_photo(callback.from_user.id, matched_user.photo, f"У вас мэтч! 🔥\n{matched_user}", reply_markup=keyboard,
                   parse_mode='HTML')


@bot.message_handler(content_types=['text'])
def text(message: Message) -> None:
    start(message)


if __name__ == '__main__':
    bot.polling(timeout=35)
