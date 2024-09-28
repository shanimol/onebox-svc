import os.path
import base64
from fastapi.responses import JSONResponse
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from services.user import user
from services.messages import messages
from utils import date_conv
import datetime
from utils.consts import SCOPES, CREDENTIAL_FILE_PATH, REDIRECT_URI


async def user_auth():
    flow = InstalledAppFlow.from_client_secrets_file(
        CREDENTIAL_FILE_PATH,
        SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    auth_url, _ = flow.authorization_url()
    return auth_url
