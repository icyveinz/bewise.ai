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
