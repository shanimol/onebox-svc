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
from services.engine import engine
import json

load_dotenv()
api_host_url = environ["API_HOST_URL"]

app = APIRouter()


@app.post("/")
async def new_message(data):
    try:
        bot = await engine.getengine()
        print(data)
        answer = bot.ask_question(data)
        ans = json.loads(answer.content)
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": ans["result"]},
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Something Went Wrong!",
                "log": f"{api_host_url}/logs/error.log",
            },
        )
