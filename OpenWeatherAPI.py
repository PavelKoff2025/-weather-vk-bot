"""Совместимый экспорт клиента OpenWeatherAPI."""

from openweather_api import APIConnectionError, CityNotFoundError, OpenWeatherAPI, OpenWeatherAPIError

__all__ = [
    "OpenWeatherAPI",
    "OpenWeatherAPIError",
    "CityNotFoundError",
    "APIConnectionError",
]
