"""Обработчик справки по командам бота."""

from __future__ import annotations

from vkbottle.bot import Message

from weather_vk_bot.bot import bot
from weather_vk_bot.handlers.menu import BTN_HELP, get_main_keyboard


@bot.on.message(text=BTN_HELP)
async def help_handler(message: Message) -> None:
    """Отправляет пользователю инструкцию по работе с ботом."""
    text = (
        "🤖 *Погодный бот*\n"
        "🌤 *Погода сейчас* — погода в выбранном городе\n"
        "📅 *Прогноз 5 дней* — прогноз для выбранного города\n"
        "🏙 *Мой город* — посмотреть текущий выбранный город\n"
        "✏️ *Изменить город* — выбрать новый город\n"
        "📍 *Геолокация* — определить город автоматически\n"
        "📊 *Расширенный режим* — детальный анализ качества воздуха, рассвет/закат\n"
        "ℹ️ *Помощь* — это сообщение\n\n"
        "📍 Чтобы отправить геолокацию, нажмите на скрепку → Геолокация"
    )
    await message.answer(text, keyboard=get_main_keyboard())
