from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os.path
import base64
import datetime

from services.user import user
from services.messages import messages
from utils import date_conv
from utils.consts import SCOPES, CREDENTIAL_FILE_PATH, REDIRECT_URI


def fetch_credentials(code):
    flow = Flow.from_client_secrets_file(CREDENTIAL_FILE_PATH, SCOPES)
    flow.redirect_uri = REDIRECT_URI
    flow.fetch_token(code=code)
    return flow.credentials


def fetch_user(code):
    credentials = fetch_credentials(code)
    user_info_service = build("oauth2", "v2", credentials=credentials)
    user_info = user_info_service.userinfo().get().execute()
    return user_info


def fetch_emails(code):
    credentials = fetch_credentials(code)
    service = build("gmail", "v1", credentials=credentials)

    end_date = datetime.datetime.now()  # Today
    start_date = end_date - datetime.timedelta(days=30)

    start_date = start_date.strftime("%Y/%m/%d")
    end_date = end_date + datetime.timedelta(days=1)
    end_date = end_date.strftime("%Y/%m/%d")
    next_page_token = None

    email_list = []

    while True:
        message_list_obj = (
            service.users()
            .messages()
            .list(
                userId="me",
                q="after:{} before:{}".format(start_date, end_date),
                maxResults=500,
                pageToken=next_page_token,
            )
            .execute()
        )

        message_list = message_list_obj.get("messages", [])

        # Check if any messages were returned
        if not message_list:
            print("No more messages found.")
            break

        for message_object in message_list:
            message_id = message_object.get("id", None)
            thread_id = message_object.get("threadId", None)
            mail_from = None
            mail_to = None
            mail_subject = ""
            mail_date = None
            mail_body = ""

            # Retrieve the full message using the message ID
            message = (
                service.users().messages().get(userId="me", id=message_id).execute()
            )

            # Process headers
            for header in message.get("payload", {}).get("headers", []):
                if header.get("name") == "From":
                    from_value = header.get("value", "")
                    if from_value != "":
                        mail_from = (
                            from_value.split("<")[1].split(">")[0]
                            if "<" in from_value and ">" in from_value
                            else from_value
                        )

                if header.get("name") == "Subject":
                    mail_subject = header.get("value", "")

                if header.get("name") == "Date":
                    date = header.get("value", "")
                    if date != "":
                        date = date_conv.remove_after_time(date)
                        mail_date = (
                            datetime.datetime.strptime(
                                date + " UTC", "%a, %d %b %Y %H:%M:%S %Z"
                            ).strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-4]
                            + "Z"
                        )

                if header.get("name") == "To":
                    to_value = header.get("value", "")
                    if to_value != "":
                        mail_to = (
                            to_value.split("<")[1].split(">")[0]
                            if "<" in to_value and ">" in to_value
                            else to_value
                        )

            for parts in message.get("payload", {}).get("parts", []):
                if parts["mimeType"] == "text/plain":
                    data = parts["body"]["data"]
                    data_b64 = base64.urlsafe_b64decode(parts["body"]["data"])
                    data_b64_decode = data_b64.decode("utf-8")
                    if data_b64_decode != None:
                        mail_body = data_b64_decode

            if (
                thread_id != None
                or message_id != None
                or mail_from != None
                or mail_to != None
                or mail_date != None
            ):
                email_list.append(
                    {
                        "messageId": message_id,
                        "sender": mail_from,
                        "receiver": mail_to,
                        "subject": mail_subject,
                        "body": mail_body,
                        "date": mail_date,
                        "threadId": thread_id,
                        "label": "inbox",
                        "type": messages.MessageType.EMAIL,
                    }
                )

        next_page_token = message_list_obj.get("nextPageToken", None)
        if not next_page_token:
            break
    return email_list


def fetch_meet(code):
    # Build the Google Meet service using Calendar API
    service = build("meet", "v2", credentials=credentials)
    conference_records = service.conferenceRecords().list()
    for record in conference_records:
        print(record)
        # request = (
        #     service.conferenceRecords()
        #     .transcripts()
        #     .list("conferenceRecords/5e1ef7eb-f6ae-4928-b599-6f685ef685c1")
        # )
        # response = request.execute()
        # print(response)


def fetch_calendar(code):
    credentials = fetch_credentials(code)
    service = build("calendar", "v3", credentials=credentials)

    # Get the current date
    now = datetime.datetime.utcnow().isoformat() + "Z"
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])
    for event in events:
      start = event["start"].get("dateTime", event["start"].get("date"))
      print(start, event["summary"])