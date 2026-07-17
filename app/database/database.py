"""Файл с функциями для связи бота и БД"""

# Импорт необходимых библиотеки
import asyncpg
from typing import Optional
from collections import defaultdict
from asyncpg import Record
# Импорт необходимых зависимостей
from config import DB_NAME, DB_PASSWORD, DB_USER, DB_HOST, DB_PORT

# Инициализируем пул соединений с БД
pool: Optional[asyncpg.Pool] = None

# ==================================================================================================================
async def db_init() -> None:
# ==================================================================================================================
    """Инициализация базы данных"""
    global pool

    # Создаем пул соединений
    pool = await asyncpg.create_pool(
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        host=DB_HOST,
        port=DB_PORT
    )

    if pool is None:
        raise RuntimeError("Не удалось инициализировать пул базы данных.")

    async with pool.acquire() as conn:  # Берем из пула соединений одно свободное
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
        telegram_id BIGINT PRIMARY KEY,
        username VARCHAR(255),
        role TEXT
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

# ==================================================================================================================
async def set_user_role(telegram_id: int, role: str) -> None:
# ==================================================================================================================
    """Функция, устанавливающая роль пользователя"""

    # Проверка на случай ошибки инициализации пула
    if pool is None:
        print("Ошибка: Пул базы данных не инициализирован!")
        return

    async with pool.acquire() as conn:
        await conn.execute('''
        UPDATE users SET role =  $1 WHERE telegram_id = $2;
        ''', role, telegram_id)

# ==================================================================================================================
async def get_user_role(telegram_id: int) -> str:
# ==================================================================================================================
    """Функция, получающая с БД роль пользователя"""

    if pool is None:
        print("Ошибка: Пул базы данных не инициализирован!")
        return 'stranger'

    async with pool.acquire() as conn:
        user_row = await conn.fetchrow('''
        SELECT role FROM users WHERE telegram_id = $1;
        ''', telegram_id)

        if user_row is None:
            return 'stranger'

        return user_row['role']

# ==================================================================================================================
async def add_user(telegram_id: int, username: Optional[str], role: str) -> None:
# ==================================================================================================================
    """Функция добавления пользователя в БД в таблицу users"""

    if pool is None:
        print("Ошибка: Пул базы данных не инициализирован!")
        return

    async with pool.acquire() as conn:
        await conn.execute('''
        INSERT INTO users (telegram_id, username, role) VALUES ($1, $2, $3)
        ON CONFLICT (telegram_id) DO NOTHING;
        ''', telegram_id, username, role)

        print(f'Пользователь @{username} с ID: {telegram_id} был успешно добавлен.')

# ==================================================================================================================
async def add_key(user_id: int, key: str) -> None:
# ==================================================================================================================
    """Функция добавления ключа конкретному пользователю"""

    if pool is None:
        print("Ошибка: Пул базы данных не инициализирован!")
        return

    async with pool.acquire() as conn:
        await conn.execute('''
        INSERT INTO vpn_keys (user_id, key_value) VALUES ($1, $2);
        ''', user_id, key)

        print(f'Для пользователя {user_id} был добавлен ключ {key}')

# ==================================================================================================================
async def get_user_keys(user_id: int) -> list[str]:
# ==================================================================================================================
    """Функция, которая получается все ключи конкретного пользователя"""

    if pool is None:
        print("Ошибка: Пул базы данных не инициализирован!")
        return []

    async with pool.acquire() as conn:
        rows = await conn.fetch('''SELECT * FROM vpn_keys WHERE (user_id = $1);''', user_id)

        keys = [row['key_value'] for row in rows]

        print(f'Ключи для пользователя {user_id} были выданы.')
    return keys

# ==================================================================================================================
async def delete_user_keys(user_id: int) -> None:
# ==================================================================================================================
    """Функция удаления всех ключей у пользователя"""

    if pool is None:
        print("Ошибка: Пул базы данных не инициализирован!")
        return

    async with pool.acquire() as conn:
        await conn.execute('''
        DELETE FROM vpn_keys WHERE user_id = $1;
        ''', user_id)

        print(f'Все ключи для пользователя {user_id} были удалены')

# ==================================================================================================================
async def get_users_key_data() -> dict[int, list[str]]:
# ==================================================================================================================
    """Функция получения всех ключей всех пользователей"""

    if pool is None:
        print("Ошибка: Пул базы данных не инициализирован!")
        return {}

    async with pool.acquire() as conn:
        rows = await conn.fetch('''SELECT * FROM vpn_keys;''')

        grouped_data = defaultdict(list)  # Создаем словарь

        # Идем по строкам из БД и распределяем их по владельцам
        for row in rows:
            grouped_data[row['user_id']].append(row['key_value'])

        print(f'Ключи для пользователей были выданы.')
        return dict(grouped_data)

async def get_user_data(telegram_id: int) -> Optional[Record]:

    if pool is None:
        print("Ошибка: Пул базы данных не инициализирован!")
        return None

    async with pool.acquire() as conn:
        user_data = await conn.fetchrow('''SELECT * FROM users WHERE telegram_id = $1''', telegram_id)

        print('Данные о пользователе были получены')

        return user_data

# ==================================================================================================================
async def get_all_users_data() -> list[Record]:
# ==================================================================================================================
    """Функция, которая получает всех пользователей из таблицы users"""

    if pool is None:
        print("Ошибка: Пул базы данных не инициализирован!")
        return []

    async with pool.acquire() as conn:
        users_table = await conn.fetch('''SELECT * FROM users;''')

        print('Все пользователи были выведены.')
        return users_table

