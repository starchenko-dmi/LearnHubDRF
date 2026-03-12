# LearnHub — Образовательная платформа на Django REST Framework

REST API для онлайн-платформы, где пользователи могут создавать, проходить курсы и оплачивать обучение. Проект реализован с использованием Django и Django REST Framework.


## Основные возможности

- Полноценный REST API с JWT-аутентификацией  
- Управление пользователями по email (включая аватарки)  
- CRUD для курсов и уроков с пагинацией (5 элементов на страницу)  
- Валидация видео: разрешены только `youtube.com` и `youtu.be`  
- Интеграция с Stripe: оплата курсов и отдельных уроков через безопасную Checkout-страницу  
- Подписки на обновления курсов + email-уведомления (не чаще 1 раза в 4 часа)  
- Гибкая система прав:  
  - Обычные пользователи — работают только со своими материалами  
  - Модераторы (`moderators`) — могут редактировать любые курсы/уроки (но не создавать/удалять)  
- Админка для управления всеми сущностями  
- Покрытие тестами: CRUD, права доступа, Stripe, Celery-задачи


## Технологии

- Python 3.13  
- Django 5.2 + DRF  
- PostgreSQL + Redis + Celery (с периодическими задачами)  
- djangorestframework-simplejwt  
- drf-yasg (Swagger UI)  
- Stripe API  
- Pillow (обработка изображений)  
- coverage (анализ покрытия)

## 🌐 Демо
Проект развернут по адресу: [http://158.160.183.134/swagger/](http://158.160.183.134/swagger/)

## Локальный запуск (Docker Compose)

### Требования
- Docker  
- Docker Compose  

### Шаги
git clone https://github.com/starchenko-dmi/LearnHubDRF.git
cd LearnHubDRF
cp .env.example .env

# Отредактируйте .env (SECRET_KEY, Stripe, email)
docker-compose up --build -d
docker-compose exec backend python manage.py migrate

# (опционально) docker-compose exec backend python manage.py createsuperuser

# LearnHub — Образовательная платформа на Django REST Framework

REST API для онлайн-платформы, где пользователи могут создавать, проходить курсы и оплачивать обучение. Реализовано с использованием Django 5.2 + DRF, JWT-аутентификация, Stripe, Celery + Redis, Swagger UI, админка, тестирование.

## Критические настройки безопасности (обязательно перед продакшеном)

`DEBUG = False` — никогда не включайте в продакшене; иначе утечка данных и 400 Bad Request при пустом `ALLOWED_HOSTS`.  
`SECRET_KEY` — длинный случайный ключ (≥50 символов), загружается из `.env` через `os.environ["SECRET_KEY"]`, никогда не коммитьте в репозиторий.  
`ALLOWED_HOSTS = ['ВАШ ХОСТ]` — обязательна при `DEBUG=False`, иначе все запросы вернут 400.  
`STATIC_ROOT = BASE_DIR / 'staticfiles'`, `STATIC_URL = '/static/'` — для сборки статики через `collectstatic`.  
`MEDIA_ROOT = BASE_DIR / 'media'`, `MEDIA_URL = '/media/'` — для загрузок пользователей (всегда разделяйте от `STATIC_*`).  
`SECURE_SSL_REDIRECT = True`, `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` — если за Nginx/Cloud Load Balancer.  
`X_FRAME_OPTIONS = 'DENY'`, `SECURE_CONTENT_TYPE_NOSNIFF = True`, `CSRF_TRUSTED_ORIGINS = ['https://ВАШ ХОСТ']` — защита от clickjacking, MIME-sniffing и CSRF.  
`SESSION_COOKIE_SECURE = True`, `SESSION_COOKIE_HTTPONLY = True` — безопасные куки сессий.  
`LOGGING` — настройте отправку ошибок на email (`ADMINS`) или в Sentry; проверьте через `python manage.py check --deploy`.

## Локальный запуск (Docker Compose)

Требования: Docker + Docker Compose.  
Клонируйте репозиторий: `git clone https://github.com/ваш-логин/LearnHubDRF.git && cd LearnHubDRF`.  
Создайте `.env` из шаблона: `cp .env.example .env`, затем заполните: `DEBUG=True`, `SECRET_KEY=...`, `STRIPE_*`, `EMAIL_*`, `DB_*`.  
Запустите: `docker compose up --build -d`, примените миграции: `docker compose exec backend python manage.py migrate`, при необходимости создайте суперпользователя: `docker compose exec backend python manage.py createsuperuser`.  
Документация: http://localhost:8000/swagger/.

## Настройка удалённого сервера (Yandex Cloud / AWS / др.)

Требования: Ubuntu 22.04+, порты 22 (SSH), 80/443 (HTTP/HTTPS).  
Установите Docker:  
sudo apt update && sudo apt upgrade -y  
sudo apt install -y docker.io  
sudo usermod -aG docker $USER  
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose  
newgrp docker  

Клонируйте проект:  
ssh ваш_пользователь@IP_адрес  
git clone https://github.com/ваш-логин/LearnHubDRF.git ~/learnhub && cd ~/learnhub  
cp .env.example .env  
nano .env — задайте: DEBUG=False, ALLOWED_HOSTS=IP_адрес, SECRET_KEY=..., STRIPE_*, EMAIL_*, DB_* (пароли и ключи — только из `.env`, не в коде).

Соберите и запустите:  
docker compose up -d --build  
docker compose exec backend python manage.py migrate  
docker compose exec backend python manage.py collectstatic --noinput  

## Настройка Nginx (обязательно для продакшена)

Установите: `sudo apt install nginx -y`.  
Создайте конфиг: `sudo nano /etc/nginx/sites-available/learnhub`, содержимое:
server {
    listen 80;
    server_name 158.160.183.134;
    location /static/ {
        alias /home/star-dim/learnhub/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options nosniff;
        add_header X-Frame-Options DENY;
    }
    location /media/ {
        alias /home/star-dim/learnhub/media/;
        add_header X-Content-Type-Options nosniff;
    }
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
Активируйте:  
sudo ln -s /etc/nginx/sites-available/learnhub /etc/nginx/sites-enabled/  
sudo nginx -t && sudo systemctl reload nginx  

Проверьте:  
curl -I http://ВАШ_ХОСТ/api/courses/ → 200 OK или 401 Unauthorized  
curl -I http://ВАШ_ХОСТ/static/drf-yasg/style.css → должен вернуть text/css, а не text/html  
Swagger: http://ВАШ_ХОСТ/swagger/ — должен отображаться с полным стилем  
docker compose ps — все сервисы в статусе Up  

## Автоматический деплой через GitHub Actions

В репозитории → Settings → Secrets and variables → Actions → добавьте:  
HOST = IP_адрес_сервера  
USERNAME = имя_пользователя  
SSH_KEY = приватный ключ (содержимое id_ed25519, без пароля)  

Файл `.github/workflows/deploy.yml`:  
name: Deploy to Production  
on: push  
  branches: [ develop ]  
jobs:  
  deploy:  
    runs-on: ubuntu-latest  
    steps:  
      - name: Deploy to server  
        uses: appleboy/ssh-action@v1.0.3  
        with:  
          host: ${{ secrets.HOST }}  
          username: ${{ secrets.USERNAME }}  
          key: ${{ secrets.SSH_KEY }}  
          script: |  
            cd /home/$USER/learnhub  
            git pull origin develop  
            docker compose down  
            docker compose up -d --build  

> Примечание: `.env` должен быть на сервере и содержать актуальные настройки. Не используйте `git pull` по SSH, если не уверены в ключах — лучше `scp` для копирования папки напрямую.

## Почему возникает ошибка «Cross-Origin-Opener-Policy header ignored»

Это предупреждение браузера, а не ошибка сервера: браузер считает `http://IP:8000` «ненадёжным origin» (не HTTPS, не localhost), поэтому игнорирует заголовок `Cross-Origin-Opener-Policy`. Решение:  
— В продакшене всегда используйте HTTPS (Nginx + Let’s Encrypt).  
— В dev можно игнорировать — или запускайте через `localhost:8000`, где origin считается доверенным.

## Почему статика не грузится (MIME type 'text/html' is not a supported stylesheet)

Запрос к `/static/...` возвращает HTML (например, 404 Django), а не CSS/JS. Причины:  
— `STATIC_ROOT` не задан или пустой,  
— `collectstatic` не запускался,  
— `STATIC_URL ≠ '/static/'`,  
— в `urls.py` есть `static(...)` при `DEBUG=False` (это допустимо только для dev),  
— Nginx не настроен на раздачу `/static/` (главная причина в продакшене).  

Решение:  
1. Убедитесь, что `STATIC_ROOT` существует и содержит файлы (`ls -la staticfiles/`).  
2. Выполните `docker compose exec backend python manage.py collectstatic --noinput`.  
3. В Nginx — `location /static/ { alias /путь/к/staticfiles/; }`, без `index`, без `try_files`.  
4. Перезапустите: `sudo systemctl reload nginx && docker compose down && docker compose up -d`.

## Дополнительно: Gunicorn вместо runserver

В `docker-compose.yml` замените команду backend на:  
command: gunicorn --bind 0.0.0.0:8000 config.wsgi:application  
В `requirements.txt` добавьте: `gunicorn>=23.0.0`.  
Убедитесь, что `config/wsgi.py` существует (он создаётся при `startproject`).  
Это повышает производительность и безопасность — `runserver` запрещён в продакшене.

Готово. Платформа полностью настроена, безопасна и готова к эксплуатации.
