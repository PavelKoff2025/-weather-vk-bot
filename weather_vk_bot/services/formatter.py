"""Форматирование ответов погоды для сообщений VK."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def kelvin_to_celsius(value: Any) -> float | None:
    """Конвертирует температуру из Кельвинов в градусы Цельсия."""
    if value is None:
        return None
    try:
        return round(float(value) - 273.15, 1)
    except (TypeError, ValueError):
        return None


def format_temp(value: float | None) -> str:
    """Форматирует температуру для отображения в сообщении."""
    if value is None:
        return "н/д"
    sign = "+" if value > 0 else ""
    return f"{sign}{value}°C"


def format_unix_time(value: Any, tz_shift: Any = 0) -> str:
    """Преобразует unix-время в строку HH:MM."""
    try:
        timestamp = int(value)
        shift = int(tz_shift or 0)
        local_timestamp = timestamp + shift
        return datetime.fromtimestamp(local_timestamp, tz=timezone.utc).strftime("%H:%M")
    except (TypeError, ValueError, OSError):
        return "н/д"


def join_pollutants(pollutants: list[str]) -> str:
    """Формирует строку с перечнем загрязнителей."""
    if not pollutants:
        return "в норме"
    return ", ".join(pollutants)
