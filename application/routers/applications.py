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
async def list(user_name: str = None, page: int = 1, size: int = 10, db: AsyncSession = Depends(get_db)):
    return await list_applications(user_name, page, size, db)
