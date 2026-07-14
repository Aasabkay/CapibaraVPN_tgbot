"""Файл API клиента для соединения с 3X-UI"""

# Импорт необходимых библиотек
import httpx
import json
from typing import Any
# Импорт необходимых данных из .env
from config import SERVER_IP, ENCRYPTION, SERVICE_NAME, PBK, FP, SNI, SID, SPX, PQV

# Класс API клиента
# ==================================================================================================================
class ApiBotClient:
    def __init__(self, host: str, username: str, password: str):  # Инициируем базовые переменные
        self.host = host.rstrip('/')
        self.username = username
        self.password = password

        self.client = httpx.AsyncClient()  # Хранение соединений и Cookies

    # ==================================================================================================================
    async def login(self) -> bool:
    # ==================================================================================================================
        """Функция для входа в панель 3X-UI"""
        url = f'{self.host}/login'

        payload = {
            'username': self.username,
            'password': self.password
        }  # Данные для входа

        try:
            response = await self.client.post(url=url, data=payload)  # Делаем POST запрос на сервер

            if response.status_code == 200:
                data = response.json()  # Записываем ответ от сервера

                if data.get('success') is True:  # Если панель вернула success
                    print('Успешная авторизация в панели!')
                    return True
                else:
                    print(f'Панель вернула ошибку: {data.get("msg")}')
                    return False
            else:
                print(f'Ошибка подключения к серверу на этапе логина: Статус-код: {response.status_code}')
                return False
        except Exception as e:
            print(f'Произошла ошибка при попытке логина: {e}')
            return False

    # ==================================================================================================================
    async def close_connection(self) -> None:
    # ==================================================================================================================
        """Функция предназначена для закрытия соединения с панелью"""

        await self.client.aclose()
        print('Закрываю соединение')

    # ==================================================================================================================
    async def get_inbounds(self) -> Any:
    # ==================================================================================================================
        """Функция получения всех имеющихся inbounds"""

        url = f'{self.host}/panel/api/inbounds/list'

        try:
            response = await self.client.get(url)  # Делаем GET запрос на сервер

            if response.status_code == 200:
                data = response.json()

                if data.get('success') is True:
                    inbounds = data.get('obj', [])  # Берем ключ obj, если не найдется, то дефолтное значение []
                    print(f'Успешно получено {len(inbounds)} инбаундов.')
                    return inbounds

                else:
                    print(f'Ошибка в получении инбаундов. Ошибка: {data.get("msg")}')
                    return False
            else:
                print(f'Ошибка подключения к серверу на этапе получения инбаундов. Статус-код: {response.status_code}')
                return False
        except Exception as e:
            print(f'Произошла ошибка при получении инбаундов: {e}')
            return False

    # ==================================================================================================================
    async def get_client_keys(self) -> dict:
    # ==================================================================================================================
        """Функция предназначена для получения ключей пользователей"""

        inbound_list = await self.get_inbounds()  # Получаем все актуальные инбаунды

        # Проверка на пустой словарь, чтобы программа не упала
        if inbound_list is None:
            return {}

        results = {}

        for inbound in inbound_list:
            if inbound['id'] == 1:  # Конкретно нужный инбаунд

                settings_list = json.loads(inbound['settings'])  # Превращаем json в dict
                client_list = settings_list['clients']  # Список всех клиентов инбаунда

                for client in client_list:
                    email = client.get('email', '')  # email клиента
                    client_uuid = client.get('id', '')  # uuid клиента
                    if '_' in email:
                        user_id = email.split('_')[0]

                        if user_id.isdigit():
                            user_id = int(user_id)

                            # Сборка VLESS + gRPC + Reality ключа
                            vless_link = (f'vless://{client_uuid}@{SERVER_IP}:443?type=grpc&encryption={ENCRYPTION}'
                                          f'&serviceName={SERVICE_NAME}&authority=&mode=multi&security=reality'
                                          f'&pbk={PBK}&fp={FP}&sni={SNI}&sid={SID}&spx={SPX}&pqv={PQV}#{email}'
                                          )
                            # Добавляем пользователя и его ключи в словарь вида: {user: [key1, key2]}
                            if user_id not in results:
                                results[user_id] = []
                            results[user_id].append(vless_link)
                        else:
                            continue
            else:
                continue
        return results

    # ==================================================================================================================
    async def get_user_email(self, user_id) -> str:
    # ==================================================================================================================
        """Функция для определения email(имени пользователя) из ключа"""
        inbound_list = await self.get_inbounds()  # Получаем все инбаунды

        # Проверка на пустой словарь, чтобы программа не упала
        if inbound_list is None:
            return ''

        # Имя пользователя в ключе
        user_key_name = ''

        # Цикл проверки инбаундов
        for inbound in inbound_list:
            if inbound['id'] == 1:  # Конкретно нужный инбаунд

                # Импортируем json конфиг настроек и достаем список клиентов
                settings_list = json.loads(inbound['settings'])
                client_list = settings_list['clients']

                # Цикл проверки клиентов на совпадение по telegram_id
                for client in client_list:
                    email = client.get('email', '')
                    if '_' in email:
                        telegram_id = email.split('_')[0]
                        user_name = email.split('_')[1]

                        if telegram_id.isdigit():
                            telegram_id = int(telegram_id)
                            if user_id == telegram_id:
                                user_key_name = user_name
                        else:
                            continue
                    else:
                        continue
        return user_key_name
