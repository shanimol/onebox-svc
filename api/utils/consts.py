from dotenv import load_dotenv
from os import environ

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/meetings.space.readonly",
    "https://www.googleapis.com/auth/meetings.space.created",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/calendar.events.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
    "openid",
]

CREDENTIAL_FILE_PATH = "credentials.json"

REDIRECT_URI = environ["REDIRECT_URI"]

SLACK_CLIENT_ID = environ["SLACK_CLIENT_ID"]
SLACK_CLIENT_SECRET = environ["SLACK_CLIENT_SECRET"]
SLACK_REDIRECT_URI = environ["SLACK_REDIRECT_URI"]
SLACK_BOT_TOKEN = environ["SLACK_BOT_TOKEN"]
