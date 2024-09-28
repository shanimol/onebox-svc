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
from services.channels import channel
from services.messagesummary import messagesummary

load_dotenv()
api_host_url = environ["API_HOST_URL"]

app = APIRouter()


@app.get("/")
async def get_email_by_date():
    try:
        data = await messages.get_messages_by_date(type="SLACK")
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

        message_id_summary_map = {}

        for summary in message_summary:
            res = {
                **MessageIdMap[summary.message_id],
                "summary": summary.summary,
            }
            message_id_summary_map[summary.message_id] = summary.summary

        channelMessageMap = {}

        channels = []

        for data in serialized_data:
            channelMessageMap[data["channel_id"]] = data
            channels.append(data["channel_id"])

        channel_data = await channel.bulk_get_channels_by_id(channels)
        response_data = []

        for data in channel_data:
            index = channelMessageMap[data.external_id]["id"]
            res = {
                **channelMessageMap[data.external_id],
                "channel": {
                    **data.dict(),
                    "created_at": data.created_at.isoformat(),
                    "updated_at": data.updated_at.isoformat(),
                },
                "summary": message_id_summary_map[index],
            }
            response_data.append(res)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Data Fetched",
                "data": response_data,
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
