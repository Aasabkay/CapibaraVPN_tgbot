import asyncpg
from typing import Optional
from collections import defaultdict

from config import DB_NAME, DB_PASSWORD, DB_USER

pool: Optional[asyncpg.Pool] = None

async def db_init():
    global pool

    pool = await asyncpg.create_pool(
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        host='localhost',
        port=5433
    )

    if pool is None:
        raise RuntimeError("Не удалось инициализировать пул базы данных.")

    async with pool.acquire() as conn:
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
        telegram_id BIGINT PRIMARY KEY,
        username VARCHAR(255)
        );
        ''')
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS vpn_keys (
        id SERIAL PRIMARY KEY,
        user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
        key_value TEXT NOT NULL
        );
        ''')

    print('База данных инициализирована.')

async def add_user(telegram_id: int, username: Optional[str]):
    if pool is None:
        print("Ошибка: Пул базы данных не инициализирован!")
        return

    async with pool.acquire() as conn:
        await conn.execute('''
        INSERT INTO users (telegram_id, username) VALUES ($1, $2)
        ON CONFLICT (telegram_id) DO NOTHING;
        ''', telegram_id, username)
    print(f'Пользователь @{username} с ID: {telegram_id} был успешно добавлен.')

async def add_key(user_id: int, key: str):
    if pool is None:
        print("Ошибка: Пул базы данных не инициализирован!")
        return

    async with pool.acquire() as conn:
        await conn.execute('''
        INSERT INTO vpn_keys (user_id, key_value) VALUES ($1, $2);
        ''', user_id, key)

    print(f'Для пользователя {user_id} был добавлен ключ {key}')

async def get_user_keys(user_id: int):
    if pool is None:
        print("Ошибка: Пул базы данных не инициализирован!")
        return []

    async with pool.acquire() as conn:
        rows = await conn.fetch('''SELECT * FROM vpn_keys WHERE (user_id = $1);''', user_id)

        keys = [row['key_value'] for row in rows]

    return keys

async def delete_user_keys(user_id: int):
    if pool is None:
        print("Ошибка: Пул базы данных не инициализирован!")
        return

    async with pool.acquire() as conn:
        await conn.execute('''
        DELETE FROM vpn_keys WHERE user_id = $1;
        ''', user_id)

async def get_users_key_data():
    if pool is None:
        print("Ошибка: Пул базы данных не инициализирован!")
        return {}

    async with pool.acquire() as conn:
        rows = await conn.fetch('''SELECT * FROM vpn_keys;''')

        grouped_data = defaultdict(list)

        for row in rows:
            grouped_data[row['user_id']].append(row['key_value'])

        return dict(grouped_data)

async def get_all_users():
    if pool is None:
        print("Ошибка: Пул базы данных не инициализирован!")
        return []

    async with pool.acquire() as conn:
        rows = await conn.fetch('''SELECT telegram_id FROM users;''')

        users = [row['telegram_id'] for row in rows]

        return users

