from prisma import Prisma
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from prisma import types


class User(BaseModel):
    id: int
    name: str
    email: EmailStr
    picture: Optional[str]
    token: str
    refresh_token: str
    expiry: datetime


async def create_user(user_data: User):
    db = Prisma()
    await db.connect()
    result = await db.user.upsert(
        where={"email": user_data["email"]},
        data={"create": user_data, "update": user_data},
    )
    await db.disconnect()
    return result

async def bulk_create_user(user_data):
    db = Prisma()
    await db.connect()
    result = await db.user.create_many(
       data= user_data,
       skip_duplicates=True
    )
    await db.disconnect()
    return result

async def get_user_by_email(email: EmailStr):
    db = Prisma()
    await db.connect()
    result = await db.user.find_first(where={"email": email})
    await db.disconnect()
    return result

async def get_users_by_email(emails):
    db = Prisma()
    await db.connect()
    result = await db.user.find_many(where={"email": {"in": emails}})
    await db.disconnect()
    return result

async def bulk_get_user_by_slack_id(id):
    db = Prisma()
    await db.connect()
    result = await db.user.find_many(where={"slack_id": {"in": id}})
    await db.disconnect()
    return result

async def bulk_get_user_by_id(id):
    db = Prisma()
    await db.connect()
    result = await db.user.find_many(where={"id": {"in": id}})
    await db.disconnect()
    return result