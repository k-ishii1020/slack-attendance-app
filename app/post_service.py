import os

from slack_sdk import WebClient

from app.config.config_loader import config
from app.db_service import DBService
from app.db_service import Users


class PostService:
    def __init__(self):
        self.db_service = DBService()

    def post_message(self, user_id, action, postscript) -> tuple[int, str]:
        # ユーザの個人設定をのJSONを取得
        db_service = DBService()
        user: Users = db_service.get_user(user_id=user_id)

        if user is None:
            return (
                1,
                f":warning: Slack認証が完了していません。<{os.getenv("SLACK_APP_OAUTH_URL")}|こちら>から認証を行ってください",
            )
        if user.settings_json is None:
            return 1, ":warning:ユーザの個人設定が実施されていません。個人設定を実施してください。"

        # 投稿するメッセージ
        match action:
            case "begin_office_work":
                send_message = user.settings_json["begin_office_work_message"]
                status_emoji = config["attendance_emoji"]["office_work"]
            case "begin_remote_work":
                send_message = user.settings_json["begin_remote_work_message"]
                status_emoji = config["attendance_emoji"]["remote_work"]
            case "finish_work":
                send_message = user.settings_json["finish_work_message"]
                status_emoji = config["attendance_emoji"]["finish_work"]
            case "begin_break_time":
                send_message = user.settings_json["begin_break_time_message"]
            case "finish_break_time":
                send_message = user.settings_json["finish_break_time_message"]

        if postscript:
            send_message += f"\n{postscript}"

        attendance_channel_ids = user.settings_json["attendance_channel_ids"]
        attendance_thread_channel_id = user.settings_json["attendance_thread_channel_id"]
        attendance_thread_message = user.settings_json["attendance_thread_message"]
        change_profile_status = user.settings_json["change_profile_status"]

        # ユーザのユーザトークンを設定
        # 注意:mainで生成したSlack AppのSLACK_APP_BOT_TOKENを書き換えるのは禁止。都度WebClientを生成し、ユーザトークンを設定すること。
        user_client = WebClient(token=user.access_token)

        # 直接投稿タイプ
        if attendance_channel_ids:
            for attendance_channel_id in attendance_channel_ids:
                user_client.chat_postMessage(channel=attendance_channel_id, text=send_message)

        # スレッド投稿タイプ
        """ なぜsearch_messagesを使わないのか？
        search_messagesは、ユーザトークンを使用するAPIで、そのユーザが参加しているプライベートチャンネルやDMのメッセージを検索することができる。
        万が一、管理者がユーザトークンを悪用してしまうと、そのユーザが参加しているプライベートチャンネルやDMのメッセージを取得することができてしまう。
        そのため、conversations_historyを使用し、さらにユーザスコープはchannels:historyのみ限定している。
        """
        if attendance_thread_channel_id:
            SEARCH_LIMIT = 10  # 会話を検索する回数 (1回につき100件取得) 1日に1000件を超える会話がある場合、1001件目以降の会話は取得できない。
            attendance_thread_message_ts = None
            cursor_param = None

            for _ in range(SEARCH_LIMIT):
                # attendance_thread_channel_idのチャンネル内の24時間以内の会話を取得。
                # 24時間以内のメッセージを取得するため、oldestに24時間前のUNIX時間を指定する。
                conversations_list = user_client.conversations_history(
                    channel=attendance_thread_channel_id,
                    limit=100,
                    cursor=cursor_param,
                )
                for message in conversations_list["messages"]:
                    # conversations_listの中からattendance_thread_messageを含むメッセージTSを探す（前方一致）
                    if message["text"].startswith(attendance_thread_message):
                        attendance_thread_message_ts = message["ts"]
                        break
                if attendance_thread_message_ts:
                    break
                else:
                    # 次のページがない場合、ループを抜ける
                    if "response_metadata" not in conversations_list or not conversations_list[
                        "response_metadata"
                    ].get("next_cursor"):
                        break
                    cursor_param = conversations_list["response_metadata"]["next_cursor"]
                    continue

            if attendance_thread_message_ts is None:
                return 1, ":warning:勤怠スレッドが見つかりませんでした。キーワードを確認してください。"

            user_client.chat_postMessage(
                channel=attendance_thread_channel_id, text=send_message, thread_ts=attendance_thread_message_ts
            )

        if action not in ["begin_office_work", "begin_remote_work", "finish_work"]:
            return 0, ""

        # ユーザのステータスを変更
        if change_profile_status:
            # ユーザのステータスを取得
            user_profile = user_client.users_profile_get(user=user_id)
            status_text = user_profile["profile"]["status_text"]
            user_client.users_profile_set(profile={"status_text": status_text, "status_emoji": status_emoji})

        return 0, ""
