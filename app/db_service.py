"""タスクの操作に関するサービスクラス"""

import logging
from functools import wraps

from sqlalchemy import TIMESTAMP
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import text
from sqlalchemy.ext.declarative import declarative_base

from app.config.db_settings import Session

Base = declarative_base()


def session_scope(func):
    """セッション管理のデコレーター"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        db_session = Session()
        try:
            result = func(db_session, *args, **kwargs)
            db_session.commit()
            return result
        except Exception as e:
            db_session.rollback()
            logging.error(f"Error during {func.__name__} with args {args}, kwargs {kwargs}: {str(e)}")
            raise
        finally:
            db_session.close()
            Session.remove()

    return wrapper


class DBService:
    @staticmethod
    @session_scope
    def get_user(db_session, user_id):
        return db_session.query(Users).filter(Users.user_id == user_id).first()

    @staticmethod
    @session_scope
    def save_access_token(db_session, user_id, access_token):
        user = Users(user_id=user_id, access_token=access_token)
        db_session.add(user)
        return user

    @staticmethod
    @session_scope
    def save_personal_settings(db_session, user_id, settings):
        user = Users(user_id=user_id, settings_json=settings)
        # 既にユーザが存在する場合は更新
        db_session.query(Users).filter(Users.user_id == user_id).update({"settings_json": settings})
        return user


class Users(Base):
    __tablename__ = "users"

    user_id = Column(String(250), primary_key=True)
    access_token = Column(String(250), nullable=False)
    settings_json = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
