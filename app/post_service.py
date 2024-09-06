import os

from slack_sdk import WebClient

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
            return 1, ":warning:Slackアプリの認証が実施されていません。認証を実施してください。"
        if user.settings_json is None:
            return 1, ":warning:ユーザの個人設定が実施されていません。個人設定を実施してください。"

        # 投稿するメッセージ
        match action:
            case "begin_office_work":
                send_message = user.settings_json["begin_office_work_message"]
                status_emoji = os.getenv("OFFICE_WORK_EMOJI")
            case "begin_remote_work":
                send_message = user.settings_json["begin_remote_work_message"]
                status_emoji = os.getenv("REMOTE_WORK_EMOJI")
            case "finish_work":
                send_message = user.settings_json["finish_work_message"]
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
        if attendance_thread_channel_id:
            # attendance_thread_channel_idからchannnel_nameを取得
            channel_info = user_client.conversations_info(channel=attendance_thread_channel_id)
            channel_name = channel_info["channel"]["name"]

            # attendance_thread_channel_idのチャンネル内を検索し、直近でattendance_thread_messageが含まれるスレッドを取得
            search_query = f"in:{channel_name} {attendance_thread_message}"

            result = user_client.search_messages(
                channel=attendance_thread_channel_id,
                query=search_query,
                count=1,
                sort="timestamp",
                sort_dir="desc",
                page=1,
            )
            if result["messages"]["total"] == 0:
                return 1, ":warning:勤怠スレッドが見つかりませんでした。キーワードを確認してください。"
            result_ts = result["messages"]["matches"][0]["ts"]
            user_client.chat_postMessage(channel=attendance_thread_channel_id, text=send_message, thread_ts=result_ts)

        if action not in ["begin_office_work", "begin_remote_work"]:
            return 0, ""

        # ユーザのステータスを変更
        if change_profile_status:
            # ユーザのステータスを取得
            user_profile = user_client.users_profile_get(user=user_id)
            status_text = user_profile["profile"]["status_text"]
            user_client.users_profile_set(profile={"status_text": status_text, "status_emoji": status_emoji})

        return 0, ""
