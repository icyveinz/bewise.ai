from fastapi import FastAPI
from routers import applications
from lifespan.lifespan import lifespan

app = FastAPI(lifespan=lifespan)

app.include_router(applications.router)


@app.get("/")
async def root():
    return {"message": "Service is running"}
