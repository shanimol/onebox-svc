from prisma import Prisma
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timezone


async def get_by_date():
    db = Prisma()
    await db.connect()
    result = await db.meeting.find_many()
    await db.disconnect()
    return result
