# Telegram Yougile Bot

Бот для создания заявок в таск-трекере Yougile.

## Переменные окружения (.env)

- `TELEGRAM_TOKEN` — токен бота Telegram
- `YOUGILE_API_TOKEN` — токен API Yougile
- `COLUMN_ID` — ID колонки Yougile
- `ASSIGNED_USER_ID` — ID назначенного исполнителя
- `NOTIFY_CHANNEL_ID` — ID канала для уведомлений

## Запуск на Render

1. Загрузите репозиторий на GitHub
2. Перейдите на https://render.com
3. Нажмите "New Web Service"
4. Подключите GitHub и выберите репозиторий
5. Настройки:
   - Runtime: Python
   - Start Command: `python main.py`
   - Environment: Add Environment Variables вручную (или используйте `.env`)
6. Нажмите Deploy

Готово!
