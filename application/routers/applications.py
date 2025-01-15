from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import SessionLocal
from kafka_producer import send_to_kafka
from models import Application
from schemas import ApplicationResponse, ApplicationCreate

router = APIRouter(prefix="/applications", tags=["Applications"])

async def get_db():
    async with SessionLocal() as session:
        yield session

@router.post("/", response_model=ApplicationResponse)
async def create_application(
    application: ApplicationCreate, db: AsyncSession = Depends(get_db)
):
    new_application = Application(**application.dict())
    db.add(new_application)
    try:
        await db.commit()
        await db.refresh(new_application)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    await send_to_kafka("applications", {
        "id": new_application.id,
        "user_name": new_application.user_name,
        "description": new_application.description,
        "created_at": new_application.created_at.isoformat(),
    })
    return new_application

@router.get("/", response_model=list[ApplicationResponse])
async def list_applications(
    user_name: str = None, page: int = 1, size: int = 10, db: AsyncSession = Depends(get_db)
):
    query = select(Application)
    if user_name:
        query = query.filter(Application.user_name == user_name)
    query = query.offset((page - 1) * size).limit(size)
    results = await db.execute(query)
    return results.scalars().all()