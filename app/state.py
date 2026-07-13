"""Файл состояний пользователей"""

from aiogram.fsm.state import StatesGroup, State

# Состояние рассылки для администратора
class AdminBroadcast(StatesGroup):
    waiting_for_content = State()

# Состояние для отправки пользователем ошибки
class UserError(StatesGroup):
    waiting_for_error = State()

class AddKeyToUser(StatesGroup):
    id = State()
    keys_num = State()
    key = State()