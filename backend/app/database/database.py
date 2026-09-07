from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from ..config import settings as ss

engine = create_async_engine(
    ss.DB_URL.replace("postgresql://", "postgresql+asyncpg://")
)

SessionLocal = async_sessionmaker(autoflush=False, bind=engine)


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()
