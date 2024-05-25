from config import bot, admins
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from utils import edit_message_markup_with_except, delete_message_with_except
from db import get_pending_verification_requests, get_user_profile, update_verification_request


current_index = {}
pending_requests = {}


@bot.message_handler(commands=['review'])
def review_requests(message: Message) -> None:
    if message.from_user.id not in admins:
        return
    pending_requests[message.chat.id] = get_pending_verification_requests()
    if not pending_requests[message.chat.id]:
        bot.send_message(message.chat.id, "Нет заявок на рассмотрение.")
    else:
        current_index[message.chat.id] = 0
        send_request(message.chat.id)


def send_request(chat_id):
    request = pending_requests[chat_id][current_index[chat_id]]
    user = get_user_profile(request.user_id)
    markup = InlineKeyboardMarkup()
    approve_button = InlineKeyboardButton(text="Одобрить", callback_data=f"approve_{request.id}")
    reject_button = InlineKeyboardButton(text="Отклонить", callback_data=f"reject_{request.id}")
    next_button = InlineKeyboardButton(text="Следующий", callback_data="next")
    prev_button = InlineKeyboardButton(text="Предыдущий", callback_data="prev")
    markup.add(approve_button, reject_button)
    if current_index[chat_id] > 0:
        markup.add(prev_button)
    if current_index[chat_id] < len(pending_requests[chat_id]) - 1:
        markup.add(next_button)
    bot.send_photo(chat_id, user.photo, caption=f"{user}", reply_markup=markup, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_") or call.data in ["next", "prev"])
def handle_verification(callback: CallbackQuery) -> None:
    delete_message_with_except(callback.message)
    chat_id = callback.message.chat.id

    if callback.data.startswith("approve_"):
        request_id = callback.data.split('_')[1]
        reviewed_by = callback.from_user.username
        update_verification_request(request_id, 'approved', reviewed_by)
        bot.send_message(chat_id, "Заявка одобрена.")
    elif callback.data.startswith("reject_"):
        request_id = callback.data.split('_')[1]
        reviewed_by = callback.from_user.username
        update_verification_request(request_id, 'rejected', reviewed_by)
        bot.send_message(chat_id, "Заявка отклонена.")
    elif callback.data == "next":
        if current_index[chat_id] < len(pending_requests[chat_id]) - 1:
            current_index[chat_id] += 1
    elif callback.data == "prev":
        if current_index[chat_id] > 0:
            current_index[chat_id] -= 1

    send_request(chat_id)
