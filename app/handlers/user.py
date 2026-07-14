"""Файл, отвечающий за панель ПОЛЬЗОВАТЕЛЕЙ"""

# Импорт необходимых библиотек
from aiogram import F, Router
from aiogram.exceptions import TelegramForbiddenError, TelegramAPIError
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
# Импорт необходимых зависимостей
from app.keyboards.inline import user_inline
from app.state import UserError
from config import ADMIN_ID, PANEL_HOST, PANEL_LOGIN, PANEL_PASSWORD
from app.database.database import add_user, get_user_keys, get_all_users
from app.services.vpn_api_client import ApiBotClient

# Инициализация роутера пользователя
user_router = Router()

# ========== 1. СТАРТ И НАВИГАЦИЯ (/start и /menu) ==========
# ==================================================================================================================
@user_router.message(CommandStart())
async def user_start(message: Message):
# ==================================================================================================================
    """Текст приветствия пользователя при первом запуске бота"""

    # Получаем актуальные данные о всех пользователях
    users_id = await get_all_users()

    hello_text = (f'<b>Привет!</b>👋 <b>Я - CapibaraVPN, бот, созданный для удобства администрирования VPN ключей'
                  f' между пользователями!</b>\n'
                  f'Ниже есть кнопки: "Получить ключ" и "Отправить ошибку".\n'
                  f'Думаю, объяснять зачем они, не нужно.\n'
                  f'🧾 <b>Для вызова меню используйте /menu</b>')

    await message.answer(hello_text,
                         reply_markup=user_inline)

    if message.from_user.id not in users_id:  # Проверка на наличие пользователя в БД
        user_info = (f'<b>Зарегистрирован новый пользователь</b>\n'
                     f'<b>ID</b>: {message.from_user.id}\n'
                     f'<b>Username</b>: @{message.from_user.username}')

        await message.bot.send_message(chat_id=ADMIN_ID, text=user_info)
        await add_user(message.from_user.id, message.from_user.username)

# ==================================================================================================================
@user_router.message(Command("menu"))
async def menu(message: Message):
# ==================================================================================================================
    """Главное меню пользователя по команде /menu (на случай бага бота, если меню не появится само)"""

    await message.answer('📖 <b>Главное меню:</b>', reply_markup=user_inline)


# ========== 2. ОТПРАВКА ЖАЛОБЫ АДМИНУ ==========
# ==================================================================================================================
@user_router.callback_query(F.data == 'send_error')
async def send_error(callback: CallbackQuery, state: FSMContext):
# ==================================================================================================================
    """Функция устанавливает статус ожидания сообщения от пользователя"""

    await callback.answer('Вы выбрали написать о проблеме.')
    await callback.message.answer('<b>Опишите проблему</b> ✍️ или <b>прикрепите скриншот</b> 📱.')
    await state.set_state(UserError.waiting_for_error)  # Устанавливаем статус ожидания сообщения

# ==================================================================================================================
@user_router.message(UserError.waiting_for_error)
async def report(message: Message, state: FSMContext):
# ==================================================================================================================
    """Функция отправляет жалобу пользователя админу"""

    try:
        user_info = (f'❗ <b>Поступила новая жалоба</b>! От:\n'
                     f'<b>Имя:</b> {message.from_user.full_name}\n'
                     f'<b>ID:</b> {message.from_user.id}\n'
                     f'<b>Username:</b> @{message.from_user.username}')  # Сбор информации о пользователе

        await message.bot.send_message(chat_id=ADMIN_ID, text=user_info)  # Отправка админу

        await message.send_copy(chat_id=ADMIN_ID)  # Копия сообщения в чат админа
        await message.answer('✅ <b>Ваша жалоба была отправлена админу.</b>\n'
                             'Он просмотрит и исправит ее в ближайшее время. ✍️',
                             reply_markup=user_inline)

    except (TelegramForbiddenError, TelegramAPIError):
        await message.answer('🚫 <b>При отправке жалобы произошла ошибка!</b> Повторите попытку позже...',
                             reply_markup=user_inline)
    finally:
        await state.clear()


# ========== 3. ПОЛУЧЕНИЕ КЛЮЧЕЙ ==========
# ==================================================================================================================
@user_router.callback_query(F.data == 'get_key')
async def get_user_key(callback: CallbackQuery, bot_api_client: ApiBotClient):
# ==================================================================================================================
    """Функция, которая выдает из БД ключ пользователю"""

    await callback.answer('Вы выбрали получить ключ(-и).')

    # Получаем актуальные ключи для пользователя
    users_data = await get_user_keys(callback.from_user.id)

    # Проверяем, есть ли у пользователя ключи
    if not users_data:
        await callback.message.answer('🚫 К сожалению на данный момент у вас <b>нет активных ключей</b> 😥 '
                                      'Обратитесь к владельцу.',
                                      reply_markup=user_inline)
        return

    await callback.message.answer('📜 <b>Ваши ключи:</b>')

    # Проходимся по массиву ключей и по очереди выдаем пользователю
    for num, key in enumerate(users_data, start=1):
        key_email = await bot_api_client.get_user_email(callback.from_user.id)
        user_key_text = (f'🔑 <b>Ключ №{num}:</b>\n'
                         f'📜 <b>Название ключа:</b> {key_email}\n'
                         f'<code>{key}</code>')

        await callback.message.answer(text=user_key_text,
                                      disable_web_page_preview=True)

    await callback.message.answer('Что-нибудь ещё? 🤗', reply_markup=user_inline)