from prisma import Prisma


async def bulk_get_calendar_items():
    db = Prisma()
    await db.connect()
    result = await db.calendar.find_many()
    await db.disconnect()
    return result


async def bulk_insert_calendar_items(data):
    serialized_data = [
        {
            **calendar.dict(),
        }
        for calendar in data.data
    ]
    db = Prisma()
    await db.connect()
    await db.calendar.create_many(data=serialized_data, skip_duplicates=True)
    await db.disconnect()
