"""Файл, отвечающий за панель АДМИНА"""

# Импорт необходимых библиотек
import asyncio
from aiogram import F, Router
from aiogram.exceptions import TelegramForbiddenError, TelegramAPIError
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

# Импорт необходимых данных из конфига
from config import ADMIN_ID, PANEL_HOST, PANEL_LOGIN, PANEL_PASSWORD
# Импорт клавиатуры и состояний
from app.keyboards.inline import admin_inline
from app.state import AdminBroadcast, AddKeyToUser
# Импорт функций для работы с БД
from app.database.database import add_key, delete_user_keys, get_all_users
# Импорт API клиента
from app.services.vpn_api_client import ApiBotClient
# Инициализация роутера админа
admin_router = Router()
admin_router.message.filter(F.from_user.id == ADMIN_ID) # Проверка USER_ID, чтобы выдавать панель только админу

# ========== 1. СТАРТ И НАВИГАЦИЯ (/start и /menu) ==========
# ==================================================================================================================
@admin_router.message(CommandStart())
async def admin_start(message: Message) -> None:
# ==================================================================================================================
    """Текст приветствия админа при первом запуске бота."""

    await message.answer(
        f'👋 <b>Добро пожаловать</b>, {message.from_user.first_name}.',
        reply_markup=admin_inline
    )

# ==================================================================================================================
@admin_router.message(Command("menu"))
async def menu(message: Message) -> None:
# ==================================================================================================================
    """Главное меню админа по команде /menu (на случай бага бота, если меню не появится само)"""

    await message.answer(
        '📖 <b>Главное меню</b>:',
        reply_markup=admin_inline
    )

# ========== 2. ЛОГИКА ОБЩЕЙ РАССЫЛКИ ==========
# ==================================================================================================================
@admin_router.callback_query(F.data == 'msg')
async def start_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
# ==================================================================================================================
    """Инициализация общей рассылки для пользователей."""

    await callback.answer('Вы выбрали общую рассылку сообщения.')
    await callback.message.answer('💭 Введите сообщение, которое вы хотите отправить:')

    # Переход в состояние ожидания сообщения
    await state.set_state(AdminBroadcast.waiting_for_content)

# ==================================================================================================================
@admin_router.message(AdminBroadcast.waiting_for_content)
async def broadcast(message: Message, state: FSMContext) -> None:
# ==================================================================================================================
    """Логика рассылки сообщения админа пользователям."""

    success_count = 0
    error_count = 0

    # Получаем актуальный список пользователей
    users_id = await get_all_users()

    # Проверка на наличие пользователей в БД
    if not users_id:
        await message.answer(
            '🚫 В данный момент в базе данных нет пользователей! Рассылка невозможна.',
            reply_markup=admin_inline
        )
        await state.clear()
        return

    # Цикл отправки сообщения для каждого пользователя
    for user_id in users_id:
        try:
            await message.send_copy(chat_id=user_id)
            success_count += 1

            await asyncio.sleep(0.05)

        except (TelegramForbiddenError, TelegramAPIError) as e:
            print(f'🚫 Не удалось отправить сообщение пользователю {user_id}. Ошибка: {e}')
            error_count += 1

    results_text = (f'📊 <b>Результаты рассылки:</b>\n'
                    f'✅ Успешно отправлено сообщений: {success_count}\n'
                    f'🚫 Не удалось отправить: {error_count}\n'
                    f'🙍‍♂️ Всего пользователей в базе: {len(users_id)}')

    await message.answer(results_text,
                         reply_markup=admin_inline)

    # Сбрасываем состояние
    await state.clear()

# ========== 3. ВЫВОД ВСЕХ ПОЛЬЗОВАТЕЛЕЙ В ЧАТ С АДМИНОМ ==========
#===================================================================================================================
@admin_router.callback_query(F.data == 'all_users_list')
async def show_all_users(callback: CallbackQuery) -> None:
# ==================================================================================================================
    """Реализация вывода пользователей"""

    await callback.answer('Вы выбрали показать всех пользователей.')
    await callback.message.answer('📨 Вывожу всех пользователей...')

    # Получаем актуальный список пользователей
    users_id = await get_all_users()

    try:
        for num, user in enumerate(users_id, start=1):
            user_chat = await callback.bot.get_chat(chat_id=user)  # Информация о пользователе по его ID

            response_text = (f'🙍‍♂️<b>Пользователь №{num}:</b>\n'
                             f'📫<b>ID:</b> {user_chat.id}\n'
                             f'💭<b>Username:</b> {user_chat.username}')

            await callback.message.answer(response_text)
        await callback.message.answer('✅ <b>Успешно</b>, что делаем дальше?',
                                      reply_markup=admin_inline)
    except Exception as e:
        await callback.message.answer(
            f'🚫 Произошла ошибка при попытке вывести пользователей. Ошибка: {e}',
            reply_markup=admin_inline
        )

# ========== 4. БЛОК ДОБАВЛЕНИЯ КЛЮЧА(-ЕЙ) ДЛЯ ПОЛЬЗОВАТЕЛЯ ==========
# ==================================================================================================================
@admin_router.callback_query(F.data == 'add_keys')
async def get_user_id(callback: CallbackQuery, state: FSMContext) -> None:
# ==================================================================================================================
    """Функция отвечает за запрос ID пользователя, которому хоти добавить ключ"""

    await callback.answer('Вы выбрали добавить ключ(-и) пользователю.')
    await callback.message.answer('🙍‍♂️ Введите ID пользователя:')

    # Устанавливаем состояние ID
    await state.set_state(AddKeyToUser.id)

# ==================================================================================================================
@admin_router.message(AddKeyToUser.id)
async def get_keys_num(message: Message, state: FSMContext) -> None:
# ==================================================================================================================
    """Функция отвечает за запрос количества ключей и назначение ID пользователя"""

    await state.update_data(id=message.text)  # Запоминаем полученный ID пользователя из сообщения
    await state.set_state(AddKeyToUser.keys_num)  # Устанавливаем состояние ожидания количества ключей
    await message.answer('📫 Введите сколько ключей вы хотите добавить')

# ==================================================================================================================
@admin_router.message(AddKeyToUser.keys_num)
async def get_keys(message: Message, state: FSMContext) -> None:
# ==================================================================================================================
    """Функция отвечает за запрос ключей и назначение количества ключей"""

    await state.update_data(keys_num=message.text)  # Запоминаем количество ключей из сообщения
    await state.set_state(AddKeyToUser.key)  # Устанавливаем состояние ожидания ключей
    await message.answer('🔑 Введите ключи, отдельным сообщением каждый')

# ==================================================================================================================
@admin_router.message(AddKeyToUser.key)
async def add_keys(message: Message, state: FSMContext) -> None:
# ==================================================================================================================
    """Функция реализует логику записи ключей для пользователя в базу данных"""

    # Получаем все ранее запрошенные данные
    user_data = await state.get_data()

    target_keys_count = int(user_data['keys_num'])  # Количество ключей, введенное админом
    uploaded_keys = user_data.get('keys', [])  # Список со всеми ключами

    current_key = message.text.strip()  # Забираем ключ из сообщения
    uploaded_keys.append(current_key)  # Тут же его добавляем в список

    await state.update_data(keys=uploaded_keys)
    current_keys_num = len(uploaded_keys)

    # Цикл получения ключей от админа
    if current_keys_num < target_keys_count:
        await message.answer(f'✅ Успешно принят {current_keys_num} ключ.🔑\n'
                             f'📜 <b>Осталось еще {target_keys_count-current_keys_num}</b>.')
        return
    else:
        for key in uploaded_keys:
            data = await state.get_data()
            user_id = int(data['id'])
            await add_key(user_id, key)  # Функция, которая добавляет запись в БД
        await message.answer('✅ <b>Успешно приняты все ключи!</b> Что дальше?',
                             reply_markup=admin_inline)
        await state.clear()

# ========== 5. ОБНОВЛЕНИЕ КЛЮЧА(-ЕЙ) ДЛЯ ПОЛЬЗОВАТЕЛЯ ==========
# ==================================================================================================================
@admin_router.callback_query(F.data == 'keys_update')
async def users_keys_update(callback: CallbackQuery, bot_api_client: ApiBotClient) -> None:
# ==================================================================================================================
    """Функция обновления ключей для пользователя"""

    await callback.answer('Вы выбрали обновить ключи пользователей.')

    new_keys = await bot_api_client.get_client_keys()

    # Цикл обновления ключей
    for user_id, keys in new_keys.items():
        await delete_user_keys(user_id)  # Для конкретного пользователя полностью очищаем его ключи из БД

        for num, key in enumerate(keys, start=1):
            await add_key(user_id, key)  # Из списка НОВЫХ ключей берем ключ и ID пользователя, добавляем в БД
            try:
                await callback.bot.send_message(chat_id=user_id,
                                                text='<b>Появилось обновление ключей!</b> 📨')

                user_emails = await bot_api_client.get_user_email(user_id)

                header = "<b>Ваш ключ:</b>" if len(keys) == 1 else f"Ключ №{num}:"

                user_key_text = (
                    f'🔑 {header}\n'
                    f'📜 <b>Название ключа:</b> {user_emails[num - 1]}\n'
                    f'<code>{key}</code>'
                )

                await callback.bot.send_message(
                    chat_id=user_id,  # Отправляем ключ в чат пользователя
                    text=user_key_text,
                    disable_web_page_preview=True
                )

                await asyncio.sleep(0.05)
            except Exception as e:
                print(f'🚫 Ошибка отправки сообщения пользователю {user_id}: {e}')

    await callback.message.answer(
        text='Вы отправили все известные ключи. Что-нибудь ещё?',
        reply_markup=admin_inline
    )


