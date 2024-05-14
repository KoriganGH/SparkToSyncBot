import telebot
from os import getenv
from dotenv import load_dotenv
import db

# Загрузка переменных окружения
load_dotenv()
TOKEN = getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)


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
def start(message: telebot.types.Message) -> None:
    edit_message_markup_with_except(message)

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

    edit_message_markup_with_except(callback.message)

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


def set_name(message: telebot.types.Message, callback: telebot.types.CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if user is None:
        user: LocalUserProfile = users.get(callback.from_user.id)
        if user is None:
            return

    if message.text is None:
        delete_message_with_except(callback.message)
        get_name(callback, True)
        return
    user.name = message.text
    delete_message_with_except(message)
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

    edit_message_markup_with_except(callback.message)

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

    edit_message_markup_with_except(callback.message)

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
    edit_message_markup_with_except(callback.message)

    _message_text = "Напишите свой возраст:" if not error else "Напишите свой возраст корректно:"

    try:
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                              text=_message_text)
    except:
        bot.send_message(callback.message.chat.id, _message_text)

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

    edit_message_markup_with_except(callback.message)

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
    edit_message_markup_with_except(callback.message)

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
        delete_message_with_except(message)
        get_city(callback, True)
        return

    user.city = message.text
    delete_message_with_except(message)

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

    edit_message_markup_with_except(callback.message)

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
    edit_message_markup_with_except(callback.message)

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
        delete_message_with_except(message)
        get_about(callback, True)
        return

    user.about = message.text
    delete_message_with_except(message)

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

    edit_message_markup_with_except(callback.message)

    keyboard = telebot.types.InlineKeyboardMarkup()
    edit_button = telebot.types.InlineKeyboardButton("Изменить", callback_data="choose_hobbies")
    next_step_button = telebot.types.InlineKeyboardButton("Далее", callback_data="show_photo_registration")
    keyboard.add(edit_button, next_step_button)

    try:
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                              text=f"Ваши хобби: {', '.join(str(item) for item in user.hobbies)}",
                              reply_markup=keyboard)
    except:
        bot.send_message(callback.message.chat.id, f"Ваши хобби: {', '.join(str(item) for item in user.hobbies)}",
                         reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('choose_hobbies'))
def choose_hobbies(callback: telebot.types.CallbackQuery) -> None:
    temp_callback_data = ""
    if callback.data.endswith('once'):
        temp_callback_data = "once"

    keyboard = telebot.types.InlineKeyboardMarkup()
    hobbies = ["Спорт", "Творчество", "Природа", "Кулинария", "Гейминг", "Путешествия", "Технологии", "Духовность",
               "Коллекционирование"]
    buttons = []
    for hobby in hobbies:
        button = telebot.types.InlineKeyboardButton(hobby, callback_data=f"set_hobbies_{temp_callback_data}/{hobby}")
        buttons.append(button)
    keyboard.add(*buttons)

    try:
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                              text=f"Выберете свои хобби", reply_markup=keyboard)
    except:
        bot.send_message(callback.message.chat.id, f"Выберете свои хобби",
                         reply_markup=keyboard)


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
    else:
        user.hobbies.remove(hobby)

    # if len(user.hobbies) < 2:
    #     choose_hobbies(callback)
    #     return

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

    edit_message_markup_with_except(callback.message)

    if callback.data.endswith('registration'):
        user = users.get(callback.from_user.id)
        if user is not None:
            try:
                new_user = db.UserProfile(id=user.id, name=user.name, age=user.age, city=user.city, about=user.about,
                                          telegram=user.telegram, photo=user.photo, gender=user.gender,
                                          hobbies=user.hobbies)
                db.session.add(new_user)
                db.session.commit()
            except:
                start(callback.message)
        else:
            start(callback.message)

    keyboard = telebot.types.InlineKeyboardMarkup()
    edit_button = telebot.types.InlineKeyboardButton("Изменить", callback_data="get_photo")
    next_step_button = telebot.types.InlineKeyboardButton("Далее", callback_data="profile")
    keyboard.add(edit_button, next_step_button)
    bot.send_photo(callback.message.chat.id, user.photo, caption="Фото профиля", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('get_photo'))
def get_photo(callback: telebot.types.CallbackQuery) -> None:
    edit_message_markup_with_except(callback.message)

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
        db.session.commit()
        profile(callback)
        return

    show_photo(callback)


@bot.callback_query_handler(func=lambda callback: callback.data == 'profile')
def profile(callback: telebot.types.CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if user is None:
        return

    edit_message_markup_with_except(callback.message)
    delete_message_with_except(callback.message)

    keyboard = telebot.types.InlineKeyboardMarkup()
    button = telebot.types.InlineKeyboardButton("Изменить", callback_data="edit_profile")
    search_button = telebot.types.InlineKeyboardButton("Начать поиск", callback_data="search")
    tests_button = telebot.types.InlineKeyboardButton("Тесты", callback_data="tests")
    keyboard.add(button, search_button, tests_button)

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

    edit_message_markup_with_except(callback.message)
    delete_message_with_except(callback.message)

    keyboard = telebot.types.InlineKeyboardMarkup()
    name_button = telebot.types.InlineKeyboardButton("Имя", callback_data="get_name_once")
    gender_button = telebot.types.InlineKeyboardButton("Пол", callback_data="choose_gender_once")
    age_button = telebot.types.InlineKeyboardButton("Возраст", callback_data="get_age_once")
    city_button = telebot.types.InlineKeyboardButton("Город", callback_data="get_city_once")
    about_button = telebot.types.InlineKeyboardButton("О себе", callback_data="get_about_once")
    hobbies_button = telebot.types.InlineKeyboardButton("Хобби", callback_data="choose_hobbies_once")
    photo_button = telebot.types.InlineKeyboardButton("Фото", callback_data="get_photo_once")
    keyboard.add(name_button, gender_button, age_button, city_button, about_button, hobbies_button, photo_button)

    bot.send_message(callback.message.chat.id, 'Выберете поле для редактирования', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith('search'))
def search(callback: telebot.types.CallbackQuery) -> None:
    user: db.UserProfile = db.return_user_profile(callback.from_user.id)
    if user is None:
        return
    edit_message_markup_with_except(callback.message)
    keyboard = telebot.types.InlineKeyboardMarkup()
    if callback.data == 'search':
        basic_mode_button = telebot.types.InlineKeyboardButton("Обычный", callback_data="search_basic_mode")
        business_mode_button = telebot.types.InlineKeyboardButton("Премиум [недоступен]",
                                                                  callback_data="!search_premium_mode")
        keyboard.add(basic_mode_button, business_mode_button)
        try:
            bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                                  text="Выберете режим поиска", reply_markup=keyboard)
        except:
            bot.send_message(callback.message.chat.id, 'Выберете режим поиска', reply_markup=keyboard)

    elif callback.data == 'search_basic_mode':
        basic_search(callback)
    elif callback.data == 'search_premium_mode':
        premium_search(callback)


def basic_search(callback: telebot.types.CallbackQuery) -> None:
    available_users = db.get_users_with_no_interactions(callback.from_user.id)
    if available_users:
        for user in available_users:
            keyboard = telebot.types.InlineKeyboardMarkup()
            like_button = telebot.types.InlineKeyboardButton(text="👍", callback_data=f'reaction_{user.id}_like')
            dislike_button = telebot.types.InlineKeyboardButton(text="👎", callback_data=f'reaction_{user.id}_dislike')
            keyboard.add(like_button, dislike_button)
            if user.photo is None:
                continue

            bot.send_photo(callback.message.chat.id, user.photo, f"Профиль\n{user}", reply_markup=keyboard)
    else:
        bot.send_message(callback.message.chat.id, 'На данный момент для вас нет подходящих профилей')


def premium_search(callback: telebot.types.CallbackQuery) -> None:
    pass


@bot.callback_query_handler(func=lambda call: call.data.startswith('reaction_'))
def handle_reaction(call):
    user_id = call.from_user.id
    target_user_id = int(call.data.split('_')[1])
    reaction_type = call.data.split('_')[2]

    try:
        new_reaction = db.reactions_table.insert().values(
            user_id=user_id,
            target_user_id=target_user_id,
            reaction=reaction_type
        )
        db.session.execute(new_reaction)
        db.session.commit()

    except Exception as e:
        print(e)

    bot.answer_callback_query(call.id, "Вы успешно оценили профиль!")


@bot.message_handler(content_types=['text'])
def text(message: telebot.types.Message) -> None:
    start(message)


if __name__ == '__main__':
    bot.polling(timeout=35)
