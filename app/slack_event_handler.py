"""Slackのイベントハンドラモジュール"""

import json

from slack_bolt import App

NOTIFICATION_JSON_NUMBER = 10


class SlackEventHandlers:
    def __init__(self, app: App):
        self.app = app

    def event_handlers(self):
        """イベントハンドラを設定する"""

        @self.app.event("app_home_opened")
        def handle_app_home_opened(ack, body, client):
            ack()
            self.button_action(ack=ack, user_id=body["event"]["user"], client=client, notification_message="-")

        @self.app.action("begin_office_work")
        def handle_begin_office_work(ack, body, client):
            ack()
            self.button_action(
                ack=ack, user_id=body["user"]["id"], client=client, notification_message="オフィス出勤を投稿しました"
            )

        @self.app.action("begin_remote_work")
        def handle_begin_remote_work(ack, body, client):
            ack()
            self.button_action(
                ack=ack, user_id=body["user"]["id"], client=client, notification_message="リモート出勤を投稿しました"
            )

        @self.app.action("finish_work")
        def handle_finish_work(ack, body, client):
            ack()
            self.button_action(
                ack=ack,
                user_id=body["user"]["id"],
                client=client,
                notification_message="退勤を投稿しました。今日も一日お疲れ様でした！",
            )

        @self.app.action("begin_break_time")
        def handle_begin_break_time(ack, body, client):
            ack()
            self.button_action(
                ack=ack,
                user_id=body["user"]["id"],
                client=client,
                notification_message="休憩開始を投稿しました。ゆっくり休んでくださいね！",
            )

        @self.app.action("finish_break_time")
        def handle_finish_break_time(ack, body, client):
            ack()
            self.button_action(
                ack=ack,
                user_id=body["user"]["id"],
                client=client,
                notification_message="休憩終了を投稿しました。後半戦も頑張りましょう！",
            )

        @self.app.action("personal_settings")
        def handle_personal_settings(ack, body, client):
            ack()
            with open("app/blocks/personal_settings.json", "r") as f:
                personal_settings_json = json.load(f)
            client.views_open(trigger_id=body["trigger_id"], view=personal_settings_json)

        @self.app.view("submit_personal_settings")
        def handle_submit_personal_settings(ack, body, client):
            ack()
            self.button_action(
                ack=ack, user_id=body["user"]["id"], client=client, notification_message="個人設定を保存しました"
            )

    @staticmethod
    def button_action(ack, user_id, client, notification_message):
        with open("app/blocks/app_home.json", "r") as f:
            app_home_json = json.load(f)

        app_home_json["blocks"][NOTIFICATION_JSON_NUMBER]["text"]["text"] = (
            f"アプリからのお知らせ: *{notification_message}*"
        )
        client.views_publish(user_id=user_id, view=app_home_json)
