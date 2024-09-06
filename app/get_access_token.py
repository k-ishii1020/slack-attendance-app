import os

from flask import Flask
from flask import redirect
from flask import request
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt.oauth.oauth_settings import OAuthSettings

from app.db_service import DBService


class GetAccessToken:
    def __init__(self):
        self.flask_app = Flask(__name__)
        self.db_service = DBService()

        self.oauth_settings = OAuthSettings(
            client_id=os.getenv("SLACK_APP_CLIENT_ID"),
            client_secret=os.getenv("SLACK_APP_CLIENT_SECRET"),
            user_scopes=[
                "chat:write",
                "users.profile:read",
                "users.profile:write",
                "search:read",
                "channels:read",
            ],
        )

        self.app = App(
            signing_secret=os.getenv("SLACK_APP_SIGNING_SECRET"),
            oauth_settings=self.oauth_settings,
        )
        self.handler = SlackRequestHandler(self.app)
        self.set_routes()

    def set_routes(self):
        @self.flask_app.route("/slack/install", methods=["GET"])
        def install():
            return self.handler.handle(request)

        @self.flask_app.route("/slack/oauth/callback", methods=["GET"])
        def oauth_callback():
            code = request.args.get("code")
            try:
                oauth_response = self.app.client.oauth_v2_access(
                    client_id=self.oauth_settings.client_id, client_secret=self.oauth_settings.client_secret, code=code
                )
                user_id = oauth_response["authed_user"]["id"]
                user_token = oauth_response["authed_user"]["access_token"]

                self.db_service.save_access_token(user_id, user_token)

            except Exception as e:
                print(f"Error during OAuth: {e}")
                return redirect("/error")
            return redirect("/success")

        @self.flask_app.route("/success", methods=["GET"])
        def success():
            return "Success in Slack authentication"

        @self.flask_app.route("/error", methods=["GET"])
        def error():
            return "Error in Slack authentication. Please contact the administrator."

    def run(self):
        self.flask_app.run(host="0.0.0.0", port=os.getenv("SLACK_APP_OAUTH_PORT"), debug=False)
