"""CLI-интерфейс для работы с модулем OpenWeatherAPI."""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

from openweather_api import CityNotFoundError, OpenWeatherAPI, OpenWeatherAPIError


logger = logging.getLogger(__name__)


def _print_result(title: str, data: dict[str, Any]) -> None:
    """Выводит заголовок и JSON-результат в читаемом виде."""
    print(f"\n{title}")
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _read_yes_no(prompt: str) -> bool:
    """Запрашивает ответ да/нет и возвращает флаг расширенного режима."""
    while True:
        value = input(prompt).strip().lower()
        if value in {"д", "да", "y", "yes"}:
            return True
        if value in {"н", "нет", "n", "no", ""}:
            return False
        print("Введите 'да' или 'нет'.")


def _read_float(prompt: str) -> float:
    """Запрашивает число с плавающей точкой у пользователя."""
    while True:
        raw = input(prompt).strip().replace(",", ".")
        try:
            return float(raw)
        except ValueError:
            print("Некорректное число. Повторите ввод.")


def _print_menu() -> None:
    """Печатает главное меню CLI."""
    print("\n=== OpenWeatherAPI CLI ===")
    print("1. Текущая погода по городу")
    print("2. Прогноз на 5 дней по городу")
    print("3. Погода по координатам")
    print("0. Выход")


def main() -> int:
    """Точка входа CLI-приложения."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    print("Запуск тестового CLI для OpenWeather API.")
    print("API ключ берется из OPENWEATHER_API_KEY или передается в конструктор.")

    api: OpenWeatherAPI | None = None
    try:
        api = OpenWeatherAPI()

        while True:
            _print_menu()
            choice = input("Выберите пункт: ").strip()

            if choice == "0":
                print("Выход из программы.")
                return 0

            if choice == "1":
                city = input("Введите город: ").strip()
                extended = _read_yes_no("Расширенный режим? (да/нет): ")
                result = api.get_weather_by_city(city=city, extended=extended)
                _print_result(f"Текущая погода для города {city}:", result)
                continue

            if choice == "2":
                city = input("Введите город: ").strip()
                extended = _read_yes_no("Добавить анализ воздуха? (да/нет): ")
                result = api.get_forecast_by_city(city=city, extended=extended)
                _print_result(f"Прогноз на 5 дней для города {city}:", result)
                continue

            if choice == "3":
                lat = _read_float("Введите широту (lat): ")
                lon = _read_float("Введите долготу (lon): ")
                extended = _read_yes_no("Расширенный режим? (да/нет): ")
                result = api.get_weather_by_coordinates(lat=lat, lon=lon, extended=extended)
                _print_result("Погода по координатам:", result)
                continue

            print("Неизвестный пункт меню. Выберите 0, 1, 2 или 3.")

    except CityNotFoundError as exc:
        logger.error("Город не найден: %s", exc)
        return 2
    except OpenWeatherAPIError as exc:
        logger.error("Ошибка работы CLI OpenWeatherAPI: %s", exc)
        return 1
    finally:
        if api is not None:
            api.close()


if __name__ == "__main__":
    sys.exit(main())
