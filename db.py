from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, BigInteger, ARRAY
from sqlalchemy.orm import sessionmaker, declarative_base
from os import getenv

load_dotenv()
DB_URL = getenv("DB_URL")
engine = create_engine(DB_URL)

Base = declarative_base()


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
    hobbies = Column(ARRAY(String), nullable=False)

    def __str__(self):
        return (f"Имя: {'не указано' if self.name is None else self.name}\n"
                f"Пол: {'не указан' if self.gender is None else self.gender}\n"
                f"Возраст: {'не указан' if self.age is None else self.age}\n"
                f"Город: {'не указан' if self.city is None else self.city}\n"
                f"Телеграм: {'не указан' if self.telegram is None else self.telegram}\n"
                f"О себе: {'не указано' if self.about is None else self.about}\n"
                f"Хобби: {'не указаны' if self.hobbies is None else self.hobbies}\n")


def user_exists(user_id):
    return session.query(UserProfile).filter(UserProfile.id == user_id).first() is not None


def return_user_profile(user_id):
    return session.query(UserProfile).filter(UserProfile.id == user_id).first()


Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()
