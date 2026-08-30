import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from loguru import logger

# 日志中间件：记录请求和响应日志
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        logger.info(f"--> {request.method} {request.url.path}")
        # 放行
        response = await call_next(request)

        elapsed = (time.perf_counter() - start) * 1000
        logger.info(
            f"<-- {request.method} {request.url.path} "
            f"status={response.status_code} {elapsed:.2f}ms"
        )
        return response