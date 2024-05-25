from config import bot


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
