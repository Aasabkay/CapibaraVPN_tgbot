# 🦦 CapibaraVPN Bot

[RU] Асинхронный Telegram-бот на базе **Aiogram 3** для автоматизации и управления приватным VPN-сервисом (протоколы VLESS + Reality) через API панели **3X-UI**. Бот поддерживает ролевую модель (администратор/клиент), безопасную рассылку ключей, обработку тикетов обратной связи и использует изолированную микросервисную архитектуру.

[EN] An asynchronous Telegram bot based on **Aiogram 3** for automating and managing a private VPN service (VLESS + Reality protocols) via the **3X-UI** panel API. The bot supports a role-based model (admin/client), secure key distribution, feedback ticket processing, and utilizes an isolated microservice architecture.

---

## 🚀 Основной функционал / Main Features

**[RU] Для администратора:**
* **Синхронизация с 3X-UI:** Автоматический парсинг инбаундов и ключей напрямую из панели.
* **Управление пользователями:** Ролевая система, мониторинг базы клиентов.
* **Массовые рассылки:** Мультиконтейнерная отправка обновленных ключей с защитой от флуда (Rate Limits).

**[EN] For Administrator:**
* **3X-UI Synchronization:** Automatic parsing of inbounds and keys directly from the panel.
* **User Management:** Role system, monitoring the client database.
* **Mass Mailing:** Multi-container dispatch of updated keys with flood protection (Rate Limits).

**[RU] Для пользователя:**
* **Доступ к VPN:** Быстрое получение актуальных VLESS/Reality конфигураций.
* **Обратная связь:** Встроенная система тикетов для репорта багов с пересылкой медиафайлов и логов администратору.

**[EN] For User:**
* **VPN Access:** Quick retrieval of up-to-date VLESS/Reality configurations.
* **Feedback System:** Built-in ticket system for reporting bugs, including media and log forwarding to the admin.

---

## 🛠 Технологический стек / Tech Stack

* **Язык / Language:** Python 3.11+
* **Фреймворк / Framework:** Aiogram 3.x (Asyncio), httpx
* **База данных / Database:** PostgreSQL
* **Хранилище состояний / State Storage:** Redis 7 (FSM)
* **Оркестрация / Orchestration:** Docker, Docker Compose

---

## 📦 Архитектура проекта / Project Architecture

```text
├── app/
│   ├── database/         # База данных / Database
│   │   └── database.py   # Реализация функций для связи бота и БД / DB interaction functions
│   ├── handlers/         # Обработчики команд / Command handlers
│   │   ├── admin.py      # Команды администратора / Admin handlers
│   │   └── user.py       # Команды пользователей / User handlers
│   ├── keyboards/        # Клавиатуры / Bot Keyboards
│   │   └── inline.py     # Inline-клавиатуры / Inline keyboards
│   ├── services/         # Дополнительные сервисы / Additional services
│   │   └── vpn_api_client.py # Запросы к 3X-UI серверу / Requests to 3X-UI API
│   └── states.py         # Машина состояний / FSM states
├── .env.example          # Шаблон конфигурации / Environment config template
├── .gitignore            # Исключения Git / Git ignores
├── .dockerignore         # Исключения Docker / Docker ignores
├── Dockerfile            # Сборка образа / Image build
├── bot_run.py            # Точка входа / Entry point
├── config.py             # Загрузка переменных окружения / Env variables loading
├── requirements.txt      # Зависимости / Project dependencies
└── docker-compose.yml    # Манифест деплоя / Multi-container deploy manifest
```

# ⚙️ Установка и запуск / Installation & Setup
**[RU]** Бот упакован в Docker, что делает его развертывание на сервере (VPS) максимально быстрым.

**[EN]** The bot is dockerized, making its deployment on a server (VPS) as fast as possible.

* **1. Клонирование репозитория / Clone the repository**
```bash
git clone https://github.com/Aasabkay/CapibaraVPN_tgbot.git
cd CapibaraVPN_tgbot
```
* **2. Настройка переменных окружения / Environment configuration**

**[RU]** Создайте файл .env на основе шаблона `.env.example` и заполните свои данные (токен бота, доступы к БД и 3X-UI панели).

**[EN]** Create an .env file based on the template `.env.example` and fill in your credentials (bot token, DB access, and 3X-UI panel details).
```bash
cp .env.example .env
nano .env
```

* **3. Запуск через Docker Compose / Run with Docker Compose**

**[RU]** Рекомендуется использовать флаг -d для фонового запуска. Параметр restart: unless-stopped уже прописан в манифесте для автоматического перезапуска.

**[EN]** It is recommended to use the -d flag for background execution. The restart: unless-stopped parameter is already set in the manifest for auto-restarts.
```bash
docker compose up -d --build
```

* **4. Остановка бота / Stopping the bot**
```bash
docker compose down
```


