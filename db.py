from datetime import datetime
from typing import List, Type
from sqlalchemy import create_engine, Column, BigInteger, String, Integer, LargeBinary, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Query
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.exc import SQLAlchemyError
from config import DB_URL

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()


class Reaction(Base):
    __tablename__ = "reactions"
    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    target_user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    reaction = Column(String(10), nullable=False)  # "like" или "dislike"
    created_at = Column(DateTime, default=datetime.now)


def add_reaction(user_id, target_user_id, reaction_type) -> bool:
    try:
        new_reaction = Reaction(
            user_id=user_id,
            target_user_id=target_user_id,
            reaction=reaction_type
        )

        with Session() as session:
            session.add(new_reaction)
            session.commit()
            return True

    except SQLAlchemyError as e:
        print(f"Error occurred: {e}")
        return False


class Match(Base):
    __tablename__ = "matches"
    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    matched_user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    created_at = Column(DateTime, default=datetime.now)


def add_match(user_id, matched_user_id):
    new_match = Match(
        user_id=user_id,
        matched_user_id=matched_user_id
    )
    with Session() as session:
        session.add(new_match)
        session.commit()


def check_match(user_id, target_user_id) -> bool:
    with Session() as session:
        match = session.query(Reaction).filter_by(
            user_id=target_user_id,
            target_user_id=user_id,
            reaction="like"
        ).first()

        return match is not None


class UserProfile(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)
    city = Column(String(50), nullable=False)
    about = Column(String(500), nullable=False)
    telegram = Column(String(50), nullable=True)
    photo = Column(LargeBinary, nullable=False)
    hobbies = Column(MutableList.as_mutable(ARRAY(String)), nullable=False)
    personality = Column(String(50), nullable=True)
    premium = Column(Boolean, default=False, nullable=False)
    verified = Column(Boolean, default=None, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    reactions = relationship(
        "UserProfile",
        secondary="reactions",
        primaryjoin=id == Reaction.user_id,
        secondaryjoin=id == Reaction.target_user_id,
        backref="reacted_by"
    )
    matches = relationship(
        "UserProfile",
        secondary="matches",
        primaryjoin=id == Match.user_id,
        secondaryjoin=id == Match.matched_user_id,
        backref="matched_with"
    )

    def __str__(self):
        return (
            f"<b>Имя | </b>{self.name or 'не указано'}\n"
            f"<b>Пол | </b>{self.gender or 'не указан'}\n"
            f"<b>Возраст | </b>{self.age or 'не указан'}\n"
            f"<b>Город | </b>{self.city or 'не указан'}\n"
            f"<b>Хобби | </b>{', '.join(self.hobbies) if self.hobbies else 'не указаны'}\n"
            f"<b>О себе | </b>{self.about or 'не указано'}\n"
            f"\n{'✅<b> Профиль верифицирован </b>✅' if self.verified else ''}"
        )

    def __repr__(self):
        return (
            f"Возраст: {self.age or 'не указан'}\n"
            f"Город: {self.city or 'не указан'}\n"
            f"{'Тип личности: ' + self.personality if self.personality else ''}\n"
            f"Хобби: {', '.join(self.hobbies) if self.hobbies else 'не указаны'}\n"
            f"О себе: {self.about or 'не указано'}\n"
        )


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
            hobbies=user.hobbies,
            personality=user.personality
        )
        with Session() as session:
            session.add(new_user)
            session.commit()
            return True

    except SQLAlchemyError as e:
        print(f"Error occurred: {e}")
        return False


def user_exists(user_id) -> bool:
    with Session() as session:
        return session.query(UserProfile).filter_by(id=user_id).first() is not None


def get_user_profile(user_id):
    with Session() as session:
        return session.query(UserProfile).filter_by(id=user_id).first()


def get_all_users():
    with Session() as session:
        return session.query(UserProfile)


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


def get_user_first_match(user: UserProfile) -> Type[UserProfile] | None:
    with Session() as session:
        user = session.merge(user)
        matches = user.matches
        if matches:
            return matches[0]
        return None


def delete_user_first_match(user: UserProfile) -> bool:
    with Session() as session:
        user = session.merge(user)
        del user.matches[0]
        session.commit()
        return True


def get_query_of_users_who_liked_first(user_id) -> Query:
    """ Возвращает запрос, содержащий пользователей, которые первыми положительно оценили заданного пользователя """
    with Session() as session:
        users_evaluated_by_user = session.query(Reaction.target_user_id).filter(
            Reaction.user_id == user_id
        ).subquery()

        query_users = session.query(UserProfile).join(
            Reaction, UserProfile.id == Reaction.user_id
        ).filter(
            Reaction.target_user_id == user_id,
            Reaction.reaction == "like",
            ~UserProfile.id.in_(users_evaluated_by_user)
        )
        return query_users


def get_query_of_users_with_no_interactions(user_id) -> Query:
    """ Возвращает запрос содержащий пользователей, с которыми заданный пользователь еще не взаимодействовал """
    with Session() as session:
        interacted_users = session.query(Reaction.target_user_id).filter(
            Reaction.user_id == user_id).union(
            session.query(Reaction.user_id).filter(Reaction.target_user_id == user_id)
        ).subquery()

        query_users = session.query(UserProfile).filter(
            UserProfile.id != user_id,
            ~UserProfile.id.in_(interacted_users)
        )

        return query_users


def get_filtered_users(users: Query, filters: dict) -> List[UserProfile]:
    if filters.get("city"):
        users = users.filter(UserProfile.city.ilike(f"%{filters['city']}%"))

    if filters.get("age"):
        age_range = filters["age"].split("-")
        users = users.filter(UserProfile.age >= age_range[0], UserProfile.age <= age_range[1])

    if filters.get("gender"):
        users = users.filter_by(gender=filters["gender"])

    return users.all()


class VerificationRequest(Base):
    __tablename__ = "verification_requests"
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # Статус: "pending", "approved", "rejected"
    request_date = Column(DateTime, default=datetime.now)
    review_date = Column(DateTime)
    reviewed_by = Column(String(100))

    user = relationship("UserProfile", backref="verification_requests")


def add_verification_request(user_id):
    with Session() as session:
        verification_request = VerificationRequest(user_id=user_id)
        session.add(verification_request)
        session.commit()


def update_verification_request(request_id, status, reviewed_by):
    with Session() as session:
        request = session.query(VerificationRequest).filter_by(id=request_id).first()
        if request:
            request.status = status
            request.review_date = datetime.now()
            request.reviewed_by = reviewed_by
            if status == "approved":
                user = session.query(UserProfile).filter_by(id=request.user_id).first()
                user.verified = True
            session.commit()


def get_pending_verification_requests():
    with Session() as session:
        requests = session.query(VerificationRequest).filter_by(status='pending').all()
    return requests


# class Tests(Base):
#     __tablename__ = "tests"
#     user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
#     test_result = Column(String(100), nullable=False)
#     created_at = Column(DateTime, default=datetime.now)


Base.metadata.create_all(engine)
