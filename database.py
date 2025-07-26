from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from contextlib import asynccontextmanager

Base = declarative_base()

DATABASE_URL = "mysql+asyncmy://root:Madaminov27!@localhost:3306/movie_db"

engine = create_async_engine(DATABASE_URL, 
                echo=True,
                pool_recycle=280,
                pool_pre_ping=True
    )

sync_engine = create_engine("mysql+pymysql://root:Madaminov27!@localhost:3306/movie_db")

AsyncSessionLocal = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
SessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def get_sync_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()