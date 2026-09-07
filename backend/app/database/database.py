from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..config import settings as ss
engine = create_engine(ss.DB_URL)

SessionLocal = sessionmaker(autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
