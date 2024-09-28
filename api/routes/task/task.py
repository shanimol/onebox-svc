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
from services.tasks import tasks
from services.user import user
import datetime
from services.messages import messages

load_dotenv()
api_host_url = environ["API_HOST_URL"]

app = APIRouter()


@app.get("/")
async def get_by_date():
    try:
        data = await tasks.get_by_date()

        serialized_data = [
            {
                **task.dict(),
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
            }
            for task in data
        ]

        user_ids = []
        user_ids.append(serialized_data[0]["user_id"])

        msg_user_map = {}
        for data in serialized_data:
            msg = await messages.get_message_by_id(data["source_id"])
            user_ids.append(msg.sender_id)
            msg_user_map[data["source_id"]] = msg.sender_id

        users_data = await user.bulk_get_user_by_id(user_ids)

        user_data_map = {}

        for user_data in users_data:
            user_data_map[user_data.id] = user_data

        name = users_data[0].dict()["name"]

        response_data = [
            {
                **data,
                "user_name": name,
                "sender_name": user_data_map[msg_user_map[data["source_id"]]].dict()[
                    "name"
                ],
            }
            for data in serialized_data
        ]

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


class TaskStatusUpdate(BaseModel):
    task_id: str
    status: str


@app.post("/status")
async def update_task_status(data: TaskStatusUpdate):
    try:
        await tasks.update_task(data)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Status Updated",
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
