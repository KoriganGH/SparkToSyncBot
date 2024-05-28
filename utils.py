from config import bot, translator


def translate_ru_to_eng(text: str) -> str:
    result = translator.translate_text(text, target_lang="EN-US")
    return str(result)


def delete_message_with_except(message) -> None:
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass


def edit_message_markup_with_except(message) -> None:
    try:
        bot.edit_message_reply_markup(message.chat.id, message.message_id)
    except:
        pass
