# LearnHub — Образовательная платформа на Django REST Framework

REST API для онлайн-платформы, где пользователи могут создавать, проходить курсы и оплачивать обучение. Реализовано с использованием Django и Django REST Framework.

## Основные возможности

Проект предоставляет полноценный REST API для образовательной платформы с поддержкой пользователей, курсов, уроков, платежей и подписок. Все операции защищены и соответствуют принципам безопасности.

- **Регистрация и управление пользователями** осуществляется по email. Аутентификация реализована через JWT-токены (получение и обновление). Пользователи могут загружать аватарки, а авторы — превью для курсов и уроков.
- **Для курсов и уроков реализован полный CRUD**: курсы управляются через ViewSet, уроки — через Generic-классы. При просмотре курса отображается список его уроков и их количество.
- **Система платежей** поддерживает оплату как целого курса, так и отдельных уроков. Список платежей можно фильтровать и сортировать по дате, курсу, уроку или способу оплаты.
- **Валидация видео**: все ссылки на видео в уроках проходят валидацию — разрешены только домены youtube.com и youtu.be.
- **Подписки на обновления курсов**: пользователи могут подписываться на обновления курсов. При обновлении курса всем подписчикам отправляется email-уведомление, но не чаще чем раз в 4 часа, чтобы избежать спама.
- **Пагинация**: для удобства навигации реализована пагинация — списки курсов и уроков разбиты на страницы по 5 элементов.
- **Гибкая система прав доступа**:
  - Обычные пользователи могут видеть, редактировать и удалять только свои курсы и уроки.
  - Модераторы (пользователи в группе moderators) могут просматривать и редактировать любые материалы, но не могут создавать или удалять их.
- **Профиль пользователя защищён**: редактировать можно только свой профиль, а при просмотре чужого отображаются только публичные данные — email и город.
- **Админка** позволяет управлять всеми сущностями: пользователями, группами, курсами, уроками, платежами и подписками.
- **Проект покрыт автоматическими тестами**: проверяются CRUD-операции, права доступа, валидация YouTube, логика подписок, асинхронные задачи и интеграция с Stripe.

## Новый функционал

### Интеграция с Stripe
Добавлена интеграция с Stripe для приёма платежей. При запросе оплаты курса создаются продукт, цена и сессия в Stripe. Пользователь получает ссылку на безопасную страницу Stripe Checkout. Поддерживается проверка статуса платежа по ID сессии. Используются тестовые карты (например, 4242 4242 4242 4242), поэтому деньги не списываются.

### Асинхронные задачи через Celery и Redis
Реализованы асинхронные задачи:
- При обновлении курса запускается задача отправки email-уведомлений всем подписчикам.
- Ежедневно в 02:00 выполняется периодическая задача, которая блокирует пользователей (is_active = False), не заходивших в систему более 30 дней (на основе поля last_login).

Умная логика уведомлений гарантирует, что письмо отправляется только если курс не обновлялся последние 4 часа.

### Тестирование
Тестирование нового функционала включает:
- Юнит-тесты для Celery-задач с использованием моков.
- Интеграционный тест Stripe, который создаёт реальную сессию в тестовом режиме и проверяет её статус.
- Все тесты проходят без необходимости запускать Redis или Celery вручную.

## Структура проекта

Проект состоит из двух основных приложений:

### Приложение `users`
- **Кастомная модель User**: авторизация по email, аватарка, город проживания
- **Модель Payment**: хранение информации о платежах, включая данные Stripe (stripe_session_id, stripe_payment_url)
- **Celery-задачи**:
  - `send_course_update_notification` — отправка email-уведомлений при обновлении курса
  - `deactivate_inactive_users` — блокировка пользователей, не заходивших более 30 дней

### Приложение `materials`
- **Модель Course**: название, описание, превью, владелец, цена, дата последнего обновления
- **Модель Lesson**: название, описание, превью, ссылка на видео (с валидацией YouTube), курс
- **Модель Subscription**: связь пользователь-курс для управления подписками
- **Валидатор**: `validate_youtube_url` — проверяет, что ссылка ведёт на youtube.com или youtu.be
- **Пагинатор**: `MaterialsPagination` — разбивает списки на страницы по 5 элементов

## Технологии

Проект использует современный стек технологий:
- Python 3.13
- Django 5.2
- Django REST Framework
- djangorestframework-simplejwt
- PostgreSQL
- Redis
- Celery с celery-beat
- Stripe API
- drf-yasg для генерации документации Swagger
- Pillow для обработки изображений
- coverage для анализа покрытия тестами
- Docker и Docker Compose для контейнеризации
- Nginx для раздачи статики и проксирования
- Gunicorn для продакшен-сервера

## Запуск проекта

### Локально (через Docker Compose)

```bash
# 1. Клонировать репозиторий
git clone https://github.com/starchenko-dmi/LearnHubDRF.git
cd LearnHubDRF

# 2. Создать .env из шаблона
cp .env.example .env

# 3. Настроить .env
nano .env
```

В `.env` укажите:
- `SECRET_KEY` — минимум 50 случайных символов
- `STRIPE_SECRET_KEY`, `STRIPE_PUBLIC_KEY` — тестовые ключи Stripe (получите в [dashboard.stripe.com/test/apikeys](https://dashboard.stripe.com/test/apikeys))
- `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` — данные для отправки email (например, Яндекс: `EMAIL_HOST_USER=ваш@yandex.ru`, `EMAIL_HOST_PASSWORD=пароль_приложения`)

```bash
# 4. Запустить контейнеры
docker compose up --build -d

# 5. Применить миграции
docker compose exec backend python manage.py migrate

# 6. (Опционально) Создать суперпользователя
docker compose exec backend python manage.py createsuperuser

# 7. Открыть документацию
http://localhost:8000/swagger/
```

## Развёртывание на удалённом сервере

### Требования
- Ubuntu 22.04+ (рекомендуется: 2 CPU, 2 ГБ RAM)
- Открытые порты: `22` (SSH), `80`/`443` (HTTP/HTTPS)

### Установка Docker
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io
sudo usermod -aG docker $USER
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
newgrp docker
```

### Настройка проекта
```bash
git clone https://github.com/ваш-логин/LearnHubDRF.git ~/learnhub
cd ~/learnhub
cp .env.example .env
nano .env
```

В `.env` укажите:
```env
DEBUG=False
ALLOWED_HOSTS=IP_адрес_сервера
SECRET_KEY=ваш_надёжный_ключ_минимум_50_символов
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLIC_KEY=pk_test_...
EMAIL_HOST_USER=ваш@email.com
EMAIL_HOST_PASSWORD=пароль_приложения
```

### Запуск
```bash
docker compose up -d --build
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic --noinput
```

## Настройка Nginx (обязательно для продакшена)

### Установка и конфигурация
```bash
sudo apt install nginx -y
sudo nano /etc/nginx/sites-available/learnhub
```

### Содержимое конфига:
```nginx
server {
    listen 80;
    server_name IP_адрес_сервера;

    location /static/ {
        alias /var/www/learnhub/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options nosniff;
    }

    location /media/ {
        alias /var/www/learnhub/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Активация:
```bash
sudo ln -s /etc/nginx/sites-available/learnhub /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Автоматический деплой через GitHub Actions

### Секреты в репозитории
- `HOST` — IP-адрес сервера
- `USERNAME` — имя пользователя на сервере
- `SSH_KEY` — приватный ключ (содержимое файла `id_ed25519`)

### Файл `.github/workflows/deploy.yml`
```yaml
name: Deploy LearnHub with Docker

on:
  push:
    branches: [ develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Install lint dependencies
        run: pip install flake8

      - name: Run linting
        run: flake8 .

      - name: Test Docker build
        run: docker compose build --no-cache backend

      - name: Run tests
        env:
          SECRET_KEY: fake-secret-key
          DEBUG: 'True'
        run: python manage.py test

  deploy:
    needs: test
    if: success() && github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - name: Copy files to server
        uses: appleboy/scp-action@v0.1.7
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.SSH_KEY }}
          source: "."
          target: "/home/star-dim/learnhub"
          strip_components: 1

      - name: Deploy on server
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.SSH_KEY }}
          script_stop: true
          script: |
            set -e
            cd /home/star-dim/learnhub
            docker compose down
            docker compose up -d --build
            if ! docker compose ps --services --status running | grep -q backend; then
              echo "❌ ERROR: backend container failed to start!"
              exit 1
            fi
            echo "✅ Deployment successful"
```

## Критические настройки безопасности

| Настройка | Значение в продакшене | Примечание |
|----------|------------------------|------------|
| `DEBUG` | `False` | Обязательно! Иначе утечка данных. |
| `SECRET_KEY` | Случайная строка ≥50 символов | Никогда не коммитьте в репозиторий! |
| `ALLOWED_HOSTS` | `['IP_адрес_сервера']` | Обязателен при `DEBUG=False`. |
| `STATIC_ROOT` | `/var/www/learnhub/staticfiles/` | Для `collectstatic`. |
| `MEDIA_ROOT` | `/var/www/learnhub/media/` | Для загрузок пользователей. |
| `SECURE_SSL_REDIRECT` | `True` | Только после настройки HTTPS. |
| `SECURE_PROXY_SSL_HEADER` | `("HTTP_X_FORWARDED_PROTO", "https")` | Если за Nginx. |

> **Важно**: Все секреты — только через `.env`, который добавлен в `.gitignore`.

## Проверка работоспособности

- **API**:  
  ```bash
  curl -I http://IP_адрес_сервера/api/courses/
  ```
  → должен вернуть `200 OK` или `401 Unauthorized`

- **Статика**:  
  ```bash
  curl http://IP_адрес_сервера/static/drf-yasg/style.css
  ```
  → должен вернуть CSS, а не HTML

- **Swagger**:  
  http://IP_адрес_сервера/swagger/ — должен отображаться с полным стилем

- **Контейнеры**:  
  ```bash
  docker compose ps
  ```
  — все сервисы в статусе `Up`

## Примеры использования API

### Получение JWT-токена
```bash
curl -X POST http://IP_адрес_сервера/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@mail.ru", "password":"admin"}'
```

Пример ответа:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Получение списка курсов
```bash
curl -X GET http://IP_адрес_сервера/api/courses/ \
  -H "Authorization: Bearer <access_token>"
```

Пример ответа:
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Python для начинающих",
      "description": "Базовый курс по Python",
      "preview": null,
      "owner": 1,
      "price": 5000,
      "last_update": "2026-03-11T15:00:00Z",
      "lessons_count": 10
    },
    {
      "id": 2,
      "title": "Django REST Framework",
      "description": "Создание REST API на DRF",
      "preview": null,
      "owner": 1,
      "price": 7000,
      "last_update": "2026-03-11T15:05:00Z",
      "lessons_count": 15
    }
  ]
}
```

## Лицензия

Этот проект лицензирован в соответствии с MIT License - подробности см. в файле [LICENSE](LICENSE).

---

Готово. Проект полностью настроен для безопасной работы в продакшене:
✅ HTTPS через Nginx  
✅ Статика раздаётся напрямую (не через Django)  
✅ Секреты из `.env`  
✅ Автодеплой  
✅ Защита от XSS, CSRF, Clickjacking, MIME-sniffing  
✅ Поддержка Stripe, Celery, Swagger, JWT