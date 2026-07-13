"""Файл, отвечающий за панель АДМИНА"""

from aiogram import F, Router
from aiogram.exceptions import TelegramForbiddenError, TelegramAPIError
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.keyboards.inline import user_inline
from app.state import UserError
from config import ADMIN_ID
from app.database.database import add_user, get_user_keys, get_all_users

user_router = Router()

# Стартовое сообщение для пользователя
@user_router.message(CommandStart())
async def user_start(message: Message):
    users_id = await get_all_users()
    await message.answer('---\nПривет! Я - CapibaraVPN бот, созданный для удобства создателя '
                         'и пользователей CapibaraVPN.\n---'
                         '\nНиже есть кнопки: "Получить ключ" и "Отправить ошибку". \n---'
                         '\nДумаю, объяснять зачем они, не нужно. Для вызова меню используйте /menu'
                         ,reply_markup=user_inline)
    await add_user(message.from_user.id, message.from_user.username)

    if message.from_user.id not in users_id:  # Проверка на наличие пользователя в БД
        user_info = (f'**Зарегистрирован новый пользователь**\n'
                     f'**ID**: {message.from_user.id}\n'
                     f'**Username**: @{message.from_user.username}')

        await message.bot.send_message(chat_id=ADMIN_ID, text=user_info, parse_mode='Markdown')

# Функция меню для пользователя через команду /menu
@user_router.message(Command("menu"))
async def menu(message: Message):
    await message.answer('Главное меню:', reply_markup=user_inline)


# Обработка ошибок
@user_router.callback_query(F.data == 'send_error')
async def send_error(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Вы выбрали написать о проблеме.')
    await callback.message.answer('Опишите проблему или прикрепите скриншот.')
    await state.set_state(UserError.waiting_for_error)  # Устанавливаем статус ожидания сообщения

@user_router.message(UserError.waiting_for_error)
async def report(message: Message, state: FSMContext):
    try:
        user_info = (f'**Поступила новая жалоба**! От:\n'
                     f'Имя: {message.from_user.full_name}\n'
                     f'ID: {message.from_user.id}\n'
                     f'Username: @{message.from_user.username}')  # Сбор информации о пользователе

        await message.bot.send_message(chat_id=ADMIN_ID, text=user_info, parse_mode='Markdown')  # Отправка админу

        await message.send_copy(chat_id=ADMIN_ID)  # Копия сообщения в мой чат
        await message.answer('**Ваша жалоба была отправлена админу.**\nОн просмотрит и исправит ее в ближайшее время.',
                             reply_markup=user_inline, parse_mode='Markdown')  # Markdown чисто для разметки

    except (TelegramForbiddenError, TelegramAPIError):
        await message.answer('**При отправке жалобы произошла ошибка!** Повторите попытку позже...',
                             reply_markup=user_inline, parse_mode='Markdown')
    finally:
        await state.clear()


# Функция получения ключей пользователем
@user_router.callback_query(F.data == 'get_key')
async def get_user_key(callback: CallbackQuery):
    await callback.answer('Вы выбрали получить ключ(-и).')

    users_data = await get_user_keys(callback.from_user.id)

    if not users_data:
        await callback.message.answer('К сожалению на данный момент у вас нет активных ключей. Обратитесь к владельцу.',
                                      reply_markup=user_inline)
        return

    await callback.message.answer('Ваши ключи:')
    for num, key in enumerate(users_data, start=1):
        await callback.message.answer(text=f'<b>Ключ №{num}:</b>\n<code>{key}</code>',
                                      parse_mode='HTML',
                                      disable_web_page_preview=True)

    await callback.message.answer('Что-нибудь ещё?', reply_markup=user_inline)