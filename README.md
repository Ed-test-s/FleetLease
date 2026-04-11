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

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

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
