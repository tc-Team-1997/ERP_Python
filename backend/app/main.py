from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.router import api_router
from backend.app.core.config import settings
from backend.app.db.base import Base
from backend.app.db.session import engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Multi-tenant Business Automation SaaS — Payroll, Invoicing & Expense Management.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {
        "message": "Business Automation SaaS API is running",
        "modules": ["Payroll", "Invoicing", "Expenses"],
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(api_router, prefix=settings.api_v1_prefix)
