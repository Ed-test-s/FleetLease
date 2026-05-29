# FleetLease: deploy на Railway

Этот документ описывает production-развертывание проекта в Railway без изменения
локального сценария разработки (`docker-compose` + MinIO + hot reload + Vite dev server).

## 1) Что используется в репозитории

- Backend Dockerfile: `backend/Dockerfile.railway`
- Frontend Dockerfile: `frontend/Dockerfile.railway`
- Frontend nginx config: `frontend/nginx.railway.conf`

Локальные `backend/Dockerfile`, `frontend/Dockerfile` и `docker-compose.yml` не меняются и
остаются для dev-окружения.

## 2) Что создается в Railway

В Railway-конструкторе создайте:

1. PostgreSQL plugin
2. Object Storage (S3-compatible)
3. Service `backend` из этого репозитория:
   - Root Directory: `backend`
   - Dockerfile Path: `Dockerfile.railway`
4. Service `frontend` из этого репозитория:
   - Root Directory: `frontend`
   - Dockerfile Path: `Dockerfile.railway`

## 3) Railway variables для backend

Обязательные:

- `DATABASE_URL` = `postgresql+asyncpg://...`
- `DATABASE_URL_SYNC` = `postgresql://...`
- `SECRET_KEY` = длинный случайный секрет
- `MINIO_ENDPOINT`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `MINIO_BUCKET`
- `MINIO_ABOUT_BUCKET`
- `MINIO_SECURE=true`
- `MINIO_EXTERNAL_ENDPOINT`
- `CORS_ORIGINS=["https://<frontend-domain>.up.railway.app"]`

Опциональные:

- `NBRB_BASE_URL`, `NBRB_REQUEST_TIMEOUT`, `VAT_RATE_PERCENT`
- SMTP-переменные `MAIL_*` для восстановления пароля

## 4) Порядок деплоя

1. Задеплойте backend.
2. Проверьте endpoint `GET /health` на backend-домене.
3. Задеплойте frontend.
4. Откройте frontend-домен и проверьте базовые пользовательские сценарии.

## 5) Smoke-test checklist

- [ ] Главная страница frontend открывается.
- [ ] Прямой переход по SPA-маршруту (например `/catalog`) не дает 404.
- [ ] API-вызовы из frontend проходят успешно.
- [ ] Авторизация работает.
- [ ] Загрузка/чтение файлов из S3 работает.

## 6) Типичные проблемы и решения

### CORS ошибки

Симптом: браузер блокирует запросы к API.  
Решение: проверьте `CORS_ORIGINS` в backend Railway variables.

Поддерживаемые форматы:

- JSON: `["https://frontend.example.com"]`
- CSV: `https://frontend.example.com,https://admin.example.com`

### Неверный S3 endpoint

Симптом: ошибки при загрузке/чтении файлов (`S3Error`, timeout).  
Решение:

- убедитесь, что `MINIO_ENDPOINT` указывает на endpoint Railway Object Storage;
- если endpoint с TLS, используйте `MINIO_SECURE=true`;
- в `MINIO_EXTERNAL_ENDPOINT` укажите публичный URL для формирования ссылок на объекты.

### Неверный порт приложения

Симптом: backend не становится healthy в Railway.  
Решение: `backend/Dockerfile.railway` уже запускает uvicorn с `${PORT:-8000}`; убедитесь, что
не переопределили команду запуска в Railway.

### Frontend не видит backend

Симптом: `502`/`504` от nginx на `/api`.  
Решение: проверьте сервисное имя backend в Railway private network. При необходимости
обновите upstream в `frontend/nginx.railway.conf`.
