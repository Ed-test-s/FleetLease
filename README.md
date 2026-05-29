# FleetLease — Веб-приложение лизинга грузовых автомобилей

B2B платформа, связывающая лизингополучателей, лизинговые компании и поставщиков грузовой техники.

## Стек технологий

- **Backend**: Python 3.12, FastAPI, SQLAlchemy (async), PostgreSQL
- **Frontend**: Vue 3, Vite, Pinia, Tailwind CSS, Vue Router
- **Хранилище файлов**: MinIO (S3-совместимое)
- **Контейнеризация**: Docker, Docker Compose

## Быстрый старт

### Через Docker Compose (рекомендуется)

```bash
docker-compose up --build
```

Сервисы:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- MinIO Console: http://localhost:9001

### Локальная разработка

#### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Полный reset и seed тестовых данных

```bash
cd backend
python -m app.scripts.seed_full
```

Если backend запущен в Docker Compose, можно выполнить ту же команду прямо в контейнере:

```bash
docker exec fleetlease-backend python -m app.scripts.seed_full
```

Команда полностью очищает прикладные данные базы и заново создает демонстрационный набор пользователей, банковских счетов и объявлений.

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Deploy to Railway

Для production-развертывания добавлены отдельные Dockerfile, при этом локальная разработка
через `docker-compose` остается без изменений.

### Что деплоим из репозитория

- Backend service: `backend/Dockerfile.railway`
- Frontend service: `frontend/Dockerfile.railway`

`docker-compose.yml` по-прежнему используется только для локального dev-сценария
(`Vite dev server`, hot reload, локальные PostgreSQL + MinIO).

### Инфраструктура в Railway

1. Создайте сервис **PostgreSQL** через Railway plugin.
2. Создайте **S3-compatible Object Storage** (Railway Object Storage).
3. Создайте 2 приложения из этого репозитория:
   - backend (root directory: `backend`, dockerfile path: `Dockerfile.railway`)
   - frontend (root directory: `frontend`, dockerfile path: `Dockerfile.railway`)

### Переменные для backend в Railway

Минимально необходимые:

- `DATABASE_URL` (в формате `postgresql+asyncpg://...`)
- `DATABASE_URL_SYNC` (в формате `postgresql://...`)
- `SECRET_KEY`
- `MINIO_ENDPOINT`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `MINIO_BUCKET`
- `MINIO_ABOUT_BUCKET`
- `MINIO_SECURE=true`
- `MINIO_EXTERNAL_ENDPOINT`
- `CORS_ORIGINS=["https://<frontend-domain>.up.railway.app"]`

Примечания:

- `CORS_ORIGINS` поддерживает как JSON-массив, так и CSV-строку.
- В `MINIO_EXTERNAL_ENDPOINT` можно указывать как полный URL (`https://...`),
  так и host:port (схема будет выбрана по `MINIO_SECURE`).

### Порядок деплоя

1. Сначала задеплойте backend и проверьте `/health`.
2. Затем задеплойте frontend (nginx раздает `dist` и проксирует `/api` на backend).
3. Выполните smoke-test:
   - открывается frontend-домен;
   - SPA-роуты открываются напрямую (без 404);
   - запросы к `/api/v1/*` проходят;
   - загрузка файлов в S3 работает.

Подробный пошаговый runbook: `docs/deploy-railway.md`.

## Ролевая модель

| Роль | Описание |
|------|----------|
| Гость | Просмотр каталога, профилей, калькулятора лизинга |
| Лизингополучатель (client) | Подача заявок, работа с договорами, оплата |
| Лизинговый менеджер (lease_manager) | Рассмотрение заявок, формирование договоров |
| Поставщик (supplier) | Управление каталогом техники |
| Администратор (admin) | Управление пользователями и системой |

## Структура проекта

```
FleetLease/
├── backend/
│   ├── app/
│   │   ├── api/endpoints/    # API роутеры
│   │   ├── core/             # Конфигурация, БД, безопасность
│   │   ├── models/           # SQLAlchemy модели
│   │   ├── schemas/          # Pydantic схемы
│   │   ├── services/         # Бизнес-логика
│   │   └── main.py
│   ├── alembic/              # Миграции БД
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/              # API клиент (axios)
│   │   ├── components/       # Vue компоненты
│   │   ├── views/            # Страницы
│   │   ├── stores/           # Pinia хранилища
│   │   ├── router/           # Vue Router
│   │   └── utils/            # Утилиты
│   └── package.json
└── docker-compose.yml
```
