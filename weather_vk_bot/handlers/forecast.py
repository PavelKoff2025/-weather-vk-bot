"""Обработчики совместимости для старого сценария прогноза."""

from __future__ import annotations

from vkbottle.bot import Message

from weather_vk_bot.bot import bot, user_storage, weather_service
from weather_vk_bot.handlers import WeatherStates
from weather_vk_bot.handlers.menu import (
    BTN_CHANGE_CITY,
    BTN_COMPARE,
    BTN_EXTENDED,
    BTN_FORECAST,
    BTN_GEO,
    BTN_HELP,
    BTN_MY_CITY,
    BTN_WEATHER_NOW,
    get_main_keyboard,
)


async def _safe_delete_state(peer_id: int) -> None:
    """Безопасно удаляет состояние пользователя, если оно существует."""
    try:
        await bot.state_dispenser.delete(peer_id)
    except KeyError:
        return


@bot.on.message(state=WeatherStates.AWAITING_CITY_FORECAST)
async def forecast_by_city_handler(message: Message) -> None:
    """Обрабатывает ввод города в legacy-сценарии прогноза."""
    city = (message.text or "").strip()
    if not city:
        await message.answer("❌ Пожалуйста, введите название города.")
        return

    if city in {"Назад", "Главное меню"}:
        await _safe_delete_state(message.peer_id)
        await message.answer(
            "Добро пожаловать в VK Weather Bot.\n\nВыберите действие через кнопки ниже.",
            keyboard=get_main_keyboard(),
        )
        return

    if city in {
        BTN_WEATHER_NOW,
        BTN_FORECAST,
        BTN_GEO,
        BTN_EXTENDED,
        BTN_HELP,
        BTN_MY_CITY,
        BTN_CHANGE_CITY,
        BTN_COMPARE,
    }:
        await _safe_delete_state(message.peer_id)
        await message.answer("🔘 Используйте главное меню.", keyboard=get_main_keyboard())
        return

    result = weather_service.get_forecast(city=city)
    if result["success"]:
        user_storage.set_city(message.from_id, city)

    await message.answer(result["message"])
    await message.answer("🔘 Выберите следующее действие:", keyboard=get_main_keyboard())
    await _safe_delete_state(message.peer_id)
