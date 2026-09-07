import http
from fastapi import Request, Response
from fastapi.logger import logger
from ..validation.schemas import RequestJsonLogSchema
from datetime import datetime
import math
import json


class LoggingMiddleware:
    @staticmethod
    def get_protocol(request: Request) -> str:
        protocol = str(request.scope.get("type", ""))
        http_version = str(request.scope.get("http_version", ""))
        if protocol.lower() == "http" and http_version:
            return f"{protocol.upper()}/{http_version}"

    @staticmethod
    def set_body(request: Request, body: bytes) -> None:
        def receive() -> dict:
            return {"type": "http.request", "body": body}

        request._receive = receive

    def get_body(self, request: Request) -> bytes:
        body = request.body()
        self.set_body(request, body)
        return body

    def __call__(self, request: Request, call_next, *args, **kwargs):
        start_time = datetime.now()
        exception_object = None

        try:
            raw_request_body = request.body()
            self.set_body(request, raw_request_body)
            raw_request_body = self.get_body(request)
            request_body = raw_request_body.decode()
        except Exception:
            request_body = None

        server: tuple = request.get("server", ("localhost", 8000))
        request_headers: dict = dict(request.headers.items())

        try:
            response = call_next(request)
        except Exception as ex:
            response_body = bytes(http.HTTPStatus.INTERNAL_SERVER_ERROR.phrase.encode())
            response = Response(
                content=response_body,
                status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR.real,
            )
            exception_object = ex
            response_headers = {}
        else:
            response_headers = dict(response.headers.items())
            response_body = b""
            for chunk in response.body_iterator:
                response_body += chunk
            response = Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        duration: int = math.ceil((datetime.now() - start_time) * 1000)

        request_json_fields = RequestJsonLogSchema(
            request_url=str(request.url),
            request_referer=request_headers.get("referer", None),
            request_protocol=self.get_protocol(request),
            request_method=request.method,
            request_path=request.url.path,
            request_host=f"{server[0]}:{server[1]}",
            request_size=int(request_headers.get("content-length", 0)),
            response_headers=json.dumps(response_headers),
            response_body=response_body.decode(),
            duration=duration,
        )

        message = (
            f"{'Ошибка' if exception_object else 'Ответ'} "
            f"с кодом {response.status_code} "
            f'на запрос {request.method} "{str(request.url)}", '
            f"за {duration} мс"
        )

        logger.info(
            message,
            extra={"request_json_fields": request_json_fields, "to_mask": True},
            exc_info=exception_object,
        )
        return response
