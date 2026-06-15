"""Пакет для работы с API OpenWeatherMap."""

from .client import OpenWeatherAPI
from .exceptions import APIConnectionError, CityNotFoundError, OpenWeatherAPIError

__all__ = [
    "OpenWeatherAPI",
    "OpenWeatherAPIError",
    "CityNotFoundError",
    "APIConnectionError",
]
