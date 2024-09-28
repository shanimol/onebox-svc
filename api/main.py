from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routes.oauth import oauth
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from os import environ
from threading import Thread
from services.mq import q
from routes.task import task
from routes.email import email
from routes.slackmessages import slackmessages
from routes.meetings import meetings
from routes.calendar import calendar
from routes.chat import chat

load_dotenv()
frontend_host_url = environ["FRONTEND_HOST_URL"]


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

t = Thread(target=q.init_kafka_consumer, args=[])
t.start()


@app.get("/")
def read_root():
    return {"success": True, "message": "API Running Successfully"}


app.include_router(oauth.app, prefix="/api/auth", tags=["auth"])
app.include_router(task.app, prefix="/api/task", tags=["task"])
app.include_router(meetings.app, prefix="/api/meetings", tags=["meetings"])
app.include_router(email.app, prefix="/api/email", tags=["email"])
app.include_router(
    slackmessages.app, prefix="/api/slackmessages", tags=["slackmessages"]
)
app.include_router(calendar.app, prefix="/api/calendar", tags=["calendar"])
app.include_router(chat.app, prefix="/api/chat", tags=["chat"])
