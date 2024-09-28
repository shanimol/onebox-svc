from prisma import Prisma
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    EMAIL = "EMAIL"
    SLACK = "SLACK"


async def create_message(message):
    db = Prisma()
    await db.connect()
    await db.messages.create_many(data=message, skip_duplicates=True)
    await db.disconnect()


async def get_all_messages():
    db = Prisma()
    await db.connect()
    messages = await db.messages.find_many()
    await db.disconnect()
    return messages


async def get_messages_by_date(type):
    db = Prisma()
    await db.connect()
    messages = await db.messages.find_many(where={"source": type})
    await db.disconnect()
    return messages


async def get_message_by_id(id):
    db = Prisma()
    await db.connect()
    messages = await db.messages.find_first(where={"id": id})
    await db.disconnect()
    return messages
