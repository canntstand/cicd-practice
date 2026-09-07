from typing import Any, Callable
from functools import wraps
from psycopg2 import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


def db_exc_check(func: Callable) -> Any:
    @wraps(func)
    async def wrapper(*args, **kwargs):
        db = None
        for arg in args:
            if hasattr(arg, "execute"):
                db = arg
                break

        if not db:
            db = kwargs.get("db")
        try:
            return await func(*args, **kwargs)
        except IntegrityError as e:
            await db.rollback()
            logger.error("Database error", exc_info=e)
            raise HTTPException(400, detail="data integrity error")

        except SQLAlchemyError as e:
            await db.rollback()
            logger.error("Database error", exc_info=e)
            raise HTTPException(500, detail="database operation failed")

        except ValueError as e:
            await db.rollback()
            logger.error("Database error", exc_info=e)
            raise HTTPException(status_code=400, detail=str(e))

    return wrapper
