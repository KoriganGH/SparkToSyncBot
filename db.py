from sqlalchemy import create_engine, Column, BigInteger, String, Integer, LargeBinary, Boolean, DateTime, ForeignKey, \
    Table, func
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.dialects.postgresql import ARRAY
from os import getenv
from sqlalchemy.exc import SQLAlchemyError

# Загрузка переменных окружения
from dotenv import load_dotenv

load_dotenv()

# Настройка базы данных
DB_URL = getenv("DB_URL")
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Таблица для связи реакций
reactions_table = Table('reactions', Base.metadata,
                        Column('user_id', BigInteger, ForeignKey('users3.id'), primary_key=True),
                        Column('target_user_id', BigInteger, ForeignKey('users3.id'), primary_key=True),
                        Column('reaction', String(10), nullable=False)  # 'like' или 'dislike'
                        )


# Модель профиля пользователя
class UserProfile(Base):
    __tablename__ = 'users3'
    id = Column(BigInteger, primary_key=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)
    city = Column(String(50), nullable=False)
    about = Column(String(500), nullable=False)
    telegram = Column(String(50), nullable=False)
    photo = Column(LargeBinary, nullable=False)
    hobbies = Column(MutableList.as_mutable(ARRAY(String)), nullable=False)
    premium = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True),
                        server_default=func.now())
    reactions = relationship(
        'UserProfile',
        secondary=reactions_table,
        primaryjoin=id == reactions_table.c.user_id,
        secondaryjoin=id == reactions_table.c.target_user_id,
        backref="reacted_by"
    )

    def __str__(self):
        return (
            f"<b>|Имя| </b>{self.name or 'не указано'}\n"
            f"<b>|Пол| </b>{self.gender or 'не указан'}\n"
            f"<b>|Возраст| </b>{self.age or 'не указан'}\n"
            f"<b>|Город| </b>{self.city or 'не указан'}\n"
            f"<b>|О себе| </b>{self.about or 'не указано'}\n"
            f"<b>|Хобби| </b>{', '.join(self.hobbies) if self.hobbies else 'не указаны'}"
        )


# Функции утилиты базы данных
def add_user(user) -> bool:
    try:
        new_user = UserProfile(
            id=user.id,
            name=user.name,
            age=user.age,
            city=user.city,
            about=user.about,
            telegram=user.telegram,
            photo=user.photo,
            gender=user.gender,
            hobbies=user.hobbies
        )
        with Session() as session:
            session.add(new_user)
            session.commit()
            return True

    except SQLAlchemyError as e:
        print(f"Error occurred: {e}")
        return False


def add_reaction(user_id, target_user_id, reaction_type) -> bool:
    try:
        new_reaction = reactions_table.insert().values(
            user_id=user_id,
            target_user_id=target_user_id,
            reaction=reaction_type
        )

        with Session() as session:
            session.execute(new_reaction)
            session.commit()
            return True

    except SQLAlchemyError as e:
        print(f"Error occurred: {e}")
        return False


def user_exists(user_id) -> bool:
    with Session() as session:
        return session.query(UserProfile).filter_by(id=user_id).first() is not None


def return_user_profile(user_id):
    with Session() as session:
        return session.query(UserProfile).filter_by(id=user_id).first()


# def edit_user_field(user: UserProfile, field_name: str, new_value: str) -> bool:
#     try:
#         with Session() as session:
#             user = session.merge(user)
#             setattr(user, field_name, new_value)
#             session.commit()
#             return True
#
#     except SQLAlchemyError as e:
#         print(f"Error occurred: {e}")
#         return False


def update_user(user: UserProfile) -> bool:
    try:
        with Session() as session:
            session.merge(user)
            session.commit()
            return True

    except SQLAlchemyError as e:
        print(f"Error occurred: {e}")
        return False


def get_users_who_liked_first(user_id):
    """ Возвращает пользователей, которые лайкнули заданного пользователя первыми. """
    with Session() as session:
        query = session.query(UserProfile).join(
            reactions_table, UserProfile.id == reactions_table.c.user_id
        ).filter(
            reactions_table.c.target_user_id == user_id,
            reactions_table.c.reaction == 'like'
        )
        return query.all()


def get_users_with_no_interactions(user_id):
    """ Возвращает пользователей, с которыми заданный пользователь еще не взаимодействовал. """
    with Session() as session:
        # Получаем ID пользователей, с которыми уже было взаимодействие
        interacted_users = session.query(reactions_table.c.target_user_id).filter(
            reactions_table.c.user_id == user_id).union(
            session.query(reactions_table.c.user_id).filter(reactions_table.c.target_user_id == user_id)
        ).subquery()

        # Запрос к пользователям, которые не в списках взаимодействий
        available_users = session.query(UserProfile).filter(
            UserProfile.id != user_id,
            ~UserProfile.id.in_(interacted_users)
        ).all()

        return available_users


# Создание таблиц
Base.metadata.create_all(engine)
