"""Инициализация бота, сервисов и хранилища состояний."""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from vkbottle import API, Bot
from vkbottle.http import AiohttpClient

from weather_vk_bot.services.weather_service import WeatherService
from weather_vk_bot.services.state_manager import UserStorage


logger = logging.getLogger(__name__)

load_dotenv()

VK_TOKEN = os.getenv("VK_TOKEN")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
VK_DISABLE_SSL_VERIFY = os.getenv("VK_DISABLE_SSL_VERIFY", "0").strip() in {"1", "true", "True"}

if not VK_TOKEN:
    raise RuntimeError("Не найден токен VK_TOKEN в переменных окружения.")

if VK_DISABLE_SSL_VERIFY:
    class InsecureAiohttpClient(AiohttpClient):
        """HTTP-клиент для dev-среды с отключенной SSL-проверкой."""

        @asynccontextmanager
        async def request(
            self,
            url: str,
            method: str = "GET",
            data: dict[str, Any] | None = None,
            **kwargs: Any,
        ) -> AsyncGenerator[Any]:
            kwargs.setdefault("ssl", False)
            async with super().request(url=url, method=method, data=data, **kwargs) as response:
                yield response

    logger.warning(
        "Отключена проверка SSL для VK API. Используйте только в локальной среде разработки."
    )
    insecure_http_client = InsecureAiohttpClient()
    vk_api = API(token=VK_TOKEN, http_client=insecure_http_client)
    bot = Bot(api=vk_api)
else:
    bot = Bot(token=VK_TOKEN)

user_storage = UserStorage()
weather_service = WeatherService(api_key=OPENWEATHER_API_KEY)

logger.info("Бот и сервисы успешно инициализированы.")
