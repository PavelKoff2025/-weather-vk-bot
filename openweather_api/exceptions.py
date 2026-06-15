"""Пользовательские исключения для модуля OpenWeatherAPI."""


class OpenWeatherAPIError(Exception):
    """Базовое исключение для модуля OpenWeatherAPI."""


class CityNotFoundError(OpenWeatherAPIError):
    """Город не найден."""


class APIConnectionError(OpenWeatherAPIError):
    """Ошибка соединения с API OpenWeatherMap."""
