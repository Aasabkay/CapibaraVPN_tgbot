"""Файл API соединения с 3X-UI"""


import httpx
import json
from config import SERVER_IP, ENCRYPTION, SERVICE_NAME, PBK, FP, SNI, SID, SPX, PQV

class ApiBotClient:
    def __init__(self, host: str, username: str, password: str):  # Инициируем базовые переменные
        self.host = host.rstrip('/')
        self.username = username
        self.password = password

        self.client = httpx.AsyncClient()  # Для запоминания сессии

    # Функция входа в панель
    async def login(self):
        url = f'{self.host}/login'

        payload = {
            'username': self.username,
            'password': self.password
        }  # Данные для входа

        try:
            response = await self.client.post(url=url, data=payload)  # Делаем POST запрос на сервер

            if response.status_code == 200:
                data = response.json()

                if data.get('success') is True:
                    print('Успешная авторизация в панели!')
                    return True
                else:
                    print(f'Панель вернула ошибку: {data.get("msg")}')
                    return False
            else:
                print(f'Ошибка подключения к серверу: Статус-код: {response.status_code}')
                return False
        except Exception as e:
            print(f'Произошла ошибка при попытке логина: {e}')
            return False

    # Функция закрытия соединения
    async def close_connection(self):
        await self.client.aclose()
        print('Закрываю соединение')

    # Функция получения инбаундов
    async def get_inbounds(self):
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
                print(f'Ошибка подключения к серверу. Статус-код: {response.status_code}')
                return False
        except Exception as e:
            print(f'Произошла ошибка при получении инбаундов: {e}')
            return False

    # Функция получения ключей пользователей
    async def get_client_keys(self):
        inbound_list = await self.get_inbounds()  # Из вышеописанной функции берем все инбаунды

        # Проверка на пустой словарь, чтобы программа не упала
        if inbound_list is None:
            return {}

        results = {}

        for inbound in inbound_list:
            if inbound['id'] == 1:  # Конкретно нужный инбаунд

                settings_list = json.loads(inbound['settings'])
                client_list = settings_list['clients']

                for client in client_list:
                    email = client.get('email', '')
                    client_uuid = client.get('id', '')
                    if '_' in email:
                        user_id = email.split('_')[0]

                        if user_id.isdigit():
                            user_id = int(user_id)

                            vless_link = (f'vless://{client_uuid}@{SERVER_IP}:443?type=grpc&encryption={ENCRYPTION}'
                                          f'&serviceName={SERVICE_NAME}&authority=&mode=multi&security=reality'
                                          f'&pbk={PBK}&fp={FP}&sni={SNI}&sid={SID}&spx={SPX}&pqv={PQV}#{email}'
                                          )
                            if user_id not in results:
                                results[user_id] = []
                            results[user_id].append(vless_link)
                        else:
                            continue
            else:
                continue
        return results