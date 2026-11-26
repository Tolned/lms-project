# 🎓 LMS Project — Платформа онлайн-обучения

**Бэкенд-часть SPA веб-приложения для управления курсами, уроками, платежами
и рассылками. Интеграция с Celery для фоновых задач, Stripe для платежей и
Docker Compose для оркестрации сервисов.**

Разработано в рамках профильного курса по бэкенд-разработке от **Skypro**.

---

## 🛠️ Технологический стек

* **Язык программирования:** Python 3.12+
* **Фреймворк:** Django 6.0, Django REST Framework
* **Пакетный менеджер:** Poetry
* **База данных:** PostgreSQL 16
* **Очереди и брокер:** Celery 5, Celery Beat, Redis 7
* **Платежи:** Stripe API
* **Аутентификация:** `djangorestframework-simplejwt` (JWT)
* **Документация API:** `drf-spectacular` (OpenAPI 3.0, Swagger, ReDoc)
* **Контейнеризация:** Docker, Docker Compose
* **Тестирование:** Pytest, Pytest-Django, Pytest-Cov, Pytest-Mock
* **Качество кода:** Flake8, Black, Isort, Mypy

---

## 🚀 Архитектура и функциональные модули

### 🛡️ 1. Пользователи и авторизация (`users/`)

Управление учетными записями и разграничение прав доступа:

* **Кастомная модель `User`** — авторизация по `email` вместо `username`,
  поле `telegram_chat_id` для интеграции с ботом.
* **JWT-аутентификация** — пара `access`/`refresh` токенов с настраиваемым
  временем жизни.
* `IsOwnerOrReadOnly` — пользователь может редактировать только свои объекты.
* `IsModerator` — расширенные права для модераторов платформы.

### 📚 2. Курсы и уроки (`lms/`)

Ядро платформы — управление учебным контентом:

* **Модель `Course`** — название, описание, цена, владелец, поле
  `updated_at` для отслеживания обновлений.
* **Модель `Lesson`** — привязка к курсу, валидация YouTube-ссылок.
* **Пагинация `PageNumberPagination`** — вывод по 5 элементов на страницу.
* **Фильтрация и сортировка** — на базе `DjangoFilterBackend` и
  `OrderingFilter`.

### 🔔 3. Подписки и уведомления

Механизм оповещения пользователей об изменениях:

* **Модель `Subscription`** — связь `пользователь ↔ курс` с уникальным
  ограничением.
* `send_course_update_notification` — отложенная Celery-задача для рассылки
  email подписчикам при обновлении курса.
* **Защита от спама (правило 4 часов)** — уведомление отправляется только
  если курс не обновлялся более 4 часов.
* **Celery Beat** — периодическая задача `deactivate_inactive_users` для
  блокировки пользователей, не заходивших более 30 дней.

### 💳 4. Платежи и интеграция со Stripe

Модуль: `lms/services.py`.

* **Создание продукта и цены** в Stripe через API.
* **Checkout Session** — генерация ссылки на оплату.
* **Проверка статуса платежа** — webhook-подобная логика обновления статуса.
* **История платежей** — привязка к пользователю с возможностью фильтрации.

### 🐳 5. Оркестрация сервисов (Docker Compose)

Файлы: `Dockerfile`, `docker-compose.yml`.

* **5 сервисов в одной команде** — `db`, `redis`, `web`, `celery`,
  `celery-beat`.
* **`expose` вместо `ports`** — PostgreSQL и Redis изолированы внутри
  Docker-сети.
* **Named volumes** — `postgres_data`, `redis_data`, `media_volume` для
  сохранности данных.
* **Healthcheck** — сервисы стартуют в строгом порядке готовности.
* **`env_file: .env`** — переменные окружения подключены ко всем сервисам,
  секреты не хранятся в коде.

### 📝 6. Декораторы и валидаторы

* **Кастомные валидаторы DRF** — проверка YouTube-URL, валидация
  взаимоисключающих полей.
* `@extend_schema` от `drf-spectacular` — ручное описание сложных
  эндпоинтов.
* **Консольный email-бэкенд** — для локальной отладки без SMTP-сервера.

---

## 🧪 Тестирование и контроль качества кода

Проект покрыт модульными и интеграционными тестами с использованием фикстур,
параметризации и мок-объектов (`unittest.mock`, `pytest-mock`).

```bash
# Запуск всех тестов с отчетом о покрытии кода (требование: 80%+)
poetry run pytest --cov=users --cov=lms --cov=config \
  --cov-report=term-missing

# Проверка стиля кода (PEP 8) и строгой типизации
poetry run flake8
poetry run mypy .

# Автоматическое форматирование кода и импортов
poetry run isort .
poetry run black .
```

---

## 💻 Инструкция по развертыванию и запуску

### Вариант A: Docker Compose (рекомендуется)

#### 1. Клонирование репозитория

```bash
git clone https://github.com
cd lms-project
```

#### 2. Настройка переменных окружения

Создайте файл `.env` в корне проекта по образцу `.env.example`:

```bash
cp .env.example .env
```

Заполните реальные значения `SECRET_KEY`, `STRIPE_SECRET_KEY` и
`STRIPE_PUBLISHABLE_KEY`.

#### 3. Запуск всех сервисов одной командой

```bash
docker compose up --build
```

> Поднимутся 5 сервисов: PostgreSQL, Redis, Django (Gunicorn), Celery Worker,
> Celery Beat.

#### 4. Создание суперпользователя

```bash
docker compose exec web python manage.py createsuperuser
```

#### 5. Открытие приложения

* **API:** http://localhost:8000
* **Swagger UI:** http://localhost:8000/api/schema/swagger-ui/
* **ReDoc:** http://localhost:8000/api/schema/redoc/
* **Админка Django:** http://localhost:8000/admin/

---

### Вариант B: Локальный запуск (без Docker)

#### 1. Установка зависимостей через Poetry

```bash
poetry install
```

#### 2. Настройка `.env`

Создайте файл `.env` по образцу `.env.example` и укажите реальные данные для
PostgreSQL и Redis.

#### 3. Применение миграций

```bash
poetry run python manage.py migrate
```

#### 4. Запуск трёх процессов (в отдельных терминалах)

```bash
# Терминал 1 — Django
poetry run python manage.py runserver

# Терминал 2 — Celery Worker
poetry run celery -A config worker -l info

# Терминал 3 — Celery Beat
poetry run celery -A config beat -l info
```

---

## 📡 Основные эндпоинты API

### Пользователи и токены (`users/`)

* `POST /api/users/register/` — регистрация нового пользователя.
* `POST /api/users/token/` — получение пары JWT-токенов (`access`/`refresh`).
* `GET /api/users/me/` — просмотр профиля текущего пользователя.

### Курсы и подписки (`lms/`)

* `GET /api/lms/courses/` — получение списка курсов с пагинацией.
* `POST /api/lms/courses/` — создание нового курса.
* `PATCH /api/lms/courses/{id}/` — обновление курса с запуском рассылки.
* `POST /api/lms/subscribe/` — подписка на обновления выбранного курса.

### Платежи Stripe (`lms/`)

* `POST /api/lms/payment/create/` — создание платежной сессии через Stripe.
* `GET /api/lms/payment/status/` — проверка текущего статуса платежа.

> Полная интерактивная документация доступна по адресу
> `/api/schema/swagger-ui/`.

---

## 🐛 Troubleshooting

* **Ошибка подключения к PostgreSQL** — в Docker используйте хост `db`,
  локально — `localhost`.
* **Celery не видит Redis** — в Docker хост `redis`, локально —
  `localhost:6379`.
* **Порт 8000 занят** — измените маппинг в `docker-compose.yml`:
  `"8001:8000"`.
* **Миграции не применяются** — выполните
  `docker compose exec web python manage.py migrate`.

---

> 💡 *Проект выполнен в соответствии с техническим заданием и учебными
> стандартами Skypro.*
