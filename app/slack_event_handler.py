"""Slackのイベントハンドラモジュール"""

import json
import os

from slack_bolt import App

from app.db_service import DBService
from app.db_service import Users
from app.post_service import PostService

WELCOME_MESSAGE_JSON_NUMBER = 0
NOTIFICATION_JSON_NUMBER = 9


class SlackEventHandlers:
    def __init__(self, app: App):
        self.app = app
        self.post_service = PostService()

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
            self.post_message(
                body,
                client=client,
                action="begin_office_work",
                notification_message=":office:オフィス出勤を投稿しました",
            )

        # リモート出勤ボタン
        @self.app.action("begin_remote_work")
        def handle_begin_remote_work(ack, body, client):
            ack()
            self.post_message(
                body,
                client=client,
                action="begin_remote_work",
                notification_message=":house:リモート出勤を投稿しました",
            )

        # 退勤ボタン
        @self.app.action("finish_work")
        def handle_finish_work(ack, body, client):
            ack()
            self.post_message(
                body,
                client=client,
                action="finish_work",
                notification_message="退勤を投稿しました。今日も一日お疲れ様でした！",
            )

        # 休憩開始ボタン
        @self.app.action("begin_break_time")
        def handle_begin_break_time(ack, body, client):
            ack()
            self.post_message(
                body,
                client=client,
                action="begin_break_time",
                notification_message="休憩開始を投稿しました。ゆっくり休んでくださいね！",
            )

        # 休憩終了ボタン
        @self.app.action("finish_break_time")
        def handle_finish_break_time(ack, body, client):
            ack()
            self.post_message(
                body,
                client=client,
                action="finish_break_time",
                notification_message="休憩終了を投稿しました。後半戦もファイトです！",
            )

        # 個人設定モーダル呼び出し
        @self.app.action("personal_settings")
        def handle_personal_settings(ack, body, client):
            ack()
            db_service = DBService()

            # ユーザの個人設定をのJSONを取得
            user: Users = db_service.get_user(user_id=body["user"]["id"])
            personal_settings_view = self.create_personal_settings_view(user.settings_json)

            # モーダルを表示
            client.views_open(trigger_id=body["trigger_id"], view=personal_settings_view)

        # 個人設定保存
        @self.app.view("submit_personal_settings")
        def handle_submit_personal_settings(ack, body, client):
            ack()
            user_id = body["user"]["id"]

            values = body["view"]["state"]["values"]

            # fmt: off
            begin_office_work_message = values["begin_office_work_message"]["begin_office_work_message"]["value"]
            begin_remote_work_message = values["begin_remote_work_message"]["begin_remote_work_message"]["value"]
            finish_work_message = values["finish_work_message"]["finish_work_message"]["value"]
            begin_break_time_message = values["begin_break_time_message"]["begin_break_time_message"]["value"]
            finish_break_time_message = values["finish_break_time_message"]["finish_break_time_message"]["value"]
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
                    "begin_office_work_message": begin_office_work_message,
                    "begin_remote_work_message": begin_remote_work_message,
                    "finish_work_message": finish_work_message,
                    "begin_break_time_message": begin_break_time_message,
                    "finish_break_time_message": finish_break_time_message,
                    "attendance_channel_ids": attendance_channel_ids,
                    "attendance_thread_channel_id": attendance_thread_channel_id,
                    "attendance_thread_message": attendance_thread_message,
                    "change_profile_status": change_profile_status,
                }

                sb_service = DBService()
                sb_service.save_personal_settings(user_id, personal_settings_json_data)

            self.publish_app_home(user_id=user_id, client=client, notification_message=message)

    def post_message(self, body, client, action, notification_message):
        result = self.post_service.post_message(
            user_id=body["user"]["id"],
            action=action,
            postscript=body["view"]["state"]["values"]["postscript"]["postscript"]["value"],
        )
        if result[0] == 1:
            notification_message = result[1]
        self.publish_app_home(user_id=body["user"]["id"], client=client, notification_message=notification_message)

    @staticmethod
    def publish_app_home(user_id, client, notification_message):
        with open("app/blocks/app_home.json", "r") as f:
            app_home_json = json.load(f)

        app_home_json["blocks"][WELCOME_MESSAGE_JSON_NUMBER]["text"]["text"] = os.getenv("WELCOME_MESSAGE")

        app_home_json["blocks"][NOTIFICATION_JSON_NUMBER]["text"]["text"] = (
            f"*アプリからのお知らせ*:\n {notification_message}"
        )
        client.views_publish(user_id=user_id, view=app_home_json)

    @staticmethod
    def personal_settings_error_check(
        attendance_channel_ids, attendance_thread_channel_id, attendance_thread_message
    ) -> tuple:
        if not attendance_channel_ids and not attendance_thread_channel_id:
            return False, ":warning: チャンネルに直接投稿タイプかスレッド内投稿タイプのどちらかは必須です"

        if attendance_thread_channel_id and not attendance_thread_message:
            return False, ":warning:スレッド内投稿タイプを設定する場合はスレッドの最初のメッセージを入力してください"
        return True, "個人設定を保存しました"

    @staticmethod
    def create_personal_settings_view(settings_json: dict) -> dict:
        # デフォルト値
        begin_office_work_message = os.getenv("BEGIN_OFFICE_WORK_MESSAGE")
        begin_remote_work_message = os.getenv("BEGIN_REMOTE_WORK_MESSAGE")
        finish_work_message = os.getenv("FINISH_WORK_MESSAGE")
        begin_break_time_message = os.getenv("BEGIN_BREAK_TIME_MESSAGE")
        finish_break_time_message = os.getenv("FINISH_BREAK_TIME_MESSAGE")

        attendance_channel_ids = []
        attendance_thread_channel_id = None
        attendance_thread_message = ""
        change_profile_status = True
        change_profile_status_text = "はい"
        change_profile_status_value = "True"

        if settings_json:
            begin_office_work_message = settings_json["begin_office_work_message"]
            begin_remote_work_message = settings_json["begin_remote_work_message"]
            finish_work_message = settings_json["finish_work_message"]
            begin_break_time_message = settings_json["begin_break_time_message"]
            finish_break_time_message = settings_json["finish_break_time_message"]
            attendance_channel_ids = settings_json["attendance_channel_ids"]
            attendance_thread_channel_id = settings_json["attendance_thread_channel_id"]
            attendance_thread_message = settings_json["attendance_thread_message"]
            change_profile_status = settings_json["change_profile_status"]

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
                    "type": "header",
                    "text": {"type": "plain_text", "text": ":memo: 投稿メッセージ設定", "emoji": True},
                },
                {
                    "type": "input",
                    "block_id": "begin_office_work_message",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "begin_office_work_message",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "例: 業務開始します（出社）",
                            "emoji": True,
                        },
                        "initial_value": begin_office_work_message,
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "オフィス勤務時に投稿するメッセージを入力",
                        "emoji": True,
                    },
                    "optional": True,
                },
                {
                    "type": "input",
                    "block_id": "begin_remote_work_message",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "begin_remote_work_message",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "例: 業務開始します（リモート）",
                            "emoji": True,
                        },
                        "initial_value": begin_remote_work_message,
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "リモート勤務時に投稿するメッセージを入力",
                        "emoji": True,
                    },
                    "optional": True,
                },
                {
                    "type": "input",
                    "block_id": "finish_work_message",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "finish_work_message",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "例: 業務終了します。お疲れ様でした。",
                            "emoji": True,
                        },
                        "initial_value": finish_work_message,
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "退勤時に投稿するメッセージを入力",
                        "emoji": True,
                    },
                    "optional": True,
                },
                {
                    "type": "input",
                    "block_id": "begin_break_time_message",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "begin_break_time_message",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "例: 休憩開始します。",
                            "emoji": True,
                        },
                        "initial_value": begin_break_time_message,
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "休憩開始時に投稿するメッセージを入力",
                        "emoji": True,
                    },
                    "optional": True,
                },
                {
                    "type": "input",
                    "block_id": "finish_break_time_message",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "finish_break_time_message",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "例: 休憩終了します。",
                            "emoji": True,
                        },
                        "initial_value": finish_break_time_message,
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "休憩終了時に投稿するメッセージを入力",
                        "emoji": True,
                    },
                    "optional": True,
                },
                {"type": "divider"},
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": ":mega: 投稿チャンネル設定", "emoji": True},
                },
                {
                    "type": "input",
                    "block_id": "attendance_channel_ids",
                    "element": {
                        "type": "multi_conversations_select",
                        "action_id": "attendance_channel_ids",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "対象チャンネルを選択（複数選択可）",
                            "emoji": True,
                        },
                        "filter": {"include": ["public", "private"], "exclude_bot_users": True},
                        "initial_conversations": attendance_channel_ids,
                    },
                    "label": {"type": "plain_text", "text": "チャンネルに直接投稿タイプ", "emoji": True},
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
                        "placeholder": {
                            "type": "plain_text",
                            "text": "対象チャンネルを選択（複数選択不可）",
                            "emoji": True,
                        },
                        "filter": {"include": ["public", "private"], "exclude_bot_users": True},
                        "initial_conversation": attendance_thread_channel_id,
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "スレッド内投稿タイプ",
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
                        "text": "対象スレッドのメッセージを入力（前方一致）",
                        "emoji": True,
                    },
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
                    "type": "header",
                    "text": {"type": "plain_text", "text": ":house: プロフィールステータス設定", "emoji": True},
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

        # 初期登録前の場合は不要な要素を削除
        if not attendance_thread_channel_id:
            del views["blocks"][11]["element"]["initial_conversation"]

        if not attendance_thread_message:
            del views["blocks"][12]["element"]["initial_value"]

        return views
