# Базовый образ. Если poetry ругается на версию Python (requires-python),
# замени на python:3.13-slim
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Системные зависимости: libpq5 нужен для psycopg2-binary
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

# Poetry
RUN pip install --no-cache-dir poetry

# Сначала копируем только файлы зависимостей — так слой кэшируется
# и пересборка при изменении кода не переуставляет пакеты
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Копируем код проекта
COPY . .

EXPOSE 8000

# По умолчанию запускаем gunicorn (боевой WSGI-сервер)
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]