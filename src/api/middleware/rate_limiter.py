"""
Middleware simple de limitation de débit (Anti Brute-Force).
"""

import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class InMemoryRateLimiterMiddleware(BaseHTTPMiddleware):
    """Limite le nombre de requêtes par minute par IP."""

    def __init__(self, app, max_requests_per_minute: int = 300) -> None:
        super().__init__(app)
        self.max_requests = max_requests_per_minute
        self.requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60

        # Purge des timestamps expirés
        self.requests[client_ip] = [t for t in self.requests[client_ip] if t > window_start]

        if len(self.requests[client_ip]) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": "Trop de requêtes. Veuillez patienter."},
            )

        self.requests[client_ip].append(now)
        return await call_next(request)
