"""Обработчики текущей погоды, выбора города и расширенного режима."""

from __future__ import annotations

import logging

from vkbottle.bot import Message

from weather_vk_bot.bot import bot, user_storage, weather_service
from weather_vk_bot.handlers import WeatherStates
from weather_vk_bot.handlers.menu import (
    BTN_CHANGE_CITY,
    BTN_COMPARE,
    BTN_EXTENDED,
    BTN_FORECAST,
    BTN_GEO,
    BTN_HELP,
    BTN_MY_CITY,
    BTN_WEATHER_NOW,
    get_city_keyboard,
    get_main_keyboard,
)


logger = logging.getLogger(__name__)

HELP_TEXT = (
    "🤖 *Погодный бот*\n"
    "🌤 *Погода сейчас* — погода в выбранном городе\n"
    "📅 *Прогноз 5 дней* — прогноз для выбранного города\n"
    "🏙 *Мой город* — посмотреть текущий выбранный город\n"
    "✏️ *Изменить город* — выбрать новый город\n"
    "📍 *Геолокация* — определить город автоматически\n"
    "📊 *Расширенный режим* — детальная информация о воздухе и рассвете/закате\n\n"
    "⚖️ *Сравнить города* — сравнение двух городов по погодным параметрам\n\n"
    "📍 Чтобы отправить геолокацию, нажмите на скрепку → Геолокация"
)


async def _safe_delete_state(peer_id: int) -> None:
    """Безопасно удаляет состояние пользователя, если оно существует."""
    try:
        await bot.state_dispenser.delete(peer_id)
    except KeyError:
        return


async def _send_weather_for_selected_city(message: Message) -> None:
    """Отправляет текущую погоду для выбранного города пользователя."""
    city = user_storage.get_city(message.from_id)
    if not city:
        await message.answer(
            "🏙 У вас пока не выбран город.\nНажмите «🏙 Мой город» → «✏️ Изменить город».",
            keyboard=get_main_keyboard(),
        )
        return

    extended = user_storage.get_extended(message.from_id)
    result = weather_service.get_weather(city=city, extended=extended)
    await message.answer(result["message"])
    await message.answer("🔘 Выберите следующее действие:", keyboard=get_main_keyboard())


async def _send_forecast_for_selected_city(message: Message) -> None:
    """Отправляет прогноз для выбранного города пользователя."""
    city = user_storage.get_city(message.from_id)
    if not city:
        await message.answer(
            "🏙 Сначала выберите ваш город через «🏙 Мой город» → «✏️ Изменить город».",
            keyboard=get_main_keyboard(),
        )
        return

    result = weather_service.get_forecast(city=city)
    await message.answer(result["message"])
    await message.answer("🔘 Выберите следующее действие:", keyboard=get_main_keyboard())


@bot.on.message(text=BTN_WEATHER_NOW)
async def weather_now_handler(message: Message) -> None:
    """Обрабатывает кнопку текущей погоды для выбранного города."""
    await _safe_delete_state(message.peer_id)
    await _send_weather_for_selected_city(message)


@bot.on.message(text=BTN_FORECAST)
async def forecast_for_selected_city_handler(message: Message) -> None:
    """Обрабатывает кнопку прогноза для выбранного города."""
    await _safe_delete_state(message.peer_id)
    await _send_forecast_for_selected_city(message)


@bot.on.message(text=BTN_MY_CITY)
async def my_city_handler(message: Message) -> None:
    """Показывает текущий выбранный город пользователя."""
    await _safe_delete_state(message.peer_id)
    city = user_storage.get_city(message.from_id)
    if city:
        await message.answer(
            f"🏙 Ваш текущий город: {city}\n"
            "Если хотите изменить город, нажмите «✏️ Изменить город».",
            keyboard=get_city_keyboard(),
        )
    else:
        await message.answer(
            "🏙 Город пока не выбран.\nНажмите «✏️ Изменить город», чтобы указать его.",
            keyboard=get_city_keyboard(),
        )


@bot.on.message(text=BTN_CHANGE_CITY)
async def change_city_handler(message: Message) -> None:
    """Переводит пользователя в состояние ожидания нового города."""
    await bot.state_dispenser.set(message.peer_id, WeatherStates.AWAITING_CITY_WEATHER)
    await message.answer("🏙 Введите ваш город:", keyboard=get_city_keyboard())


@bot.on.message(text=BTN_EXTENDED)
async def toggle_extended_mode(message: Message) -> None:
    """Переключает расширенный режим и применяет его к выбранному городу."""
    await _safe_delete_state(message.peer_id)
    current_flag = user_storage.get_extended(message.from_id)
    new_flag = not current_flag
    user_storage.set_extended(message.from_id, new_flag)

    if new_flag:
        await message.answer(
            "✅ Расширенный режим включён.\n"
            "Прогноз и погода будут показываться для выбранного города с доп. данными.",
            keyboard=get_main_keyboard(),
        )
    else:
        await message.answer(
            "ℹ️ Расширенный режим выключен.\n"
            "Прогноз и погода будут показываться в базовом формате.",
            keyboard=get_main_keyboard(),
        )

    if user_storage.get_city(message.from_id):
        await _send_weather_for_selected_city(message)


@bot.on.message(text=BTN_HELP)
async def help_from_weather_handler(message: Message) -> None:
    """Отправляет справку из любого сценария."""
    await _safe_delete_state(message.peer_id)
    await message.answer(HELP_TEXT, keyboard=get_main_keyboard())


@bot.on.message(text=BTN_COMPARE)
async def compare_start_handler(message: Message) -> None:
    """Запускает сценарий сравнения двух городов."""
    await bot.state_dispenser.set(message.peer_id, WeatherStates.AWAITING_COMPARE_FIRST)
    await message.answer(
        "⚖️ Сравнение городов.\n"
        "Введите название первого города или отправьте первую геолокацию.",
        keyboard=get_main_keyboard(),
    )


@bot.on.message(state=WeatherStates.AWAITING_CITY_WEATHER)
async def save_city_handler(message: Message) -> None:
    """Сохраняет новый город пользователя и показывает погоду по нему."""
    city = (message.text or "").strip()
    if not city:
        await message.answer("❌ Пожалуйста, введите название города.")
        return

    if city in {
        BTN_WEATHER_NOW,
        BTN_FORECAST,
        BTN_GEO,
        BTN_EXTENDED,
        BTN_MY_CITY,
        BTN_HELP,
        BTN_COMPARE,
        "Главное меню",
        "Назад",
    }:
        await _safe_delete_state(message.peer_id)
        if city == BTN_WEATHER_NOW:
            await _send_weather_for_selected_city(message)
        elif city == BTN_FORECAST:
            await _send_forecast_for_selected_city(message)
        elif city == BTN_GEO:
            await message.answer("📍 Отправьте вашу геолокацию через кнопку прикрепления в VK.", keyboard=get_main_keyboard())
        elif city == BTN_EXTENDED:
            await toggle_extended_mode(message)
        elif city == BTN_MY_CITY:
            await my_city_handler(message)
        elif city == BTN_HELP:
            await help_from_weather_handler(message)
        elif city == BTN_COMPARE:
            await compare_start_handler(message)
        else:
            await message.answer(
                "Добро пожаловать в VK Weather Bot.\n\nВыберите действие через кнопки ниже.",
                keyboard=get_main_keyboard(),
            )
        return

    result = weather_service.get_weather(city=city, extended=False)
    if not result["success"]:
        await message.answer(result["message"])
        return

    user_storage.set_city(message.from_id, city)
    await _safe_delete_state(message.peer_id)
    await message.answer(f"✅ Ваш город сохранён: {city}")
    await _send_weather_for_selected_city(message)


@bot.on.message(state=WeatherStates.AWAITING_COMPARE_FIRST)
async def compare_first_city_handler(message: Message) -> None:
    """Сохраняет первый город для сравнения и просит второй."""
    city = (message.text or "").strip()
    if not city:
        await message.answer("❌ Введите название первого города или отправьте геолокацию.")
        return

    if city in {BTN_HELP, "Главное меню", "Назад"}:
        await _safe_delete_state(message.peer_id)
        if city == BTN_HELP:
            await help_from_weather_handler(message)
        else:
            await message.answer(
                "Добро пожаловать в VK Weather Bot.\n\nВыберите действие через кнопки ниже.",
                keyboard=get_main_keyboard(),
            )
        return

    first_result = weather_service.get_brief_weather(city)
    if not first_result["success"]:
        await message.answer(first_result["message"])
        return

    await bot.state_dispenser.set(
        message.peer_id,
        WeatherStates.AWAITING_COMPARE_SECOND,
        first_weather=first_result["data"],
    )
    await message.answer(
        "✅ Первый город принят.\nВведите второй город или отправьте вторую геолокацию.",
        keyboard=get_main_keyboard(),
    )


@bot.on.message(state=WeatherStates.AWAITING_COMPARE_SECOND)
async def compare_second_city_handler(message: Message) -> None:
    """Принимает второй город и отправляет итог сравнения."""
    city = (message.text or "").strip()
    if not city:
        await message.answer("❌ Введите название второго города или отправьте геолокацию.")
        return

    if city in {BTN_HELP, "Главное меню", "Назад"}:
        await _safe_delete_state(message.peer_id)
        if city == BTN_HELP:
            await help_from_weather_handler(message)
        else:
            await message.answer(
                "Добро пожаловать в VK Weather Bot.\n\nВыберите действие через кнопки ниже.",
                keyboard=get_main_keyboard(),
            )
        return

    state_peer = await bot.state_dispenser.get(message.peer_id)
    if state_peer is None or "first_weather" not in state_peer.payload:
        await bot.state_dispenser.set(message.peer_id, WeatherStates.AWAITING_COMPARE_FIRST)
        await message.answer("⚠️ Не найден первый город. Начните сравнение заново.", keyboard=get_main_keyboard())
        return

    second_result = weather_service.get_brief_weather(city)
    if not second_result["success"]:
        await message.answer(second_result["message"])
        return

    first = state_peer.payload["first_weather"]
    second = second_result["data"]
    await _safe_delete_state(message.peer_id)
    await message.answer(weather_service.format_brief_block("1️⃣ Первый город:", first))
    await message.answer(weather_service.format_brief_block("2️⃣ Второй город:", second))
    await message.answer(weather_service.build_comparison_message(first, second))
    await message.answer("🔘 Сравнение завершено. Выберите действие:", keyboard=get_main_keyboard())
