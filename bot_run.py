"""Основной файл. Отвечает за запуск бота"""

# Импорт основных библиотек
import asyncio
from aiogram import Bot, Dispatcher
from redis.asyncio import Redis
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

# Импорт зависимостей
from config import TOKEN, REDIS_HOST, REDIS_PORT, PANEL_HOST, PANEL_LOGIN, PANEL_PASSWORD
from app.database.database import db_init
from app.services.vpn_api_client import ApiBotClient
from app.handlers.admin import admin_router
from app.handlers.user import user_router

# Инициализируем Redis для хранения состояний(FSM) в ней, а не в оперативной памяти
redis = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
storage = RedisStorage(redis)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN,
          default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)  # Место хранения состояний назначаем на Redis

# Запуск бока
async def main():
    dp.include_routers(admin_router, user_router)
    bot_api_client = ApiBotClient(host=PANEL_HOST, username=PANEL_LOGIN, password=PANEL_PASSWORD)

    await bot_api_client.login()
    await db_init()

    try:
        await dp.start_polling(bot, bot_api_client=bot_api_client)
    finally:
        await bot_api_client.close_connection()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass