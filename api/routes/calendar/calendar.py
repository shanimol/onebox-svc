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
from services.calendar import calendar
from datetime import datetime

load_dotenv()
api_host_url = environ["API_HOST_URL"]

app = APIRouter()


class CalendarData(BaseModel):
    task_id: str
    time: datetime


class CreateCalendar(BaseModel):
    data: list[CalendarData]


@app.get("/")
async def get_calendar():
    try:
        data = await calendar.bulk_get_calendar_items()
        serialized_data = [
            {
                **calendar.dict(),
                "time": calendar.time.isoformat(),
                "created_at": calendar.created_at.isoformat(),
                "updated_at": calendar.updated_at.isoformat(),
            }
            for calendar in data
        ]

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Data Fetched",
                "data": serialized_data,
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


@app.post("/")
async def add_calendar(data: CreateCalendar):
    try:
        await calendar.bulk_insert_calendar_items(data)
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Calendar Updated",
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
