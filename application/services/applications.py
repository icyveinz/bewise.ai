from core.schemas import ApplicationCreate
from repositories.applications import ApplicationRepository
from sqlalchemy.ext.asyncio import AsyncSession
from services.kafka_service import send_to_kafka


async def create_application(application_data: ApplicationCreate, db: AsyncSession):
    application = await ApplicationRepository.create(db, application_data)
    # Отправка в Kafka
    await send_to_kafka("applications", {
        "id": application.id,
        "user_name": application.user_name,
        "description": application.description,
        "created_at": application.created_at.isoformat(),
    })
    return application

async def list_applications(user_name: str, page: int, size: int, db: AsyncSession):
    offset = (page - 1) * size
    return await ApplicationRepository.list(db, user_name, offset, size)
