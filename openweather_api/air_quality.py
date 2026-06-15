"""Логика анализа качества воздуха OpenWeatherMap."""

from __future__ import annotations

import logging
from typing import Any

from .exceptions import APIConnectionError


logger = logging.getLogger(__name__)


def analyze_air_quality(air_data: dict[str, Any]) -> dict[str, Any]:
    """Анализирует показатели загрязнения и возвращает итоговую оценку."""
    entries = air_data.get("list") or []
    if not isinstance(entries, list) or not entries:
        logger.error("В ответе качества воздуха отсутствует список list.")
        raise APIConnectionError("Не удалось проанализировать качество воздуха.")

    first_entry = entries[0]
    if not isinstance(first_entry, dict):
        logger.error("Элемент list в данных воздуха имеет некорректный формат.")
        raise APIConnectionError("Не удалось проанализировать качество воздуха.")

    components = first_entry.get("components") or {}
    if not isinstance(components, dict):
        logger.error("Поле components отсутствует или имеет некорректный формат.")
        raise APIConnectionError("Не удалось проанализировать качество воздуха.")

    thresholds: dict[str, tuple[float, float, float, float]] = {
        "so2": (20, 80, 250, 350),
        "no2": (40, 70, 150, 200),
        "pm10": (20, 50, 100, 200),
        "pm2_5": (10, 25, 50, 75),
        "o3": (60, 100, 140, 180),
        "co": (4400, 9400, 12400, 15400),
    }

    display_names: dict[str, str] = {
        "so2": "SO2",
        "no2": "NO2",
        "pm10": "PM10",
        "pm2_5": "PM2.5",
        "o3": "O3",
        "co": "CO",
    }

    def pollutant_level(value: float, bounds: tuple[float, float, float, float]) -> int:
        """Возвращает уровень загрязнения (1-5) для одного показателя."""
        if value < bounds[0]:
            return 1
        if value < bounds[1]:
            return 2
        if value < bounds[2]:
            return 3
        if value < bounds[3]:
            return 4
        return 5

    worst_level = 1
    exceeded: list[str] = []
    for key, bounds in thresholds.items():
        raw_value = components.get(key)
        if raw_value is None:
            continue

        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            logger.warning("Пропущено значение загрязнителя %s из-за некорректного формата.", key)
            continue

        level = pollutant_level(value, bounds)
        worst_level = max(worst_level, level)
        if level > 1:
            exceeded.append(display_names[key])

    label_map = {
        1: "Отлично",
        2: "Удовлетворительно",
        3: "Умеренно",
        4: "Плохо",
        5: "Опасно",
    }

    if worst_level == 1:
        summary = "Качество воздуха отличное. Все загрязнители в норме."
    elif worst_level == 2:
        summary = "Качество воздуха удовлетворительное. Есть незначительные превышения."
    elif worst_level == 3:
        if exceeded:
            pollutants = " и ".join(exceeded)
            summary = f"Качество воздуха умеренное. {pollutants} превышают норму."
        else:
            summary = "Качество воздуха умеренное. Зафиксированы превышения загрязнителей."
    elif worst_level == 4:
        summary = "Качество воздуха плохое. Чувствительным группам стоит снизить активность на улице."
    else:
        summary = "Качество воздуха опасное. Высокий риск для здоровья."

    return {
        "aqi_index": worst_level,
        "aqi_label": label_map[worst_level],
        "pollutant_details": exceeded,
        "human_summary": summary,
    }
