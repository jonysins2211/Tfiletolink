import time
from Thunder.utils.database import db

# New collection for shortener (separate from user tokens)
short_col = db.shortener_tokens_col


async def store_short_token(token: str, url: str, ttl: int = 43200):
    await short_col.insert_one({
        "token": token,
        "url": url,
        "expires_at": time.time() + ttl,
        "used": False
    })


async def resolve_short_token(token: str):
    data = await short_col.find_one({"token": token})
    if not data:
        return None

    if time.time() > data["expires_at"]:
        await short_col.delete_one({"token": token})
        return None

    if data.get("used"):
        return None

    return data["url"]


async def mark_used(token: str):
    await short_col.update_one(
        {"token": token},
        {"$set": {"used": True}}
    )
