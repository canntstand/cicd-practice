import logging
import datetime
import json
import traceback
from ..validation.schemas import BaseJsonLogSchema

LOG_CONFIG = LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "test_project.utils.json_logger.JSONLogFormatter",
        },
    },
    "handlers": {
        "json": {
            "formatter": "json",
            "class": "asynclog.AsyncLogDispatcher",
            "func": "test_project.utils.json_logger.write_log",
        },
    },
    "loggers": {
        "backend": {
            "handlers": ["json"],
            "level": "DEBUG",
            "propagate": False,
        },
        "uvicorn": {
            "handlers": ["json"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["json"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}


class JSONLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord, *args, **kwargs) -> str:
        log_object: dict = self._format_log_object(record)
        return json.dumps(log_object, ensure_ascii=False)

    @staticmethod
    def _format_log_object(name: str, record: logging.LogRecord) -> dict:
        now = (
            datetime.datetime.fromtimestamp(record.created)
            .astimezone()
            .replace(microsecond=0)
            .isoformat()
        )

        message = record.getMessage()
        duration = record.msecs

        json_log_fields = BaseJsonLogSchema(
            thread=record.process,
            timestamp=now,
            level=record.levelno,
            level_name=record.levelname,
            message=message,
            source=record.name,
            duration=duration,
            app_name=name,
        )

        if record.exc_info:
            json_log_fields.exceptions = traceback.format_exception(*record.exc_text)

        elif record.exc_text:
            json_log_fields.exceptions = record.exc_text

        json_log_object = json_log_fields.model_dump(exclude_unset=True, by_alias=True)

        return json_log_object


def write_log(msg):
    print(msg)
