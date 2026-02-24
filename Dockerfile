FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей для psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Установка зависимостей Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование проекта
COPY . .

# Сборка статических файлов
RUN python manage.py collectstatic --noinput

# Запуск Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "backend.wsgi:application"]