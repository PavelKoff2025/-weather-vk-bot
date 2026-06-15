# -weather-vk-bot

VK-бот для погоды на `vkbottle` с интеграцией OpenWeatherMap.

## Возможности

- Текущая погода для выбранного города
- Прогноз на 5 дней для выбранного города
- Смена города через сценарий `Мой город` -> `Изменить город`
- Геолокация пользователя
- Расширенный режим (дополнительные погодные метрики и воздух)
- Сравнение двух городов (по вводу городов или двум геолокациям подряд)

## Стек

- Python 3.13+
- vkbottle
- requests
- python-dotenv

## Установка

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Конфигурация

Создайте `.env` на основе `.env.example`:

```env
VK_TOKEN=ваш_токен_сообщества
OPENWEATHER_API_KEY=ваш_ключ_openweather
VK_DISABLE_SSL_VERIFY=0
```

`VK_DISABLE_SSL_VERIFY=1` используйте только для локальной отладки в средах с проблемным SSL.

## Запуск

```bash
python -m weather_vk_bot.main
```

или

```bash
./.venv/bin/python -m weather_vk_bot.main
```

## Структура

- `weather_vk_bot/main.py` — точка входа
- `weather_vk_bot/bot.py` — инициализация бота и сервисов
- `weather_vk_bot/handlers/` — обработчики меню, погоды, прогноза, гео и помощи
- `weather_vk_bot/services/` — бизнес-логика и форматирование
- `openweather_api/` — клиент OpenWeather API
