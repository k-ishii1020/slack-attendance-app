import json
import logging
import os
from functools import wraps

from sqlalchemy import TIMESTAMP
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import text
from sqlalchemy.ext.declarative import declarative_base

from app.config.db_settings import Session
from app.crypto_utils import decrypt_token
from app.crypto_utils import encrypt_token
from app.crypto_utils import generate_salt

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
        raw_user = db_session.query(Users).filter(Users.user_id == user_id).first()

        if raw_user is None:
            return None

        # DBセッションのレコードをかきかえることを防ぐため、コピーを作成
        work_user_record = Users()
        work_user_record.user_id = raw_user.user_id
        work_user_record.access_token = raw_user.access_token
        work_user_record.salt = raw_user.salt
        work_user_record.settings_json = json.loads(raw_user.settings_json) if raw_user.settings_json else None

        if work_user_record.access_token:
            # ユーザのアクセストークンを復号化
            password = os.getenv("ENCRYPTION_KEY")
            work_user_record.access_token = decrypt_token(
                work_user_record.access_token, password, work_user_record.salt
            )
        return work_user_record

    @staticmethod
    @session_scope
    def save_access_token(db_session, user_id, access_token):
        salt = generate_salt()
        password = os.getenv("ENCRYPTION_KEY")
        encrypted_token = encrypt_token(access_token, password, salt)

        user = db_session.query(Users).filter(Users.user_id == user_id).first()
        if user:
            user.access_token = encrypted_token
            user.salt = salt
        else:
            user = Users(user_id=user_id, access_token=encrypted_token, salt=salt)
        # 変更をマーク
        db_session.add(user)
        return user

    @staticmethod
    @session_scope
    def save_personal_settings(db_session, user_id, settings):
        user = db_session.query(Users).filter(Users.user_id == user_id).first()
        if user:
            user.settings_json = json.dumps(settings, ensure_ascii=False)
        else:
            user = Users(user_id=user_id, settings_json=json.dumps(settings, ensure_ascii=False))
            db_session.add(user)
        # 変更をマーク
        db_session.add(user)
        return user


class Users(Base):
    __tablename__ = "users"

    user_id = Column(String(250), primary_key=True)
    access_token = Column(String(250), nullable=False)
    salt = Column(String(250), nullable=False)
    settings_json = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
