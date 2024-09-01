"""Slackのイベントハンドラモジュール"""

import json

from slack_bolt import App

from app.db_service import DBService

NOTIFICATION_JSON_NUMBER = 10


class SlackEventHandlers:
    def __init__(self, app: App):
        self.app = app

    def event_handlers(self):
        """Slackイベントハンドラ"""

        # アプリホーム
        @self.app.event("app_home_opened")
        def handle_app_home_opened(ack, body, client):
            ack()
            self.publish_app_home(user_id=body["event"]["user"], client=client, notification_message="-")

        # 出勤ボタン
        @self.app.action("begin_office_work")
        def handle_begin_office_work(ack, body, client):
            ack()
            self.publish_app_home(
                user_id=body["user"]["id"], client=client, notification_message="オフィス出勤を投稿しました"
            )

        @self.app.action("begin_remote_work")
        def handle_begin_remote_work(ack, body, client):
            ack()
            self.publish_app_home(
                user_id=body["user"]["id"], client=client, notification_message="リモート出勤を投稿しました"
            )

        # 退勤ボタン
        @self.app.action("finish_work")
        def handle_finish_work(ack, body, client):
            ack()
            self.publish_app_home(
                user_id=body["user"]["id"],
                client=client,
                notification_message="退勤を投稿しました。今日も一日お疲れ様でした！",
            )

        # 休憩ボタン
        @self.app.action("begin_break_time")
        def handle_begin_break_time(ack, body, client):
            ack()
            self.publish_app_home(
                user_id=body["user"]["id"],
                client=client,
                notification_message="休憩開始を投稿しました。ゆっくり休んでくださいね！",
            )

        @self.app.action("finish_break_time")
        def handle_finish_break_time(ack, body, client):
            ack()
            self.publish_app_home(
                user_id=body["user"]["id"],
                client=client,
                notification_message="休憩終了を投稿しました。後半戦も頑張りましょう！",
            )

        # 個人設定モーダル呼び出し
        @self.app.action("personal_settings")
        def handle_personal_settings(ack, body, client):
            ack()
            db_service = DBService()

            # ユーザの個人設定をのJSONを取得
            personal_settings_data = db_service.load_personal_settings(user_id=body["user"]["id"])
            personal_settings_view = self.create_personal_settings_view(personal_settings_data)

            # モーダルを表示
            client.views_open(trigger_id=body["trigger_id"], view=personal_settings_view)

        # 個人設定保存
        @self.app.view("submit_personal_settings")
        def handle_submit_personal_settings(ack, body, client):
            ack()
            user_id = body["user"]["id"]

            values = body["view"]["state"]["values"]

            # fmt: off
            attendance_channel_ids = values["attendance_channel_ids"]["attendance_channel_ids"]["selected_conversations"]
            attendance_thread_channel_id = values["attendance_thread_channel_id"]["attendance_thread_channel_id"]["selected_conversation"]
            attendance_thread_message =values["attendance_thread_message"]["attendance_thread_message"]["value"]
            change_profile_status = (
                values["change_profile_status"]["change_profile_status"]["selected_option"]["value"] == "True"
            )
            # fmt: on

            result, message = self.personal_settings_error_check(
                attendance_channel_ids, attendance_thread_channel_id, attendance_thread_message
            )
            if result:
                personal_settings_json_data = {
                    "attendance_channel_ids": attendance_channel_ids,
                    "attendance_thread_channel_id": attendance_thread_channel_id,
                    "attendance_thread_message": attendance_thread_message,
                    "change_profile_status": change_profile_status,
                }

                sb_service = DBService()
                sb_service.save_personal_settings(user_id, personal_settings_json_data)

            self.publish_app_home(user_id=user_id, client=client, notification_message=message)

    @staticmethod
    def publish_app_home(user_id, client, notification_message):
        with open("app/blocks/app_home.json", "r") as f:
            app_home_json = json.load(f)

        app_home_json["blocks"][NOTIFICATION_JSON_NUMBER]["text"]["text"] = (
            f"アプリからのお知らせ: *{notification_message}*"
        )
        client.views_publish(user_id=user_id, view=app_home_json)

    @staticmethod
    def personal_settings_error_check(
        attendance_channel_ids, attendance_thread_channel_id, attendance_thread_message
    ) -> tuple:
        if not attendance_channel_ids and not attendance_thread_channel_id:
            return False, ":warning:勤怠専用チャンネルか勤怠スレッドのどちらかは必須です"

        if attendance_thread_channel_id and not attendance_thread_message:
            return False, ":warning:勤怠スレッドチャンネルを設定する場合はスレッドの最初のメッセージを入力してください"
        return True, "個人設定を保存しました"

    @staticmethod
    def create_personal_settings_view(personal_settings_data):
        attendance_channel_ids = []
        attendance_thread_channel_id = None
        attendance_thread_message = ""
        change_profile_status = True
        change_profile_status_text = "はい"
        change_profile_status_value = "True"

        if personal_settings_data:
            attendance_channel_ids = personal_settings_data["attendance_channel_ids"]
            attendance_thread_channel_id = personal_settings_data["attendance_thread_channel_id"]
            attendance_thread_message = personal_settings_data["attendance_thread_message"]
            change_profile_status = personal_settings_data["change_profile_status"]

        if not change_profile_status:
            change_profile_status_text = "いいえ"
            change_profile_status_value = "False"

        views = {
            "type": "modal",
            "callback_id": "submit_personal_settings",
            "submit": {"type": "plain_text", "text": "OK", "emoji": True},
            "close": {"type": "plain_text", "text": "戻る", "emoji": True},
            "title": {"type": "plain_text", "text": "出退勤Botの個人設定", "emoji": True},
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ":warning: *勤怠専用チャンネル or 勤怠スレッドのどちらかは必須です*",
                    },
                },
                {"type": "divider"},
                {
                    "type": "input",
                    "block_id": "attendance_channel_ids",
                    "element": {
                        "type": "multi_conversations_select",
                        "action_id": "attendance_channel_ids",
                        "placeholder": {"type": "plain_text", "text": "チャンネルを選択", "emoji": True},
                        "filter": {"include": ["public", "private"], "exclude_bot_users": True},
                        "initial_conversations": attendance_channel_ids,
                    },
                    "label": {"type": "plain_text", "text": "勤怠専用チャンネル（複数選択可）", "emoji": True},
                    "optional": True,
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "image",
                            "image_url": "https://api.slack.com/img/blocks/bkb_template_images/placeholder.png",
                            "alt_text": "placeholder",
                        }
                    ],
                },
                {"type": "divider"},
                {
                    "type": "input",
                    "block_id": "attendance_thread_channel_id",
                    "element": {
                        "type": "conversations_select",
                        "action_id": "attendance_thread_channel_id",
                        "placeholder": {"type": "plain_text", "text": "チャンネルを選択", "emoji": True},
                        "filter": {"include": ["public", "private"], "exclude_bot_users": True},
                        "initial_conversation": attendance_thread_channel_id,
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "勤怠スレッドがあるチャンネルを選択（複数選択不可）",
                        "emoji": True,
                    },
                    "optional": True,
                },
                {
                    "type": "input",
                    "block_id": "attendance_thread_message",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "attendance_thread_message",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "例: 本日の勤怠連絡はこちらのスレッドにお願いします！",
                            "emoji": True,
                        },
                        "initial_value": attendance_thread_message,
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "スレッドの最初のメッセージを入力（前方一致）",
                        "emoji": True,
                    },
                    "optional": True,
                },
                {
                    "type": "input",
                    "block_id": "change_profile_status",
                    "element": {
                        "type": "static_select",
                        "placeholder": {"type": "plain_text", "text": "Select an item", "emoji": True},
                        "options": [
                            {
                                "text": {"type": "plain_text", "text": "はい", "emoji": True},
                                "value": "True",
                            },
                            {
                                "text": {"type": "plain_text", "text": "いいえ", "emoji": True},
                                "value": "False",
                            },
                        ],
                        "action_id": "change_profile_status",
                        "initial_option": {
                            "text": {"type": "plain_text", "text": change_profile_status_text, "emoji": True},
                            "value": change_profile_status_value,
                        },
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "出勤時にプロフィールの出社ステータス変更をする :office::house:",
                        "emoji": True,
                    },
                },
            ],
        }

        # attendance_thread_channel_idがNoneの場合、"initial_conversation": attendance_thread_channel_idの行を削除
        if not attendance_thread_channel_id:
            del views["blocks"][5]["element"]["initial_conversation"]

        return views
