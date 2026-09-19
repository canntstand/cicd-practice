import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import HTTPException
from psycopg2 import IntegrityError
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


def db_exc_check(func: Callable) -> Any:
    @wraps(func)
    def wrapper(*args, **kwargs):
        db = None
        for arg in args:
            if hasattr(arg, "execute"):
                db = arg
                break

        if not db:
            db = kwargs.get("db")
        try:
            return func(*args, **kwargs)
        except IntegrityError as e:
            db.rollback()
            logger.error("Database error", exc_info=e)
            raise HTTPException(400, detail="data integrity error")

        except SQLAlchemyError as e:
            db.rollback()
            logger.error("Database error", exc_info=e)
            raise HTTPException(500, detail="database operation failed")

        except ValueError as e:
            db.rollback()
            logger.error("Database error", exc_info=e)
            raise HTTPException(status_code=400, detail=str(e))

    return wrapper
