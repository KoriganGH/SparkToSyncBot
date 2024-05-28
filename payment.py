from config import bot, PAYMENT_KEY
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from telebot.types import LabeledPrice, PreCheckoutQuery
from db import get_user_profile, update_user
from utils import delete_message_with_except


@bot.callback_query_handler(func=lambda callback: callback.data == "buy")
def pay(callback: CallbackQuery):
    delete_message_with_except(callback.message)
    pay_button = InlineKeyboardButton("Купить (999,99)", pay=True)
    cancel_button = InlineKeyboardButton("Отмена", callback_data="profile")
    keyboard = InlineKeyboardMarkup()
    keyboard.add(pay_button, cancel_button)
    prices = [LabeledPrice(label="RUB", amount=99999)]
    bot.send_invoice(chat_id=callback.message.chat.id, title="Премиум",
                     description="Премиум статус дает доступ к "
                                 "дополнительному режиму поиска и "
                                 "новейшую модель CHAT GPT для "
                                 "определения вашей "
                                 "совместимости",
                     invoice_payload="premium",
                     provider_token=PAYMENT_KEY, currency="RUB", start_parameter="test", prices=prices, reply_markup=keyboard)


@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query: PreCheckoutQuery):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@bot.message_handler(content_types=["successful_payment"])
def process_successful_payment(message: Message):
    if message.successful_payment.invoice_payload == "premium":
        user = get_user_profile(message.chat.id)
        user.premium = True
        update_user(user)
        profile_button = InlineKeyboardButton("Вернуться в профиль", callback_data="profile")
        keyboard = InlineKeyboardMarkup()
        keyboard.add(profile_button)
        bot.send_message(message.chat.id, "Вы успешно приобрели премиум статус!", reply_markup=keyboard)
