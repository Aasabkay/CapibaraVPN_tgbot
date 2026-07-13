"""Файл, отвечающий за панель АДМИНА"""

import asyncio
from aiogram import F, Router
from aiogram.exceptions import TelegramForbiddenError, TelegramAPIError
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID, PANEL_HOST, PANEL_LOGIN, PANEL_PASSWORD
from app.keyboards.inline import admin_inline
from app.state import AdminBroadcast, AddKeyToUser
from app.database.database import add_user, add_key, delete_user_keys, get_all_users
from app.services.vpn_api import ApiBotClient

# Инициализация роутера админа
admin_router = Router()
admin_router.message.filter(F.from_user.id == ADMIN_ID) # Проверка USER_ID

@admin_router.message(CommandStart())
async def admin_start(message: Message):
    await message.answer(f'Добро пожаловать, {message.from_user.first_name}.', reply_markup=admin_inline)
    await add_user(message.from_user.id, message.from_user.username)

# Функция меню для админа
@admin_router.message(Command("menu"))
async def menu(message: Message):
    await message.answer('Главное меню:', reply_markup=admin_inline)

# Функция обработки кнопки для общей рассылки
@admin_router.callback_query(F.data == 'msg')
async def send_message(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Вы выбрали общую рассылку сообщения.')
    await callback.message.answer('Введите сообщение, которое вы хотите отправить:')
    await state.set_state(AdminBroadcast.waiting_for_content)

@admin_router.message(AdminBroadcast.waiting_for_content)
async def broadcast(message: Message, state: FSMContext):

    success_count = 0
    error_count = 0

    users_id = await get_all_users()

    for user_id in users_id:
        try:
            await message.send_copy(chat_id=user_id)
            success_count += 1

            await asyncio.sleep(0.05)

        except (TelegramForbiddenError, TelegramAPIError):
            error_count += 1

    await message.answer(f'Из {len(users_id)} удалось разослать {success_count} сообщений. Всего {error_count} ошибок.',
                         reply_markup=admin_inline)
    await state.clear()

# Функция для вывода всех пользователей в чат
@admin_router.callback_query(F.data == 'all_users_list')
async def show_all_users(callback: CallbackQuery):
    await callback.answer('Вы выбрали показать всех пользователей.')
    await callback.message.answer('Вывожу всех пользователей...')

    users_id = await get_all_users()

    try:
        for num, user in enumerate(users_id, start=1):
            user_chat = await callback.bot.get_chat(chat_id=user)

            await callback.message.answer(f'**Пользователь №{num}:**\n'
                                            f'ID: {user_chat.id}\n'
                                            f'Username: {user_chat.username}', parse_mode='Markdown')
        await callback.message.answer('**Успешно**, что делаем дальше?', reply_markup=admin_inline,
                                      parse_mode='Markdown')
    except Exception as e:
        await callback.message.answer('Произошла ошибка, повторите попытку позже.', reply_markup=admin_inline)

# Функция добавления ключей для пользователя
@admin_router.callback_query(F.data == 'add_keys')
async def keys(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Вы выбрали добавить ключ(-и) пользователю.')
    await callback.message.answer('Введите ID пользователя:')
    await state.set_state(AddKeyToUser.id)

@admin_router.message(AddKeyToUser.id)
async def set_id(message: Message, state: FSMContext):
    await state.update_data(id=message.text)
    await state.set_state(AddKeyToUser.keys_num)
    await message.answer('Введите сколько ключей вы хотите добавить')

@admin_router.message(AddKeyToUser.keys_num)
async def set_key_num(message: Message, state: FSMContext):
    await state.update_data(keys_num=message.text)
    await state.set_state(AddKeyToUser.key)
    await message.answer('Введите ключи, отдельным сообщением каждый')

@admin_router.message(AddKeyToUser.key)
async def get_keys(message: Message, state: FSMContext):
    user_data = await state.get_data()

    target_keys_count = int(user_data['keys_num'])

    uploaded_keys = user_data.get('keys', [])

    current_key = message.text.strip()
    uploaded_keys.append(current_key)

    await state.update_data(keys=uploaded_keys)

    current_keys_num = len(uploaded_keys)

    if current_keys_num < target_keys_count:
        await message.answer(f'Успешно принят {current_keys_num} ключ.\n'
                             f'**Осталось еще {target_keys_count-current_keys_num}**.')
        return
    else:
        for key in uploaded_keys:
            data = await state.get_data()
            user_id = int(data['id'])
            await add_key(user_id, key)
        await message.answer('Успешно приняты все ключи! Что дальше?', reply_markup=admin_inline)
        await state.clear()

# Функция обновления ключей для пользователей
@admin_router.callback_query(F.data == 'keys_update')
async def users_keys_update(callback: CallbackQuery):
    await callback.answer('Вы выбрали обновить ключи пользователей.')

    bot_api = ApiBotClient(host=PANEL_HOST, username=PANEL_LOGIN, password=PANEL_PASSWORD)

    try:
        if not await bot_api.login():
            await callback.message.answer('Не удалось подключиться к панели. Смотри логи')
            return
        new_keys = await bot_api.get_client_keys()

    finally:
        await bot_api.close_connection()

    for user_id, keys in new_keys.items():
        await delete_user_keys(user_id)

        for num, key in enumerate(keys, start=1):
            await add_key(user_id, key)

            try:
                await callback.bot.send_message(
                    chat_id=user_id,
                    text=f'<b>Ключ №{num}:</b>\n<code>{key}</code>',
                    parse_mode='HTML'
                )

                await asyncio.sleep(0.05)
            except Exception as e:
                print(f'Ошибка отправки сообщения пользователю {user_id}: {e}')

    await callback.message.answer(
        text='Вы отправили все известные ключи. Что-нибудь ещё?',
        reply_markup=admin_inline
    )


