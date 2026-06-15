"""Хранение пользовательских настроек бота в памяти."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class UserSettings:
    """Настройки пользователя для погодного бота."""

    city: str | None = None
    extended: bool = False


class UserStorage:
    """Хранилище данных пользователя в памяти процесса."""

    def __init__(self) -> None:
        """Инициализирует внутренний словарь настроек."""
        self._storage: dict[int, UserSettings] = {}

    def _ensure_user(self, user_id: int) -> UserSettings:
        """Возвращает настройки пользователя, создавая запись при необходимости."""
        if user_id not in self._storage:
            self._storage[user_id] = UserSettings()
        return self._storage[user_id]

    def set_city(self, user_id: int, city: str) -> None:
        """Сохраняет последний выбранный город пользователя."""
        settings = self._ensure_user(user_id)
        settings.city = city

    def get_city(self, user_id: int) -> str | None:
        """Возвращает последний сохраненный город пользователя."""
        settings = self._ensure_user(user_id)
        return settings.city

    def set_extended(self, user_id: int, flag: bool) -> None:
        """Сохраняет признак расширенного режима пользователя."""
        settings = self._ensure_user(user_id)
        settings.extended = flag

    def get_extended(self, user_id: int) -> bool:
        """Возвращает признак расширенного режима пользователя."""
        settings = self._ensure_user(user_id)
        return settings.extended
