from os import getenv
from telebot import TeleBot
from deepl import Translator
from dotenv import load_dotenv

load_dotenv()
GOOGLE_USE_PATH = getenv('GOOGLE_USE_PATH')
DB_URL = getenv("DB_URL")
TOKEN = getenv("BOT_TOKEN")
admins = eval(getenv("ADMINS"))
TRANSLATE_API_KEY = getenv("TRANSLATE_API_KEY")
CHAT_GPT_API_KEY = getenv("CHAT_GPT_API_KEY")
PAYMENT_KEY = getenv("PAYMENT_KEY")
bot = TeleBot(TOKEN)
translator = Translator(TRANSLATE_API_KEY)
personality_traits = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]
hobbies = ["Спорт", "Творчество", "Природа", "Кулинария", "Гейминг", "Путешествия", "Технологии", "Духовность",
           "Коллекционирование"]
