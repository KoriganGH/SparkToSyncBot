from os import getenv
from telebot import TeleBot
from dotenv import load_dotenv

load_dotenv()
TOKEN = getenv("BOT_TOKEN")
admins = eval(getenv("ADMINS"))
bot = TeleBot(TOKEN)
