from prisma import Prisma

async def bulk_get_channels_by_id(id):
    db = Prisma()
    await db.connect()
    result = await db.channels.find_many(where={"external_id": {"in": id}})
    await db.disconnect()
    return result
