from prisma import Prisma
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    EMAIL = "EMAIL"
    SLACK = "SLACK"


async def create_message_summary(message):
    db = Prisma()
    await db.connect()
    await db.messagesummary.create_many(data=message, skip_duplicates=True)
    await db.disconnect()


async def bulk_get_message_summary(message_ids):
    db = Prisma()
    await db.connect()
    data = await db.messagesummary.find_many(where={"message_id": {"in": message_ids}})
    await db.disconnect()
    return data
