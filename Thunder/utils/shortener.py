import cloudscraper
import string
from abc import ABC, abstractmethod
from base64 import b64encode
from random import choice, randint, choices
from urllib.parse import quote
import asyncio

from Thunder.vars import Var
from Thunder.utils.logger import logger
from Thunder.utils.shortener_tokens import store_short_token


# =========================
# Helper for dummy strings
# =========================
def dummy_string(length=12):
    return ''.join(
        choices(string.ascii_letters + string.digits, k=length)
    )


# =========================
# Base Plugin
# =========================
class ShortenerPlugin(ABC):

    @classmethod
    @abstractmethod
    def matches(cls, domain: str) -> bool:
        pass

    @abstractmethod
    async def shorten(self, url: str, api_key: str) -> str:
        pass


# =========================
# Linkvertise Plugin
# =========================
class LinkvertisePlugin(ShortenerPlugin):

    @classmethod
    def matches(cls, domain: str) -> bool:
        return "linkvertise" in domain

    async def shorten(self, url: str, api_key: str) -> str:
        encoded_url = quote(
            b64encode(url.encode("utf-8")).decode("utf-8")
        )
        rand = randint(100, 9999)

        return choice([
            f"https://link-to.net/{api_key}/{rand}/dynamic?r={encoded_url}",
            f"https://up-to-down.net/{api_key}/{rand}/dynamic?r={encoded_url}",
            f"https://direct-link.net/{api_key}/{rand}/dynamic?r={encoded_url}",
            f"https://file-link.net/{api_key}/{rand}/dynamic?r={encoded_url}",
        ])


# =========================
# Bitly Plugin
# =========================
class BitlyPlugin(ShortenerPlugin):

    @classmethod
    def matches(cls, domain: str) -> bool:
        return "bitly.com" in domain

    async def shorten(self, url: str, api_key: str) -> str:
        response = self.session.post(
            "https://api-ssl.bit.ly/v4/shorten",
            json={"long_url": url},
            headers={"Authorization": f"Bearer {api_key}"}
        )
        if response.status_code == 200:
            return response.json().get("link", url)
        return url


# =========================
# Ouo.io Plugin
# =========================
class OuoIoPlugin(ShortenerPlugin):

    @classmethod
    def matches(cls, domain: str) -> bool:
        return "ouo.io" in domain

    async def shorten(self, url: str, api_key: str) -> str:
        response = self.session.get(
            f"https://ouo.io/api/{api_key}?s={quote(url)}"
        )
        if response.status_code == 200 and response.text:
            return response.text.strip()
        return url


# =========================
# Cutt.ly Plugin
# =========================
class CuttLyPlugin(ShortenerPlugin):

    @classmethod
    def matches(cls, domain: str) -> bool:
        return "cutt.ly" in domain

    async def shorten(self, url: str, api_key: str) -> str:
        response = self.session.get(
            f"https://cutt.ly/api/api.php?key={api_key}&short={quote(url)}"
        )
        if response.status_code == 200:
            return response.json()["url"]["shortLink"]
        return url


# =========================
# Generic Shortener Plugin
# =========================
class GenericShortenerPlugin(ShortenerPlugin):

    @classmethod
    def matches(cls, domain: str) -> bool:
        return True

    async def shorten(self, url: str, api_key: str) -> str:
        response = self.session.get(
            f"https://{self.domain}/api?api={api_key}&url={quote(url)}"
        )
        if response.status_code == 200:
            return response.json().get("shortenedUrl", url)
        return url


# =========================
# Shortener System
# =========================
class ShortenerSystem:

    def __init__(self):
        self.session = None
        self.plugin = None
        self.ready = False

    def _get_plugin_class(self, domain: str):
        for plugin_class in ShortenerPlugin.__subclasses__():
            if plugin_class.matches(domain):
                return plugin_class
        return GenericShortenerPlugin

    async def initialize(self) -> bool:
        if self.ready:
            return True

        if not (
            getattr(Var, "SHORTEN_ENABLED", False)
            or getattr(Var, "SHORTEN_MEDIA_LINKS", False)
        ):
            return False

        site = getattr(Var, "URL_SHORTENER_SITE", "")
        api_key = getattr(Var, "URL_SHORTENER_API_KEY", "")

        if not (site and api_key):
            return False

        try:
            self.session = cloudscraper.create_scraper(
                browser={
                    "browser": "chrome",
                    "platform": "windows",
                    "desktop": True,
                    "mobile": False
                },
                delay=1
            )

            plugin_class = self._get_plugin_class(site)
            self.plugin = plugin_class()
            self.plugin.session = self.session
            self.plugin.domain = site

            self.ready = True
            return True

        except Exception as e:
            logger.error(
                f"Failed to initialize ShortenerSystem: {e}",
                exc_info=True
            )
            return False

    async def short_url(self, url: str) -> str:
        if not self.ready:
            return url

        try:
            # Step 1: generate shortener link
            short_url = await self.plugin.shorten(
                url, Var.URL_SHORTENER_API_KEY
            )

            # Step 2: generate secure token
            token = dummy_string(24)

            # Step 3: store token -> shortener in MongoDB (async, non-blocking)
            asyncio.create_task(
                store_short_token(token, short_url)
            )

            # Step 4: generate fake path (only for obfuscation)
            fake_path = "/".join([
                "verify",
                dummy_string(6),
                "access",
                dummy_string(8),
                "download"
            ])

            return (
                "https://movie-loverzz-files.vercel.app/api/redirect/"
                f"{fake_path}?token={token}"
            )

        except Exception as e:
            logger.error(
                f"Error shortening URL {url}: {e}",
                exc_info=True
            )
            return url


# =========================
# Public API
# =========================
_system = ShortenerSystem()


async def shorten(url: str) -> str:
    if not _system.ready:
        await _system.initialize()
    return await _system.short_url(url)
