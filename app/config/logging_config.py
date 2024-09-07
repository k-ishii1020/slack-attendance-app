import logging
import os
from logging.handlers import TimedRotatingFileHandler

from slack_log_handler import SlackLogHandler

# ログフォーマットを設定
LOG_FORMAT = "%(asctime)s %(levelname)s : %(message)s"

EMOJIS = {
    logging.NOTSET: ":loudspeaker:",
    logging.DEBUG: ":speaker:",
    logging.INFO: ":memo:",
    logging.WARNING: ":warning:",
    logging.ERROR: ":rotating_light:",
    logging.CRITICAL: ":warning:",
}


def setup_logging():
    """ロギング設定を行う"""
    # ファイルハンドラーを作成
    file_handler = TimedRotatingFileHandler("./logs/error.log", when="D", backupCount=30)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    # コンソールハンドラーを作成
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    console_handler.setLevel(logging.INFO)

    # Slack エラーハンドラーを作成
    slack_error_handler = SlackLogHandler(
        os.getenv("LOG_ERROR_WEBHOOK"),
        username=os.getenv("NICKNAME"),
        emojis=EMOJIS,
    )
    slack_error_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    slack_error_handler.setLevel(logging.ERROR)

    # Loggerの基本設定
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[file_handler, console_handler, slack_error_handler],
    )
    return logging.getLogger(__name__)
