FROM python:3.13-slim

WORKDIR /app

# Установка системных зависимостей для psycopg2 и Pillow
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Настраиваем кодировку (важно для Python 3.13+)
ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]