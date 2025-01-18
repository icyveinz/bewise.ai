# Проект: FastAPI приложение с интеграцией PostgreSQL и Kafka

Этот проект представляет собой FastAPI приложение, которое взаимодействует с базой данных PostgreSQL и отправляет сообщения в Kafka. Проект включает в себя CI/CD пайплайн для автоматического форматирования кода, Docker-контейнеризацию, а также использование Nginx в качестве прокси-сервера.

## Запуск проекта

1. Убедитесь, что у вас установлены Docker и Docker Compose.

2. Соберите и запустите контейнеры:

   ```bash
   docker-compose up --build
   ```
3. Приложение будет доступно по адресу http://localhost:8000.

## Генерация `requirements.txt`

Для генерации файла `requirements.txt` используйте команду:

```bash
make generate
```

## Структура проекта

### `.github/workflows/ci.yml`

Этот файл определяет CI/CD пайплайн, который автоматически форматирует код с помощью Black при каждом пуше или пул-реквесте в ветку `main`.

```yaml
name: CI

on:
  push:
    branches: ["main"]
  pull_request:
    branches: ["main"]

jobs:
  formatter:
    runs-on: ubuntu-latest
    permissions:
      contents: write  # Grant write permissions to the GITHUB_TOKEN
    steps:
      # Check out the repository
      - name: Checkout code
        uses: actions/checkout@v3

      # Set up Python
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.9"  # Replace with your desired Python version

      # Install Black
      - name: Install Black
        run: pip install black

      # Run Black to format the code
      - name: Run Black
        run: black .

      # Check if there are any changes after formatting
      - name: Check for changes
        id: changes
        run: |
          git diff --exit-code || echo "::set-output name=changes::true"

      # Commit changes if there are any
      - name: Commit auto-fixes
        if: steps.changes.outputs.changes == 'true'
        run: |
          git config --global user.name "GitHub Actions"
          git config --global user.email "actions@github.com"
          git add .
          git commit -m "Apply Black formatting [skip ci]" || echo "No changes to commit"
          git push
```
### `Dockerfile`

Dockerfile для контейнеризации приложения. Используется образ Python 3.9, устанавливаются необходимые зависимости и запускается приложение.

```dockerfile
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install PostgreSQL client tools (including pg_isready)
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /application

# Copy the current directory contents into the container at /application
COPY . /application

# Make sure the wait-for-db.sh script is executable
RUN chmod +x /application/wait-for-db.sh

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set the PYTHONPATH environment variable
ENV PYTHONPATH=/application

# Run the wait-for-db.sh script and then the application
ENTRYPOINT ["/application/wait-for-db.sh", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### `main.py`

Основной файл приложения, который инициализирует FastAPI и подключает роутеры.

```python
from fastapi import FastAPI
from routers import applications
from lifespan.lifespan import lifespan

app = FastAPI(lifespan=lifespan)

app.include_router(applications.router)


@app.get("/")
async def root():
    return {"message": "Service is running"}
```

### `Makefile`

Makefile для удобного управления проектом. Включает команды для запуска приложения, генерации `requirements.txt` и проверки кода с помощью Ruff.

```makefile
HOST ?= localhost
PORT ?= 8001

run:
	uvicorn main:app --host ${HOST} --port ${PORT} --reload
generate:
	pip freeze > requirements.txt
check:
	ruff check . --fix
```

### `wait-for-db.sh`

Скрипт для ожидания готовности PostgreSQL перед запуском приложения.

```bash
#!/bin/bash

# Wait until PostgreSQL is ready
until pg_isready -h db -p 5432 -U user -d applications_db; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 2
done

echo "PostgreSQL is ready. Starting the application..."
exec "$@"
```

### `core/database.py`

Модуль для работы с базой данных. Используется SQLAlchemy для асинхронного взаимодействия с PostgreSQL.

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import OperationalError
import asyncio

DATABASE_URL = "postgresql+asyncpg://user:password@db:5432/applications_db"

engine = create_async_engine(DATABASE_URL)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


async def init_db():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database initialized successfully")
    except OperationalError as e:
        print(f"Failed to initialize the database: {e}")
        raise
```

### `core/models.py`

Модели SQLAlchemy для таблиц в базе данных.

```python
from sqlalchemy import Column, Integer, String, DateTime, func
from core.database import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
```

### `core/schemas.py`

Pydantic схемы для валидации данных.

```python
from pydantic import BaseModel
from datetime import datetime


class ApplicationCreate(BaseModel):
    user_name: str
    description: str


class ApplicationResponse(ApplicationCreate):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
```

### `lifespan/lifespan.py`

Контекстный менеджер для управления жизненным циклом приложения, включая инициализацию базы данных.

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        print("Starting up: Initializing the database")
        await init_db()  # Initialize the database
        print("Database initialization completed")
        yield  # Control is handed over to the app
    except Exception as e:
        print(f"Error during startup: {e}")
        raise
    finally:
        print("Shutting down: Perform cleanup if necessary")
```

### `repositories/applications.py`

Репозиторий для работы с данными заявок.

```python
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.models import Application
from core.schemas import ApplicationCreate


class ApplicationRepository:
    @staticmethod
    async def create(
        db: AsyncSession, application_data: ApplicationCreate
    ) -> Application:
        new_application = Application(
            user_name=application_data.user_name,
            description=application_data.description,
        )
        db.add(new_application)
        await db.commit()
        await db.refresh(new_application)
        return new_application

    @staticmethod
    async def list(
        db: AsyncSession, user_name: str = None, offset: int = 0, limit: int = 10
    ):
        query = select(Application)
        if user_name:
            query = query.filter(Application.user_name == user_name)
        query = query.offset(offset).limit(limit)
        results = await db.execute(query)
        return results.scalars().all()
```

### `routers/applications.py`

Роутеры FastAPI для обработки запросов, связанных с заявками.

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import SessionLocal
from core.schemas import ApplicationResponse, ApplicationCreate
from services.applications import create_application, list_applications

router = APIRouter(prefix="/applications", tags=["Applications"])


async def get_db():
    async with SessionLocal() as session:
        yield session


@router.post("/", response_model=ApplicationResponse)
async def create(application: ApplicationCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await create_application(application, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[ApplicationResponse])
async def list(
    user_name: str = None,
    page: int = 1,
    size: int = 10,
    db: AsyncSession = Depends(get_db),
):
    return await list_applications(user_name, page, size, db)
```

### `services/applications.py`

Сервисный слой для работы с заявками, включая отправку данных в Kafka.

```python
from core.schemas import ApplicationCreate
from repositories.applications import ApplicationRepository
from sqlalchemy.ext.asyncio import AsyncSession
from services.kafka_service import send_to_kafka


async def create_application(application_data: ApplicationCreate, db: AsyncSession):
    application = await ApplicationRepository.create(db, application_data)
    # Отправка в Kafka
    await send_to_kafka(
        "applications",
        {
            "id": application.id,
            "user_name": application.user_name,
            "description": application.description,
            "created_at": application.created_at.isoformat(),
        },
    )
    return application


async def list_applications(user_name: str, page: int, size: int, db: AsyncSession):
    offset = (page - 1) * size
    return await ApplicationRepository.list(db, user_name, offset, size)
```

### `services/kafka_service.py`

Сервис для отправки сообщений в Kafka.

```python
from aiokafka import AIOKafkaProducer
import json

producer = None


async def get_producer():
    global producer
    if producer is None:
        producer = AIOKafkaProducer(bootstrap_servers="kafka:9092")
        await producer.start()
    return producer


async def send_to_kafka(topic: str, message: dict):
    producer = await get_producer()
    await producer.send_and_wait(topic, json.dumps(message).encode("utf-8"))
```

### `nginx/Dockerfile`

Dockerfile для Nginx, который используется в качестве прокси-сервера.

```dockerfile
FROM nginx:mainline-alpine3.20-slim
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

### `nginx/nginx.conf`

Конфигурация Nginx для проксирования запросов к FastAPI приложению.

```nginx
server {
    listen 8000;
    server_name null.null;
    location / {
        proxy_pass http://application:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```