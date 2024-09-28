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
from services.meetings import meetings
import datetime

load_dotenv()
api_host_url = environ["API_HOST_URL"]

app = APIRouter()


@app.get("/")
async def get_by_date():
    try:
        data = await meetings.get_by_date()

        serialized_data = [
            {
                **meet.dict(),
                "start_time": meet.start_time.isoformat(),
                "end_time": meet.end_time.isoformat(),
                "created_at": meet.created_at.isoformat(),
                "updated_at": meet.updated_at.isoformat(),
            }
            for meet in data
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
