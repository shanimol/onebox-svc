from fastapi import APIRouter, Body, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from services.oauth import oauth
from dotenv import load_dotenv
from os import environ
from services.mq import q
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from services.google.fetch import fetch_user, fetch_emails
from slack_sdk import WebClient
from services.user import user
from services.messages import messages
from services.messagesummary import messagesummary

load_dotenv()
api_host_url = environ["API_HOST_URL"]

app = APIRouter()


@app.get("/")
async def get_email_by_date():
    try:
        data = await messages.get_messages_by_date(type="EMAIL")

        serialized_data = [
            {
                **meet.dict(),
                "date": meet.date.isoformat(),
                "created_at": meet.created_at.isoformat(),
                "updated_at": meet.updated_at.isoformat(),
            }
            for meet in data
        ]

        MessageIdMap = {}

        message_ids = []

        for data in serialized_data:
            MessageIdMap[data["id"]] = data
            message_ids.append(data["id"])

        message_summary = await messagesummary.bulk_get_message_summary(message_ids)

        response_data = []

        for summary in message_summary:
            res = {
                **MessageIdMap[summary.message_id],
                "summary": summary.summary,
            }
            response_data.append(res)

        user_ids = []
        for data in response_data:
            user_ids.append(data["user_id"])
            user_ids.append(data["sender_id"])

        users = await user.bulk_get_user_by_id(user_ids)
        user_id_name_map = {}
        for u in users:
            user_id_name_map[u.id] = u.name

        res = []
        for data in response_data:
            r = {
                **data,
                "user_name": user_id_name_map[data["user_id"]],
                "sender_name": user_id_name_map[data["sender_id"]],
            }
            res.append(r)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Data Fetched",
                "data": res,
            },
        )
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Something Went Wrong!",
            },
        )
