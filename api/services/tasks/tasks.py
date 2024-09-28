from prisma import Prisma
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timezone


async def get_by_date():
    db = Prisma()
    await db.connect()
    result = await db.task.find_many()
    await db.disconnect()
    return result


async def bulk_create_task(data):
    db = Prisma()
    await db.connect()
    result = await db.task.create_many(
        data=data,
    )
    await db.disconnect()
    return result


async def update_task(data):
    db = Prisma()
    await db.connect()
    result = await db.task.update(
        where={"id": data.dict()["task_id"]}, data={"status": data.dict()["status"]}
    )
    await db.disconnect()
    return result