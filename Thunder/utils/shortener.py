import cloudscraper
import uuid
from abc import ABC, abstractmethod
from base64 import b64encode
from random import random, choice
from urllib.parse import quote

from Thunder.vars import Var
from Thunder.utils.logger import logger

# TEMP in-memory token store
# (replace with Mongo/Redis later)
TOKEN_STORE = {}


class ShortenerPlugin(ABC):
    @classmethod
    @abstractmethod
    def matches(cls, domain: str) -> bool:
        pass

    @abstractmethod
    async def shorten(self, url: str, api_key: str) -> str:
        pass


class LinkvertisePlugin(ShortenerPlugin):
    @classmethod
    def matches(cls, domain: str) -> bool:
        return "linkvertise" in domain

    async def shorten(self, url: str, api_key: str) -> str:
        encoded_url = quote(b64encode(url.encode("utf-8")))
        return choice([
            f"https://link-to.net/{api_key}/{random()*1000}/dynamic?r={encoded_url}",
            f"https://up-to-down.net/{api_key}/{random()*1000}/dynamic?r={encoded_url}",
            f"https://direct-link.net/{api_key}/{random()*1000}/dynamic?r={encoded_url}",
            f"https://file-link.net/{api_key}/{random()*1000}/dynamic?r={encoded_url}",
        ])


class GenericShortenerPlugin(ShortenerPlugin):
    @classmethod
    def matches(cls, domain: str) -> bool:
        return True

    async def shorten(self, url: str, api_key: str) -> str:
        return url


class ShortenerSystem:
    def __init__(self):
        self.session = None
        self.plugin = None
        self.ready = False

    async def initialize(self):
        if self.ready:
            return

        self.session = cloudscraper.create_scraper()
        self.plugin = GenericShortenerPlugin()
        self.plugin.session = self.session
        self.ready = True

    async def short_url(self, url: str) -> str:
        if not self.ready:
            return url

        try:
            # 1️⃣ Create shortener internally
            short_url = await self.plugin.shorten(
                url, Var.URL_SHORTENER_API_KEY
            )

            # 2️⃣ Create secure token
            token = uuid.uuid4().hex

            # 3️⃣ Store mapping
            TOKEN_STORE[token] = short_url

            # 4️⃣ Send ONLY token link
            return (
                "https://movie-loverzz-files.vercel.app/api/redirect"
                f"?token={token}"
            )

        except Exception as e:
            logger.error(f"Shortener error: {e}", exc_info=True)
            return url


_system = ShortenerSystem()


async def shorten(url: str) -> str:
    if not _system.ready:
        await _system.initialize()
    return await _system.short_url(url)


# 🔥 TOKEN RESOLVER FOR REDIRECT SERVER
def resolve_token(token: str):
    return TOKEN_STORE.get(token)
