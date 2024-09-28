from fastapi import APIRouter, Body, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from services.oauth import oauth
from dotenv import load_dotenv
from os import environ
from services.mq import q
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from slack_sdk import WebClient
from services.user import user
from services.google.fetch import fetch_user, fetch_emails, fetch_calendar
from services.slack.oauth import slack_oauth, slack_redirect
from services.messages import messages as message_repo
from services.engine import engine
import json
from services.tasks import tasks as tasks_repo
from services.messagesummary import messagesummary as messagesummary_repo
from utils.consts import SLACK_BOT_TOKEN


load_dotenv()
api_host_url = environ["API_HOST_URL"]

app = APIRouter()

SCOPES = [
    "https://www.googleapis.com/auth/meetings.space.readonly",
    "https://www.googleapis.com/auth/meetings.space.created",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/calendar.events.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
    "openid",
]


@app.get("/signin")
async def user_auth():
    try:
        url = await oauth.user_auth()
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Auth Success!", "auth_url": url},
        )
    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Something Went Wrong!",
            },
        )


@app.get("/link/slack")
async def link_slack():
    try:
        url = slack_oauth()
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Auth Success!", "auth_url": url},
        )
    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Something Went Wrong!",
            },
        )


@app.get("/oauth/callback")
async def user_auth(
    state: str = Query(None),
    code: str = Query(None),
    scope: str = Query(None),
    authuser: str = Query(None),
    prompt: str = Query(None),
):
    try:
        user_info = fetch_user(code)
        await user.create_user(
            {
                "name": user_info["name"],
                "email": user_info["email"],
                "picture": user_info["picture"],
                "google_token": credentials.token,
                "google_refresh_token": credentials.refresh_token,
                "google_token_expiry": credentials.expiry,
                "status": "ONBOARDED"
            }
        )
        email_list = fetch_emails(code)
        print(len(email_list))
      
        users = []
        emails = []
        for email in email_list:
            sender = email["mail_from"]
            emails.append(sender)
            users.append({"name": sender.split("@")[0], "email": sender, "status": "UNVERIFEID"})
      
        await user.bulk_create_user(user_data=users)
      
        users = await user.get_users_by_email(emails=emails)
        emailToId = {}
        for user in users:
            emailToId[user["email"]] = user["id"]
        
        message_models = []
        for email in email_list:
            emaildata = {}
            emaildata["sender_id"] = emailToId[email["mail_from"]]
            emaildata["body"] = email["mail_body"]
            emaildata["user_id"] = emailToId[user_info["email"]]
            emaildata["date"] = email["mail_date"]
            emaildata["message_id"] = email["message_id"]
            emaildata["source"] = "SLACK"
            emaildata["subject"] = email["mail_subject"]
            message_models.append(emaildata)

        await message_repo.create_message(message_models)
 
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Auth Success!"},
        )
    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Something Went Wrong in redirection",
            },
        )


@app.get("/load_access_points")
async def q_test():
    msgs = await message_repo.get_all_messages()
    
    serialized_data = [
            {
                **task.dict(),
                "date": task.created_at.isoformat(),
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
            }
            for task in msgs
        ]
    
    for d in serialized_data:
        d.pop("message_id", None)

    client = await engine.getengine()
    result = client.generate_action_points(serialized_data)
    print(result.content)
    actionpoints = json.loads(result.content)
    tasks = []
    for actionpoint in actionpoints:
        priority = 0
        try:
            priority = int(actionpoint["priority"])
        except  ValueError:
            _ = None

        tasks.append(
            {
                "source_id": actionpoint["message_id"],
                "user_id": "a1e00c2a-4f08-4ef0-97ad-014743854018",
                "content": actionpoint["action_point"],
                "source_type": "MESSAGE",
                "priority": priority,
                "status": "PENDING"
            }
        )
    await tasks_repo.bulk_create_task(tasks)

    return JSONResponse(
        status_code=200,
        content=actionpoints,
    )
    


@app.get("/load_slack_users")
async def q_test():
    client = WebClient(token=SLACK_BOT_TOKEN)
    result = client.users_list()
    users = []
    for member in result["members"]:
        if member["is_bot"] == False:
            profile = member["profile"]
            email = profile.get("email", "")
            name = profile.get("real_name", "")
            users.append(
                {
                    "name": name,
                    "email": email,
                    "status": "UNVERIFEID",
                    "slack_id": member["id"],
                }
            )

    result = await user.bulk_create_user(user_data=users)

    return JSONResponse(
        status_code=200,
        content=result,
    )

@app.get("/load_message_summary")
async def q_test():
    msgs = await message_repo.get_all_messages()
    
    serialized_data = [
            {
                **task.dict(),
                "date": task.created_at.isoformat(),
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
            }
            for task in msgs
        ]
    
    for d in serialized_data:
        d.pop("message_id", None)

    client = await engine.getengine()
    result = client.summarize_message(serialized_data)
    summaries = json.loads(result.content)
    message_summaries = []
    for summary in summaries:
        message_summaries.append(
            {
                "message_id": summary["message_id"],
                "summary": summary["summary"]
            }
        )
    await messagesummary_repo.create_message_summary(message_summaries)

    return JSONResponse(
        status_code=200,
        content=summaries,
    )


@app.get("/slack/callback")
async def user_auth(code: str, state: str):
    await slack_redirect(code, state)
    return JSONResponse(
        status_code=200,
        content={"success": True, "message": "Auth Success!"},
    )
