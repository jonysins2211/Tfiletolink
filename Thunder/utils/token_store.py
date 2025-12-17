import time

TOKEN_DB = {}

def store_token(token, short_url, ttl=43200):  # 12 hours
    TOKEN_DB[token] = {
        "url": short_url,
        "expires": time.time() + ttl
    }

def resolve_token(token):
    data = TOKEN_DB.get(token)
    if not data:
        return None

    if time.time() > data["expires"]:
        TOKEN_DB.pop(token, None)
        return None

    return data["url"]

def delete_token(token):
    TOKEN_DB.pop(token, None)
