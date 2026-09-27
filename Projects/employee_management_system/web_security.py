"""Central browser-response security policy for the ABAP web application."""

from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


CONTENT_SECURITY_POLICY = "; ".join(
    (
        "default-src 'self'",
        "base-uri 'none'",
        "object-src 'none'",
        "frame-ancestors 'none'",
        "form-action 'self'",
        "script-src 'self'",
        "style-src 'self'",
        "img-src 'self' data:",
        "font-src 'self'",
        "connect-src 'self'",
    )
)

PERMISSIONS_POLICY = (
    "camera=(), geolocation=(), microphone=(), payment=(), usb=()"
)

DEVELOPMENT_DOCUMENTATION_PATHS = frozenset(
    {
        "/docs",
        "/docs/oauth2-redirect",
        "/redoc",
        "/openapi.json",
    }
)

SENSITIVE_RESPONSE_ATTRIBUTE = "abap_sensitive_response"


def mark_response_sensitive(request: Request) -> None:
    """Require private, non-persistent caching for the current response."""
    setattr(request.state, SENSITIVE_RESPONSE_ATTRIBUTE, True)


class BrowserSecurityMiddleware(BaseHTTPMiddleware):
    """Apply browser defenses and cache policy consistently to responses."""

    def __init__(self, app, *, development_documentation: bool) -> None:
        super().__init__(app)
        self.development_documentation = development_documentation

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)

        is_development_documentation = (
            self.development_documentation
            and request.url.path in DEVELOPMENT_DOCUMENTATION_PATHS
        )
        if not is_development_documentation:
            response.headers["Content-Security-Policy"] = (
                CONTENT_SECURITY_POLICY
            )

        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = PERMISSIONS_POLICY

        if getattr(
            request.state,
            SENSITIVE_RESPONSE_ATTRIBUTE,
            False,
        ):
            response.headers["Cache-Control"] = "private, no-store"

        return response
