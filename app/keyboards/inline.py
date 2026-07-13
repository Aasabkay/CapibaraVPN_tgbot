"""Файл, отвечающий за InlineButtons"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Кнопки администратора
admin_inline = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Просмотр всех пользователей', callback_data='all_users_list'),
     InlineKeyboardButton(text='Отправить сообщение клиентам', callback_data='msg')],
    [InlineKeyboardButton(text='Добавить ключ клиенту', callback_data='add_keys'),
     InlineKeyboardButton(text='Обновить ключи клиентам', callback_data='keys_update')]
])

# Кнопки других пользователей
user_inline = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Получить ключ', callback_data='get_key')],
    [InlineKeyboardButton(text='Отправить ошибку', callback_data='send_error')]
])