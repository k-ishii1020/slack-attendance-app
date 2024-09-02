from slack_bolt import App

from app.db_service import DBService


class PostService:
    def __init__(self, app: App):
        self.app = app
        self.db_service = DBService()

    def post_message(self, user_id, action):
        # ユーザの個人設定をのJSONを取得
        db_service = DBService()
        personal_settings_data = db_service.load_personal_settings(user_id=user_id)

        begin_office_work_message = personal_settings_data["begin_office_work_message"]
        begin_remote_work_message = personal_settings_data["begin_remote_work_message"]
        finish_work_message = personal_settings_data["finish_work_message"]
        attendance_channel_ids = personal_settings_data["attendance_channel_ids"]
        attendance_thread_channel_id = personal_settings_data["attendance_thread_channel_id"]
        attendance_thread_message = personal_settings_data["attendance_thread_message"]
        change_profile_status = personal_settings_data["change_profile_status"]

        # ユーザとしてチャンネルに投稿する
        match action:
            case "begin_office_work":
                self.app.client.chat_postMessage(channel=attendance_channel_ids, text=begin_office_work_message)
                return
