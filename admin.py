from config import bot, admins, hobbies, personality_traits
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from utils import edit_message_markup_with_except, delete_message_with_except
from db import get_pending_verification_requests, get_user_profile, update_verification_request, update_user, \
    get_all_users, get_filtered_users

current_index = {}
pending_requests = {}
mailing_filters = {}


@bot.callback_query_handler(func=lambda callback: callback.data == "admin")
@bot.message_handler(commands=['admin'])
def admin_panel(message: Message | CallbackQuery) -> None:
    if message.from_user.id not in admins:
        return
    if isinstance(message, CallbackQuery):
        message = message.message

    delete_message_with_except(message)

    markup = InlineKeyboardMarkup(row_width=3)
    mailing_button = InlineKeyboardButton(text="Рассылка", callback_data="mailing")
    review_button = InlineKeyboardButton(text="Верификация", callback_data="review")
    markup.add(mailing_button, review_button)
    bot.send_message(message.chat.id, "Панель администратора", reply_markup=markup)


@bot.message_handler(commands=['prem'])
def give_premium(message: Message) -> None:
    if message.from_user.id not in admins:
        user = get_user_profile(message.from_user.id)
    else:
        try:
            user_id = message.text.split(' ')[1]
        except:
            bot.send_message(message.chat.id, "error")
            return
        user = get_user_profile(user_id)

    user.premium = True if not user.premium else False
    update_user(user)


@bot.callback_query_handler(func=lambda callback: callback.data == "send")
def get_users_to_send(callback: CallbackQuery) -> None:
    delete_message_with_except(callback.message)
    filters = mailing_filters[callback.from_user.id]
    if not filters:
        callback.data = "mailing"
        mailing(callback)
        return

    users = get_filtered_users(get_all_users(), filters)
    if not users:
        bot.answer_callback_query(callback.id, "Нет подходящих профилей")
        mailing(callback)
        return

    bot.send_message(callback.message.chat.id, "Напишите текст поста или stop для отмены")
    bot.register_next_step_handler(callback.message, send_to_users, users)


def send_to_users(message: Message, users):
    if message.text == "stop":
        admin_panel(message)
        return
    for user in users:
        try:
            bot.send_message(user.id, message.text)
        except:
            pass


@bot.callback_query_handler(func=lambda callback: callback.data == "mailing")
def mailing(callback: CallbackQuery) -> None:
    delete_message_with_except(callback.message)
    if not mailing_filters.get(callback.from_user.id):
        mailing_filters[callback.from_user.id] = {"personality": None, "hobby": None, "age": None, "city": None,
                                                  "gender": None}
    filters = mailing_filters[callback.from_user.id]
    markup = InlineKeyboardMarkup(row_width=1)
    button_1 = InlineKeyboardButton(text=f"Тип личности: {filters['personality'] or 'Любой'}",
                                    callback_data="filters_personality")
    button_2 = InlineKeyboardButton(text=f"Хобби: {filters['hobby'] or 'Любые'}", callback_data="filters_hobby")
    button_3 = InlineKeyboardButton(text=f"Возраст: {filters['age'] or 'Любой'}", callback_data="filters_age")
    button_4 = InlineKeyboardButton(text=f"Город: {filters['city'] or 'Любой'}", callback_data="filters_city")
    button_5 = InlineKeyboardButton(text=f"Пол: {filters['gender'] or 'Любой'}", callback_data="filters_gender")
    button_6 = InlineKeyboardButton(text="Начать рассылку", callback_data="send")
    button_7 = InlineKeyboardButton(text="Выход", callback_data="admin")
    markup.add(button_1, button_2, button_3, button_4, button_5, button_6, button_7)
    bot.send_message(callback.message.chat.id, "Фильтры для рассылки", reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith("filters"))
def edit_mailing_filters(callback: CallbackQuery) -> None:
    delete_message_with_except(callback.message)
    filters = mailing_filters[callback.from_user.id]
    if not filters:
        mailing(callback)
        return

    edit_filter = callback.data.split("_")[1]
    if filters[edit_filter]:
        filters[edit_filter] = None
        mailing(callback)
        return

    markup = InlineKeyboardMarkup(row_width=2)
    if edit_filter == "personality":
        buttons = []
        for personality in personality_traits:
            button = InlineKeyboardButton(text=personality, callback_data=f"sset_personality_{personality}")
            buttons.append(button)
        buttons.append(InlineKeyboardButton(text="Выход", callback_data="mailing"))
        markup.add(*buttons)
        bot.send_message(callback.message.chat.id, "Выберите тип личности:", reply_markup=markup)
    elif edit_filter == "hobby":
        buttons = []
        for hobby in hobbies:
            button = InlineKeyboardButton(text=hobby, callback_data=f"sset_hobby_{hobby}")
            buttons.append(button)
        buttons.append(InlineKeyboardButton(text="Выход", callback_data="mailing"))
        markup.add(*buttons)
        bot.send_message(callback.message.chat.id, "Выберите хобби:", reply_markup=markup)
    elif edit_filter == "age":
        bot.send_message(callback.message.chat.id, "Напишите диапазон возраста в виде двух чисел через пробел")
        bot.register_next_step_handler(callback.message, get_age_for_mailing, callback)
    elif edit_filter == "city":
        bot.send_message(callback.message.chat.id, "Напишите город", reply_markup=markup)
        bot.register_next_step_handler(callback.message, get_city_for_mailing, callback)
    elif edit_filter == "gender":
        button_1 = InlineKeyboardButton("Мужчина", callback_data="sset_gender_Мужчина")
        button_2 = InlineKeyboardButton("Женщина", callback_data="sset_gender_Женщина")
        markup.add(button_1, button_2)
        bot.send_message(callback.message.chat.id, "Выберите пол:", reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith("sset"))
def set_mailing_filters(callback: CallbackQuery) -> None:
    edit_filter = callback.data.split("_")[1]
    value = callback.data.split("_")[2]
    filters = mailing_filters[callback.from_user.id]
    if not filters:
        mailing(callback)
        return
    filters[edit_filter] = value
    mailing(callback)


def get_age_for_mailing(message: Message, callback) -> None:
    try:
        start_age = message.text.split(" ")[0]
        end_age = message.text.split(" ")[1]
    except:
        bot.send_message(message.chat.id, "error")
        mailing(callback)
        return
    filters = mailing_filters.get(message.from_user.id)
    if not filters:
        mailing(callback)
        return
    filters["age"] = start_age + "-" + end_age
    mailing(callback)


def get_city_for_mailing(message: Message, callback) -> None:
    city = message.text
    filters = mailing_filters.get(message.from_user.id)
    if not filters:
        mailing(callback)
        return
    filters["city"] = city
    mailing(callback)


@bot.callback_query_handler(func=lambda callback: callback.data == "review")
def review_requests(callback: CallbackQuery) -> None:
    if callback.from_user.id not in admins:
        return
    pending_requests[callback.message.chat.id] = get_pending_verification_requests()
    if not pending_requests[callback.message.chat.id]:
        bot.send_message(callback.message.chat.id, "Нет заявок на рассмотрение.")
        admin_panel(callback)
    else:
        current_index[callback.message.chat.id] = 0
        send_request(callback.message.chat.id)


def send_request(chat_id):
    request = pending_requests[chat_id][current_index[chat_id]]
    user = get_user_profile(request.user_id)
    markup = InlineKeyboardMarkup()
    approve_button = InlineKeyboardButton(text="Одобрить", callback_data=f"approve_{request.id}")
    reject_button = InlineKeyboardButton(text="Отклонить", callback_data=f"reject_{request.id}")
    next_button = InlineKeyboardButton(text="Следующий", callback_data="next")
    prev_button = InlineKeyboardButton(text="Предыдущий", callback_data="prev")
    exit_button = InlineKeyboardButton(text="Выход", callback_data="admin")
    markup.add(approve_button, reject_button, exit_button)
    if current_index[chat_id] > 0:
        markup.add(prev_button)
    if current_index[chat_id] < len(pending_requests[chat_id]) - 1:
        markup.add(next_button)
    bot.send_photo(chat_id, user.photo, caption=f"{user}", reply_markup=markup, parse_mode="HTML")


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_") or call.data in ["next",
                                                                                                           "prev"])
def handle_verification(callback: CallbackQuery) -> None:
    delete_message_with_except(callback.message)
    chat_id = callback.message.chat.id

    if callback.data.startswith("approve_"):
        request_id = callback.data.split('_')[1]
        reviewed_by = callback.from_user.username
        update_verification_request(request_id, 'approved', reviewed_by)
        bot.answer_callback_query(callback.id, "Заявка одобрена")
    elif callback.data.startswith("reject_"):
        request_id = callback.data.split('_')[1]
        reviewed_by = callback.from_user.username
        update_verification_request(request_id, 'rejected', reviewed_by)
        bot.answer_callback_query(callback.id, "Заявка отклонена")
    elif callback.data == "next":
        if current_index[chat_id] < len(pending_requests[chat_id]) - 1:
            current_index[chat_id] += 1
    elif callback.data == "prev":
        if current_index[chat_id] > 0:
            current_index[chat_id] -= 1

    send_request(chat_id)
