"""Точка входа для запуска VK погодного бота."""

from __future__ import annotations

import logging
import traceback

from vkbottle.tools import _runner

from weather_vk_bot.bot import bot
from weather_vk_bot.handlers import forecast, geo, help, menu, weather  # noqa: F401


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Патч совместимости: в ряде окружений logger в vkbottle не имеет метода opt.
if not hasattr(_runner.logger, "opt"):
    class _RunnerLoggerProxy:
        """Прокси-логгер для сохранения поведения logger.opt(exception=...)."""

        def __init__(self, logger_obj: logging.Logger, exception: BaseException | None = None) -> None:
            self._logger = logger_obj
            self._exception = exception

        def error(self, message: str) -> None:
            """Логирует ошибку и выводит traceback, если он передан."""
            self._logger.error(message)
            if self._exception is not None:
                traceback.print_exception(
                    type(self._exception),
                    self._exception,
                    self._exception.__traceback__,
                )

    def _opt_proxy(**kwargs: object) -> _RunnerLoggerProxy:
        """Эмулирует интерфейс logger.opt для vkbottle runner."""
        exc = kwargs.get("exception")
        return _RunnerLoggerProxy(_runner.logger, exc if isinstance(exc, BaseException) else None)

    _runner.logger.opt = _opt_proxy  # type: ignore[attr-defined]


if __name__ == "__main__":
    bot.run()
