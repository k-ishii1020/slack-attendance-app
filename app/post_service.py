import json

from slack_sdk import WebClient

from app.db_service import DBService
from app.db_service import Users


class PostService:
    def __init__(self):
        self.db_service = DBService()

    def post_message(self, user_id, action):
        # ユーザの個人設定をのJSONを取得
        db_service = DBService()
        user: Users = db_service.get_user(user_id=user_id)

        settings_json = json.loads(user.settings_json)

        attendance_channel_ids = settings_json["attendance_channel_ids"]
        attendance_thread_channel_id = settings_json["attendance_thread_channel_id"]
        attendance_thread_message = settings_json["attendance_thread_message"]
        change_profile_status = settings_json["change_profile_status"]

        # 投稿するメッセージ
        match action:
            case "begin_office_work":
                send_message = settings_json["begin_office_work_message"]
            case "begin_remote_work":
                send_message = settings_json["begin_remote_work_message"]
            case "finish_work":
                send_message = settings_json["finish_work_message"]
            case "begin_break_time":
                send_message = settings_json["begin_break_time_message"]
            case "finish_break_time":
                send_message = settings_json["finish_break_time_message"]

        # ユーザのユーザトークンを設定
        # 注意:Slack AppのBOTトークンを書き換えるのは禁止。都度WEBクライアントを生成し、ユーザトークンを設定すること。
        user_client = WebClient(token=user.access_token)

        for attendance_channel_id in attendance_channel_ids:
            user_client.chat_postMessage(channel=attendance_channel_id, text=send_message)

        return
