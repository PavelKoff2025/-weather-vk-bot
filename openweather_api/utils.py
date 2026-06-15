"""Утилиты форматирования погодных данных OpenWeatherMap."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from .air_quality import analyze_air_quality
from .exceptions import APIConnectionError


logger = logging.getLogger(__name__)

WEATHER_MAIN_TRANSLATIONS: dict[str, str] = {
    "Thunderstorm": "Гроза",
    "Drizzle": "Морось",
    "Rain": "Дождь",
    "Snow": "Снег",
    "Mist": "Туман",
    "Smoke": "Дымка",
    "Haze": "Мгла",
    "Dust": "Пыль",
    "Fog": "Туман",
    "Sand": "Песок",
    "Ash": "Пепел",
    "Squall": "Шквал",
    "Tornado": "Торнадо",
    "Clear": "Ясно",
    "Clouds": "Облачно",
}


def _kelvin_to_celsius(value: Any) -> float | None:
    """Конвертирует температуру из Кельвинов в градусы Цельсия."""
    if value is None:
        return None
    try:
        return round(float(value) - 273.15, 2)
    except (TypeError, ValueError):
        logger.warning("Не удалось конвертировать температуру в градусы Цельсия: %s", value)
        return None


def _format_unix_time(value: Any, timezone_shift_seconds: Any = 0) -> str | None:
    """Форматирует Unix timestamp в человекочитаемое локальное время."""
    if value is None:
        return None

    try:
        timestamp = int(value)
        shift = int(timezone_shift_seconds or 0)
    except (TypeError, ValueError):
        logger.warning("Не удалось преобразовать timestamp времени: %s", value)
        return None

    dt_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    dt_local = dt_utc.timestamp() + shift
    formatted = datetime.fromtimestamp(dt_local, tz=timezone.utc).strftime("%H:%M:%S")
    return formatted


def format_basic_weather(weather_data: dict[str, Any]) -> dict[str, Any]:
    """Формирует базовый словарь с погодными параметрами."""
    weather_list = weather_data.get("weather") or []
    weather_item = weather_list[0] if isinstance(weather_list, list) and weather_list else {}
    main_data = weather_data.get("main") or {}
    condition = weather_item.get("main")
    condition_ru = WEATHER_MAIN_TRANSLATIONS.get(str(condition), condition)

    return {
        "city": weather_data.get("name"),
        "condition": condition_ru,
        "description": weather_item.get("description"),
        "temp_c": _kelvin_to_celsius(main_data.get("temp")),
        "feels_like_c": _kelvin_to_celsius(main_data.get("feels_like")),
        "temp_min_c": _kelvin_to_celsius(main_data.get("temp_min")),
        "temp_max_c": _kelvin_to_celsius(main_data.get("temp_max")),
    }


def format_extended_weather(weather_data: dict[str, Any], air_data: dict[str, Any]) -> dict[str, Any]:
    """Формирует расширенный словарь погоды с данными по воздуху."""
    result = format_basic_weather(weather_data)
    main_data = weather_data.get("main") or {}
    sys_data = weather_data.get("sys") or {}
    timezone_shift = weather_data.get("timezone", 0)

    if "visibility" in weather_data:
        result["visibility"] = weather_data.get("visibility")
    if "pressure" in main_data:
        result["pressure"] = main_data.get("pressure")
    if "sea_level" in main_data:
        result["sea_level"] = main_data.get("sea_level")
    if "grnd_level" in main_data:
        result["ground_level"] = main_data.get("grnd_level")
    if "sunrise" in sys_data:
        result["sunrise"] = _format_unix_time(sys_data.get("sunrise"), timezone_shift)
    if "sunset" in sys_data:
        result["sunset"] = _format_unix_time(sys_data.get("sunset"), timezone_shift)

    result["air_quality"] = analyze_air_quality(air_data)
    return result


def format_forecast_data(forecast_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Преобразует ответ прогноза в компактный список значений."""
    entries = forecast_data.get("list") or []
    if not isinstance(entries, list):
        logger.error("Поле list в прогнозе имеет некорректный формат.")
        raise APIConnectionError("Получен некорректный формат данных прогноза.")

    formatted: list[dict[str, Any]] = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        main_data = item.get("main") or {}
        formatted.append(
            {
                "date_time": item.get("dt_txt"),
                "temp_c": _kelvin_to_celsius(main_data.get("temp")),
                "humidity": main_data.get("humidity"),
                "pressure": main_data.get("pressure"),
            }
        )
    return formatted
