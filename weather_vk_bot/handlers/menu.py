"""Обработчики главного меню и навигации бота."""

from __future__ import annotations

import logging

from vkbottle import Keyboard, KeyboardButtonColor, Text
from vkbottle.bot import Message

from weather_vk_bot.bot import bot


logger = logging.getLogger(__name__)

BTN_WEATHER_NOW = "🌤 Погода сейчас"
BTN_FORECAST = "📅 Прогноз 5 дней"
BTN_GEO = "📍 Геолокация"
BTN_EXTENDED = "📊 Расширенный режим"
BTN_MY_CITY = "🏙 Мой город"
BTN_CHANGE_CITY = "✏️ Изменить город"
BTN_COMPARE = "⚖️ Сравнить города"
BTN_HELP = "ℹ️ Помощь"


def get_main_keyboard() -> str:
    """Возвращает JSON-клавиатуру главного меню."""
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text(BTN_WEATHER_NOW), color=KeyboardButtonColor.PRIMARY)
    keyboard.add(Text(BTN_FORECAST), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text(BTN_GEO), color=KeyboardButtonColor.POSITIVE)
    keyboard.add(Text(BTN_EXTENDED), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text(BTN_MY_CITY), color=KeyboardButtonColor.PRIMARY)
    keyboard.add(Text(BTN_COMPARE), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text(BTN_HELP), color=KeyboardButtonColor.SECONDARY)
    return keyboard.get_json()


def get_city_keyboard() -> str:
    """Возвращает клавиатуру управления выбранным городом."""
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text(BTN_CHANGE_CITY), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("Главное меню"), color=KeyboardButtonColor.SECONDARY)
    return keyboard.get_json()


@bot.on.message(text=["/start", "Начать", "Главное меню", "Назад"])
async def main_menu_handler(message: Message) -> None:
    """Показывает главное меню с действиями погодного бота."""
    logger.info("Пользователь %s открыл главное меню.", message.from_id)
    await message.answer(
        "Добро пожаловать в VK Weather Bot.\n\nВыберите действие через кнопки ниже.",
        keyboard=get_main_keyboard(),
    )
