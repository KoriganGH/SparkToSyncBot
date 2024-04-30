from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, BigInteger
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.dialects.postgresql import ARRAY
from os import getenv

# Загрузка переменных окружения
from dotenv import load_dotenv

load_dotenv()

# Настройка базы данных
DB_URL = getenv("DB_URL")
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()


# Модель профиля пользователя
class UserProfile(Base):
    __tablename__ = 'users'
    id = Column(BigInteger, primary_key=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)
    city = Column(String, nullable=False)
    about = Column(String, nullable=False)
    telegram = Column(String, nullable=False)
    photo = Column(LargeBinary, nullable=False)
    hobbies = Column(MutableList.as_mutable(ARRAY(String)), nullable=False)

    def __str__(self):
        return (
            f"Имя: {self.name or 'не указано'}\n"
            f"Пол: {self.gender or 'не указан'}\n"
            f"Возраст: {self.age or 'не указан'}\n"
            f"Город: {self.city or 'не указан'}\n"
            f"Телеграм: {self.telegram or 'не указан'}\n"
            f"О себе: {self.about or 'не указано'}\n"
            f"Хобби: {', '.join(self.hobbies) if self.hobbies else 'не указаны'}"
        )


# Функции утилиты базы данных
def user_exists(user_id):
    return session.query(UserProfile).filter_by(id=user_id).first() is not None


def return_user_profile(user_id):
    return session.query(UserProfile).filter_by(id=user_id).first()


# Создание таблиц
Base.metadata.create_all(engine)
