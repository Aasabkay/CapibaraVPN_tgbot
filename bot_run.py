"""Основной файл. Отвечает за запуск бота"""

import asyncio
from aiogram import Bot, Dispatcher
from redis.asyncio import Redis
from aiogram.fsm.storage.redis import RedisStorage

from config import TOKEN
from app.handlers.admin import admin_router
from app.handlers.user import user_router
from app.database.database import db_init

redis = Redis(host="localhost", port=6379, decode_responses=True)
storage = RedisStorage(redis)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=storage)

# Старт бота
async def main():
    dp.include_routers(admin_router, user_router)
    await db_init()
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass