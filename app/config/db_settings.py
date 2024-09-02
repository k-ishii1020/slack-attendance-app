import logging
import os
import time

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

load_dotenv()

# MySQLの設定情報
USERNAME = os.getenv("DATABASE_USER")
PASSWORD = os.getenv("DATABASE_PASSWORD")
HOST = os.getenv("DATABASE_HOST")
DATABASE = os.getenv("DATABASE_NAME")
PORT = os.getenv("DATABASE_PORT")

DATABASE_URL = f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}?charset=utf8mb4"

engine = create_engine(
    DATABASE_URL, echo=False, query_cache_size=0, isolation_level="REPEATABLE READ", pool_pre_ping=True
)

# MySQLのセッションを作成する
Session = scoped_session(sessionmaker(bind=engine, expire_on_commit=False))


@staticmethod
def is_connect_mysql():
    """MySQLに接続できるか確認する"""
    time.sleep(10)  # docker-composeでMySQLが立ち上がるまで待つ
    try:
        db_session = Session()
        if db_session.execute(text("SELECT 1")).scalar() == 1:
            logging.info("MySQLへの接続に成功しました。")
        else:
            raise OperationalError("Unexpected result from MySQL")
    except OperationalError as e:
        logging.error(f"MySQLへの接続に失敗しました。: {e}")
        raise
    finally:
        db_session.close()
        Session.remove()
