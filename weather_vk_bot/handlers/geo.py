"""Обработчики геолокации пользователя."""

from __future__ import annotations

import logging

from vkbottle.bot import Message

from weather_vk_bot.bot import bot, user_storage, weather_service
from weather_vk_bot.handlers import WeatherStates
from weather_vk_bot.handlers.menu import BTN_GEO, get_main_keyboard


logger = logging.getLogger(__name__)

async def _safe_delete_state(peer_id: int) -> None:
    """Безопасно удаляет состояние пользователя, если оно существует."""
    try:
        await bot.state_dispenser.delete(peer_id)
    except KeyError:
        return


@bot.on.message(text=BTN_GEO)
async def ask_for_geo(message: Message) -> None:
    """Просит пользователя отправить геолокацию через интерфейс VK."""
    await message.answer(
        "📍 Отправьте вашу геолокацию через кнопку прикрепления в VK.",
        keyboard=get_main_keyboard(),
    )


@bot.on.message(func=lambda m: m.geo is not None)
async def geo_weather_handler(message: Message) -> None:
    """Обрабатывает сообщение с геолокацией и возвращает погоду по координатам."""
    try:
        coordinates = message.geo.coordinates
        lat = coordinates.latitude
        lon = coordinates.longitude
    except Exception:
        logger.exception("Ошибка разбора геолокации у пользователя %s.", message.from_id)
        await message.answer(
            "❌ Не удалось получить геолокацию. Отправьте город текстом.",
            keyboard=get_main_keyboard(),
        )
        return

    state_peer = await bot.state_dispenser.get(message.peer_id)
    state_value = state_peer.state if state_peer is not None else None

    if state_value == WeatherStates.AWAITING_COMPARE_FIRST:
        first_result = weather_service.get_brief_weather_by_coordinates(lat=lat, lon=lon)
        if not first_result["success"]:
            await message.answer(first_result["message"], keyboard=get_main_keyboard())
            return
        await bot.state_dispenser.set(
            message.peer_id,
            WeatherStates.AWAITING_COMPARE_SECOND,
            first_weather=first_result["data"],
        )
        await message.answer(
            "✅ Первая геолокация принята.\n"
            "Отправьте вторую геолокацию или введите второй город.",
            keyboard=get_main_keyboard(),
        )
        return

    if state_value == WeatherStates.AWAITING_COMPARE_SECOND:
        if state_peer is None or "first_weather" not in state_peer.payload:
            await bot.state_dispenser.set(message.peer_id, WeatherStates.AWAITING_COMPARE_FIRST)
            await message.answer("⚠️ Не найден первый город. Начните сравнение заново.", keyboard=get_main_keyboard())
            return

        second_result = weather_service.get_brief_weather_by_coordinates(lat=lat, lon=lon)
        if not second_result["success"]:
            await message.answer(second_result["message"], keyboard=get_main_keyboard())
            return

        first = state_peer.payload["first_weather"]
        second = second_result["data"]
        await _safe_delete_state(message.peer_id)
        await message.answer(weather_service.format_brief_block("1️⃣ Первый город:", first))
        await message.answer(weather_service.format_brief_block("2️⃣ Второй город:", second))
        await message.answer(weather_service.build_comparison_message(first, second))
        await message.answer("🔘 Сравнение завершено. Выберите действие:", keyboard=get_main_keyboard())
        return

    extended = user_storage.get_extended(message.from_id)
    result = weather_service.get_weather_by_coordinates(lat=lat, lon=lon, extended=extended)

    if result["success"]:
        city = result["data"].get("name")
        if city:
            user_storage.set_city(message.from_id, city)
    else:
        logger.warning(
            "Ошибка погоды по координатам пользователя %s: %s",
            message.from_id,
            result["message"],
        )

    await message.answer(result["message"])
    await message.answer("🔘 Главное меню:", keyboard=get_main_keyboard())
