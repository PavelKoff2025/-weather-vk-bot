"""Основной клиент OpenWeatherMap с публичными методами."""

from __future__ import annotations

import logging
import os
from typing import Any

import requests
from dotenv import load_dotenv

from .air_quality import analyze_air_quality
from .config import (
    AIR_POLLUTION_URL,
    CURRENT_WEATHER_URL,
    DIRECT_GEOCODING_URL,
    FORECAST_URL,
    REQUEST_TIMEOUT_SECONDS,
    REVERSE_GEOCODING_URL,
)
from .exceptions import APIConnectionError, CityNotFoundError, OpenWeatherAPIError
from .utils import format_basic_weather, format_extended_weather, format_forecast_data


logger = logging.getLogger(__name__)


class OpenWeatherAPI:
    """Клиент для работы с API OpenWeatherMap."""

    CURRENT_WEATHER_URL = CURRENT_WEATHER_URL
    FORECAST_URL = FORECAST_URL
    AIR_POLLUTION_URL = AIR_POLLUTION_URL
    DIRECT_GEOCODING_URL = DIRECT_GEOCODING_URL
    REVERSE_GEOCODING_URL = REVERSE_GEOCODING_URL
    REQUEST_TIMEOUT_SECONDS = REQUEST_TIMEOUT_SECONDS

    def __init__(self, api_key: str | None = None, use_session: bool = True) -> None:
        """Инициализирует клиент OpenWeatherMap и подготавливает HTTP-сессию."""
        load_dotenv()

        resolved_api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        if not resolved_api_key:
            raise OpenWeatherAPIError(
                "API-ключ не найден. Укажите его явно или добавьте OPENWEATHER_API_KEY в .env."
            )

        self.api_key = resolved_api_key
        self._session = requests.Session() if use_session else None

    def close(self) -> None:
        """Закрывает HTTP-сессию, если она была создана."""
        if self._session is not None:
            self._session.close()

    def _make_request(self, url: str, params: dict[str, Any]) -> dict[str, Any] | list[dict[str, Any]]:
        """Выполняет GET-запрос к API и возвращает JSON-ответ."""
        requester = self._session if self._session is not None else requests
        try:
            response = requester.get(url, params=params, timeout=self.REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
        except requests.HTTPError as exc:
            logger.error("HTTP-ошибка при запросе к OpenWeatherMap: %s", exc)
            raise APIConnectionError("Ошибка ответа API OpenWeatherMap.") from exc
        except requests.RequestException as exc:
            if url.startswith("http://api.openweathermap.org/"):
                secure_url = url.replace("http://", "https://", 1)
                logger.warning(
                    "Ошибка соединения по HTTP, выполняется повтор через HTTPS: %s",
                    exc,
                )
                try:
                    response = requester.get(
                        secure_url,
                        params=params,
                        timeout=self.REQUEST_TIMEOUT_SECONDS,
                    )
                    response.raise_for_status()
                except requests.HTTPError as retry_exc:
                    logger.error("HTTP-ошибка при повторном запросе через HTTPS: %s", retry_exc)
                    raise APIConnectionError("Ошибка ответа API OpenWeatherMap.") from retry_exc
                except requests.RequestException as retry_exc:
                    logger.error("Ошибка соединения с OpenWeatherMap через HTTPS: %s", retry_exc)
                    raise APIConnectionError("Ошибка соединения с API OpenWeatherMap.") from retry_exc
            else:
                logger.error("Ошибка соединения с OpenWeatherMap: %s", exc)
                raise APIConnectionError("Ошибка соединения с API OpenWeatherMap.") from exc

        try:
            payload: Any = response.json()
        except ValueError as exc:
            logger.error("Некорректный JSON-ответ от OpenWeatherMap: %s", exc)
            raise APIConnectionError("Получен некорректный ответ от API OpenWeatherMap.") from exc

        if not isinstance(payload, (dict, list)):
            logger.error("JSON-ответ имеет неожиданный формат.")
            raise APIConnectionError("Получен некорректный формат ответа API OpenWeatherMap.")

        return payload

    def _direct_geocode(self, city: str) -> tuple[float, float]:
        """Определяет координаты города по его названию."""
        params = {"q": city, "limit": 1, "appid": self.api_key}
        response = self._make_request(self.DIRECT_GEOCODING_URL, params)
        if not isinstance(response, list) or not response:
            logger.warning("Город не найден через прямое геокодирование: %s", city)
            raise CityNotFoundError(f"Город '{city}' не найден.")

        first_item = response[0]
        lat = first_item.get("lat")
        lon = first_item.get("lon")
        if lat is None or lon is None:
            logger.error("В ответе геокодирования отсутствуют координаты для города: %s", city)
            raise APIConnectionError("Не удалось получить координаты города.")

        return float(lat), float(lon)

    def _reverse_geocode(self, lat: float, lon: float) -> str:
        """Определяет название города по координатам."""
        params = {"lat": lat, "lon": lon, "limit": 1, "appid": self.api_key}
        response = self._make_request(self.REVERSE_GEOCODING_URL, params)
        if not isinstance(response, list) or not response:
            logger.warning(
                "Не удалось определить город по координатам: lat=%s, lon=%s",
                lat,
                lon,
            )
            raise CityNotFoundError("Город по указанным координатам не найден.")

        city_name = response[0].get("name")
        if not city_name:
            logger.error(
                "В ответе обратного геокодирования отсутствует имя города: lat=%s, lon=%s",
                lat,
                lon,
            )
            raise APIConnectionError("Не удалось определить название города.")

        return str(city_name)

    def _current_weather(self, lat: float, lon: float) -> dict[str, Any]:
        """Получает текущую погоду по координатам."""
        params = {"lat": lat, "lon": lon, "appid": self.api_key, "lang": "ru"}
        response = self._make_request(self.CURRENT_WEATHER_URL, params)
        if not isinstance(response, dict):
            logger.error("Некорректный формат ответа текущей погоды.")
            raise APIConnectionError("Получен некорректный формат данных текущей погоды.")
        return response

    def _forecast_weather(self, lat: float, lon: float) -> dict[str, Any]:
        """Получает прогноз погоды на 5 дней по координатам."""
        params = {"lat": lat, "lon": lon, "appid": self.api_key, "lang": "ru"}
        response = self._make_request(self.FORECAST_URL, params)
        if not isinstance(response, dict):
            logger.error("Некорректный формат ответа прогноза погоды.")
            raise APIConnectionError("Получен некорректный формат данных прогноза погоды.")
        return response

    def _air_pollution(self, lat: float, lon: float) -> dict[str, Any]:
        """Получает данные о загрязнении воздуха по координатам."""
        params = {"lat": lat, "lon": lon, "appid": self.api_key}
        response = self._make_request(self.AIR_POLLUTION_URL, params)
        if not isinstance(response, dict):
            logger.error("Некорректный формат ответа по качеству воздуха.")
            raise APIConnectionError("Получен некорректный формат данных качества воздуха.")
        return response

    def _format_basic_weather(self, weather_data: dict[str, Any]) -> dict[str, Any]:
        """Формирует базовый словарь с погодными параметрами."""
        return format_basic_weather(weather_data)

    def _format_extended_weather(
        self, weather_data: dict[str, Any], air_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Формирует расширенный словарь погоды с данными по воздуху."""
        return format_extended_weather(weather_data, air_data)

    def _format_forecast_data(self, forecast_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Преобразует ответ прогноза в компактный список значений."""
        return format_forecast_data(forecast_data)

    def _analyze_air_quality(self, air_data: dict[str, Any]) -> dict[str, Any]:
        """Анализирует показатели загрязнения и возвращает итоговую оценку."""
        return analyze_air_quality(air_data)

    def get_weather_by_city(self, city: str, extended: bool = False) -> dict[str, Any]:
        """Возвращает текущую погоду по названию города."""
        lat, lon = self._direct_geocode(city)
        weather_data = self._current_weather(lat, lon)
        weather_data["name"] = city
        if not extended:
            return self._format_basic_weather(weather_data)

        air_data = self._air_pollution(lat, lon)
        return self._format_extended_weather(weather_data, air_data)

    def get_forecast_by_city(self, city: str, extended: bool = False) -> dict[str, Any]:
        """Возвращает прогноз погоды на 5 дней по названию города."""
        lat, lon = self._direct_geocode(city)
        forecast_data = self._forecast_weather(lat, lon)
        result: dict[str, Any] = {
            "city": city,
            "forecast": self._format_forecast_data(forecast_data),
        }

        if extended:
            air_data = self._air_pollution(lat, lon)
            result["air_quality"] = self._analyze_air_quality(air_data)

        return result

    def get_weather_by_coordinates(
        self, lat: float, lon: float, extended: bool = False
    ) -> dict[str, Any]:
        """Возвращает текущую погоду по координатам."""
        weather_data = self._current_weather(lat, lon)
        city_name: str | None = None

        try:
            city_name = self._reverse_geocode(lat, lon)
        except CityNotFoundError:
            logger.warning("Город для координат lat=%s, lon=%s не определен.", lat, lon)

        if city_name:
            weather_data["name"] = city_name

        if not extended:
            return self._format_basic_weather(weather_data)

        air_data = self._air_pollution(lat, lon)
        return self._format_extended_weather(weather_data, air_data)
