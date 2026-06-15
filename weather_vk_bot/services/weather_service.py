"""Сервис-адаптер между обработчиками VK и OpenWeatherAPI."""

from __future__ import annotations

import logging
from typing import Any

from openweather_api import APIConnectionError, CityNotFoundError, OpenWeatherAPI, OpenWeatherAPIError
from weather_vk_bot.services.formatter import (
    format_temp,
    format_unix_time,
    join_pollutants,
    kelvin_to_celsius,
)


logger = logging.getLogger(__name__)


class WeatherService:
    """Сервис для получения и форматирования погодных данных для бота."""

    def __init__(self, api_key: str | None = None) -> None:
        """Создает экземпляр OpenWeatherAPI."""
        self._api = OpenWeatherAPI(api_key=api_key)

    def _build_weather_message(self, raw_weather: dict[str, Any], extended_data: dict[str, Any] | None) -> str:
        """Собирает человекочитаемое сообщение с текущей погодой."""
        main = raw_weather.get("main") or {}
        weather = raw_weather.get("weather") or []
        wind = raw_weather.get("wind") or {}
        sys_data = raw_weather.get("sys") or {}
        timezone_shift = raw_weather.get("timezone", 0)

        description = "н/д"
        if isinstance(weather, list) and weather:
            description = weather[0].get("description", "н/д")

        lines = [
            f"🌍 Город: {raw_weather.get('name', 'н/д')}",
            f"🌡️ Температура: {format_temp(kelvin_to_celsius(main.get('temp')))}",
            f"🤗 Ощущается: {format_temp(kelvin_to_celsius(main.get('feels_like')))}",
            f"💧 Влажность: {main.get('humidity', 'н/д')}%",
            f"💨 Ветер: {wind.get('speed', 'н/д')} м/с",
            f"☁️ Описание: {description}",
        ]

        if extended_data is not None:
            air = extended_data.get("air_quality") or {}
            lines.extend(
                [
                    f"🌅 Рассвет: {format_unix_time(sys_data.get('sunrise'), timezone_shift)}",
                    f"🌇 Закат: {format_unix_time(sys_data.get('sunset'), timezone_shift)}",
                    f"🏭 Качество воздуха: {air.get('aqi_label', 'н/д')}",
                    f"⚠️ Загрязнители: {join_pollutants(air.get('pollutant_details', []))}",
                    f"🧪 Анализ: {air.get('human_summary', 'н/д')}",
                ]
            )

        return "\n".join(lines)

    @staticmethod
    def _extract_brief_weather(raw_weather: dict[str, Any]) -> dict[str, Any]:
        """Извлекает краткие параметры погоды из сырого ответа."""
        main = raw_weather.get("main") or {}
        weather = raw_weather.get("weather") or []
        wind = raw_weather.get("wind") or {}
        description = "н/д"
        if isinstance(weather, list) and weather:
            description = weather[0].get("description", "н/д")

        return {
            "city": raw_weather.get("name", "н/д"),
            "temp_c": kelvin_to_celsius(main.get("temp")),
            "feels_like_c": kelvin_to_celsius(main.get("feels_like")),
            "humidity": main.get("humidity"),
            "wind_speed": wind.get("speed"),
            "description": description,
        }

    @staticmethod
    def _build_brief_block(label: str, brief: dict[str, Any]) -> str:
        """Формирует компактный блок погоды для сравнения."""
        return (
            f"{label}\n"
            f"🏙 {brief.get('city', 'н/д')}\n"
            f"🌡 Температура: {format_temp(brief.get('temp_c'))}\n"
            f"🤗 Ощущается: {format_temp(brief.get('feels_like_c'))}\n"
            f"💧 Влажность: {brief.get('humidity', 'н/д')}%\n"
            f"💨 Ветер: {brief.get('wind_speed', 'н/д')} м/с\n"
            f"☁️ {brief.get('description', 'н/д')}"
        )

    def format_brief_block(self, label: str, brief: dict[str, Any]) -> str:
        """Публичный метод форматирования краткого блока погоды."""
        return self._build_brief_block(label, brief)

    @staticmethod
    def build_comparison_message(first: dict[str, Any], second: dict[str, Any]) -> str:
        """Формирует сообщение сравнения двух городов по параметрам."""
        def diff(a: Any, b: Any) -> float | None:
            try:
                return round(float(a) - float(b), 1)
            except (TypeError, ValueError):
                return None

        temp_diff = diff(first.get("temp_c"), second.get("temp_c"))
        feels_diff = diff(first.get("feels_like_c"), second.get("feels_like_c"))
        hum_diff = diff(first.get("humidity"), second.get("humidity"))
        wind_diff = diff(first.get("wind_speed"), second.get("wind_speed"))

        hotter = "одинаково"
        if temp_diff is not None:
            if temp_diff > 0:
                hotter = f"теплее в городе {first.get('city')}"
            elif temp_diff < 0:
                hotter = f"теплее в городе {second.get('city')}"

        return (
            "📊 Сравнение городов:\n"
            f"• Температура: разница {temp_diff if temp_diff is not None else 'н/д'}°C ({hotter})\n"
            f"• Ощущается: разница {feels_diff if feels_diff is not None else 'н/д'}°C\n"
            f"• Влажность: разница {hum_diff if hum_diff is not None else 'н/д'}%\n"
            f"• Ветер: разница {wind_diff if wind_diff is not None else 'н/д'} м/с"
        )

    def get_brief_weather(self, city: str) -> dict[str, Any]:
        """Возвращает краткую погоду по городу для сценария сравнения."""
        result = self.get_weather(city=city, extended=False)
        if not result["success"]:
            return result
        return {
            "success": True,
            "message": "",
            "data": self._extract_brief_weather(result["data"]),
        }

    def get_brief_weather_by_coordinates(self, lat: float, lon: float) -> dict[str, Any]:
        """Возвращает краткую погоду по координатам для сценария сравнения."""
        result = self.get_weather_by_coordinates(lat=lat, lon=lon, extended=False)
        if not result["success"]:
            return result
        return {
            "success": True,
            "message": "",
            "data": self._extract_brief_weather(result["data"]),
        }

    def get_weather(self, city: str, extended: bool = False) -> dict[str, Any]:
        """Возвращает погоду по названию города в формате для отправки пользователю."""
        city_name = city.strip()
        if not city_name:
            return {"success": False, "message": "❌ Пожалуйста, введите название города.", "data": {}}

        try:
            lat, lon = self._api._direct_geocode(city_name)
            raw_weather = self._api._current_weather(lat, lon)
            raw_weather["name"] = city_name

            extended_data: dict[str, Any] | None = None
            if extended:
                air_data = self._api._air_pollution(lat, lon)
                extended_data = self._api._format_extended_weather(raw_weather, air_data)

            message = self._build_weather_message(raw_weather, extended_data)
            return {"success": True, "message": message, "data": raw_weather}
        except CityNotFoundError:
            return {"success": False, "message": "❌ Город не найден. Проверьте название.", "data": {}}
        except APIConnectionError:
            return {
                "success": False,
                "message": "⚠️ Сервис погоды временно недоступен. Попробуйте позже.",
                "data": {},
            }
        except OpenWeatherAPIError:
            logger.exception("Непредвиденная ошибка погодного сервиса при запросе города.")
            return {
                "success": False,
                "message": "⚠️ Сервис погоды временно недоступен. Попробуйте позже.",
                "data": {},
            }

    def get_weather_by_coordinates(self, lat: float, lon: float, extended: bool = False) -> dict[str, Any]:
        """Возвращает погоду по координатам в формате для отправки пользователю."""
        try:
            raw_weather = self._api._current_weather(lat, lon)
            city_name = self._api._reverse_geocode(lat, lon)
            raw_weather["name"] = city_name

            extended_data: dict[str, Any] | None = None
            if extended:
                air_data = self._api._air_pollution(lat, lon)
                extended_data = self._api._format_extended_weather(raw_weather, air_data)

            message = self._build_weather_message(raw_weather, extended_data)
            return {"success": True, "message": message, "data": raw_weather}
        except CityNotFoundError:
            return {"success": False, "message": "❌ Не удалось определить погоду по координатам.", "data": {}}
        except APIConnectionError:
            return {
                "success": False,
                "message": "⚠️ Сервис погоды временно недоступен. Попробуйте позже.",
                "data": {},
            }
        except OpenWeatherAPIError:
            logger.exception("Непредвиденная ошибка погодного сервиса при запросе координат.")
            return {"success": False, "message": "❌ Не удалось определить погоду по координатам.", "data": {}}

    def get_forecast(self, city: str) -> dict[str, Any]:
        """Возвращает прогноз погоды по городу в удобном формате."""
        city_name = city.strip()
        if not city_name:
            return {"success": False, "message": "❌ Пожалуйста, введите название города.", "data": []}

        try:
            lat, lon = self._api._direct_geocode(city_name)
            forecast_data = self._api._forecast_weather(lat, lon)
            forecast_items = forecast_data.get("list") or []

            lines: list[str] = []
            compact_data: list[dict[str, Any]] = []
            for item in forecast_items[:5]:
                main = item.get("main") or {}
                weather = item.get("weather") or []
                description = "н/д"
                if isinstance(weather, list) and weather:
                    description = weather[0].get("description", "н/д")
                temp_c = kelvin_to_celsius(main.get("temp"))
                dt_txt = item.get("dt_txt", "н/д")
                lines.append(f"📅 {dt_txt}: {format_temp(temp_c)}, {description}")
                compact_data.append({"date_time": dt_txt, "temp_c": temp_c, "description": description})

            message = f"🗓️ Прогноз для города {city_name}:\n" + "\n".join(lines)
            return {"success": True, "message": message, "data": compact_data}
        except CityNotFoundError:
            return {"success": False, "message": "❌ Город не найден. Проверьте название.", "data": []}
        except APIConnectionError:
            return {
                "success": False,
                "message": "⚠️ Сервис погоды временно недоступен. Попробуйте позже.",
                "data": [],
            }
        except OpenWeatherAPIError:
            logger.exception("Непредвиденная ошибка погодного сервиса при прогнозе.")
            return {
                "success": False,
                "message": "⚠️ Сервис погоды временно недоступен. Попробуйте позже.",
                "data": [],
            }
