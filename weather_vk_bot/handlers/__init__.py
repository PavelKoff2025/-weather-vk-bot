"""Пакет обработчиков сообщений VK бота."""

from vkbottle.dispatch.dispenser.base import BaseStateGroup


class WeatherStates(BaseStateGroup):
    """FSM-состояния для сценариев погодного бота."""

    AWAITING_CITY_WEATHER = "awaiting_city_weather"
    AWAITING_CITY_FORECAST = "awaiting_city_forecast"
    AWAITING_COMPARE_FIRST = "awaiting_compare_first"
    AWAITING_COMPARE_SECOND = "awaiting_compare_second"
