import logging
import os
import sys
import threading

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from app.config.db_settings import check_connect_mysql
from app.config.logging_config import setup_logging
from app.get_access_token import GetAccessToken
from app.slack_event_handler import SlackEventHandlers

if __name__ == "__main__":
    try:
        load_dotenv()
        setup_logging()
        check_connect_mysql()

        if os.getenv("ENCRYPTION_KEY") is None:
            logging.error("ENCRYPTION_KEY is not set.")
            sys.exit(1)

        app = App(token=os.getenv("SLACK_APP_BOT_TOKEN"))
        slack_event_handler = SlackEventHandlers(app)
        slack_event_handler.event_handlers()

        get_access_token_instance = GetAccessToken()
        get_access_token_thread = threading.Thread(target=get_access_token_instance.run)
        get_access_token_thread.start()

        SocketModeHandler(app, os.getenv("SLACK_APP_APP_TOKEN")).start()

    except KeyboardInterrupt:
        print("Program is terminated by user.")
        sys.exit(0)

    except Exception as e:
        error_message = f"An exception has occurred in your the application. reason:\n{e}"
        e
        logging.error(error_message, exc_info=True)
        sys.exit(1)
