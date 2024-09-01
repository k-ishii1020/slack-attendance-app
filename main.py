import logging
import os
import sys

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from app.config.logging_config import setup_logging
from app.db_service import DBService
from app.slack_event_handler import SlackEventHandlers

if __name__ == "__main__":
    try:
        load_dotenv()
        setup_logging()
        db_service = DBService()
        db_service.init_db()

        app = App(token=os.getenv("SLACK_BOT_TOKEN"))
        slack_event_handler = SlackEventHandlers(app)
        slack_event_handler.event_handlers()
        SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN")).start()

    except KeyboardInterrupt:
        print("プログラムがユーザによって中断されました。")
        sys.exit(0)

    except Exception as e:
        error_message = f"アプリケーションで例外が発生しました:\n{e}"
        logging.error(error_message, exc_info=True)
        sys.exit(1)
