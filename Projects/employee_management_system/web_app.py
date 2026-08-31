import secrets
from pathlib import Path
from typing import Annotated

from fastapi import (
    FastAPI,
    Form,
    Request,
)
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
    Response,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from activity_logger import log_activity
from authorization import (
    VIEW_EMPLOYEE,
    user_has_permission,
)
from database import DATABASE_FILE
from employee_repository import load_employee_records
from user_service import authenticate_user_account
from web_session import (
    begin_authenticated_session,
    clear_authenticated_session,
    load_authenticated_session_user,
)


APPLICATION_DIRECTORY = Path(__file__).resolve().parent
TEMPLATES_DIRECTORY = APPLICATION_DIRECTORY / "templates"
STATIC_DIRECTORY = APPLICATION_DIRECTORY / "static"

SESSION_COOKIE_NAME = "abap_session"
SESSION_MAX_AGE_SECONDS = 8 * 60 * 60
LOGIN_FAILURE_MESSAGE = (
    "Username or password is incorrect."
)

templates = Jinja2Templates(
    directory=TEMPLATES_DIRECTORY,
)


def create_web_application(
    database_file: Path = DATABASE_FILE,
    session_secret: str | None = None,
    secure_cookies: bool = False,
) -> FastAPI:
    application = FastAPI(
        title="Employee Management System",
        description=(
            "Web application and API for managing "
            "employee and user-account information."
        ),
        version="1.0.0",
    )

    application.add_middleware(
        SessionMiddleware,
        secret_key=(
            session_secret
            if session_secret is not None
            else secrets.token_urlsafe(32)
        ),
        session_cookie=SESSION_COOKIE_NAME,
        max_age=SESSION_MAX_AGE_SECONDS,
        same_site="lax",
        https_only=secure_cookies,
    )

    application.mount(
        "/static",
        StaticFiles(directory=STATIC_DIRECTORY),
        name="static",
    )

    @application.get(
        "/login",
        response_class=HTMLResponse,
    )
    def login_page(request: Request) -> Response:
        current_user = load_authenticated_session_user(
            request,
            database_file,
        )

        if current_user is not None:
            return RedirectResponse(
                url=request.url_for("home_page"),
                status_code=303,
            )

        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "page_title": "Sign in",
                "entered_username": "",
                "error_message": None,
            },
        )

    @application.post(
        "/login",
        response_class=HTMLResponse,
    )
    def login_submission(
        request: Request,
        username: Annotated[str, Form()],
        password: Annotated[str, Form()],
    ) -> Response:
        entered_username = username.strip()

        user_account = authenticate_user_account(
            entered_username,
            password,
            database_file,
        )

        if user_account is None:
            log_activity("Failed web login attempt.")

            return templates.TemplateResponse(
                request=request,
                name="login.html",
                context={
                    "page_title": "Sign in",
                    "entered_username": entered_username,
                    "error_message": LOGIN_FAILURE_MESSAGE,
                },
                status_code=401,
            )

        begin_authenticated_session(
            request,
            user_account,
        )
        log_activity(
            f"User {user_account['username']} "
            "logged in through the web application."
        )

        return RedirectResponse(
            url=request.url_for("home_page"),
            status_code=303,
        )

    @application.post("/logout")
    def logout(request: Request) -> Response:
        current_user = load_authenticated_session_user(
            request,
            database_file,
        )

        clear_authenticated_session(request)

        if current_user is not None:
            log_activity(
                f"User {current_user['username']} "
                "logged out of the web application."
            )

        return RedirectResponse(
            url=request.url_for("login_page"),
            status_code=303,
        )

    @application.get(
        "/",
        response_class=HTMLResponse,
    )
    def home_page(request: Request) -> Response:
        current_user = load_authenticated_session_user(
            request,
            database_file,
        )

        if current_user is None:
            return RedirectResponse(
                url=request.url_for("login_page"),
                status_code=303,
            )

        return templates.TemplateResponse(
            request=request,
            name="home.html",
            context={
                "page_title": "Employee Management System",
                "page_message": (
                    "Securely manage workforce information "
                    "through a browser."
                ),
                "active_page": "home",
                "current_user": current_user,
            },
        )

    @application.get(
        "/employees",
        response_class=HTMLResponse,
    )
    def employee_directory(request: Request) -> Response:
        current_user = load_authenticated_session_user(
            request,
            database_file,
        )

        if current_user is None:
            return RedirectResponse(
                url=request.url_for("login_page"),
                status_code=303,
            )

        if not user_has_permission(
            current_user,
            VIEW_EMPLOYEE,
        ):
            log_activity(
                f"Web employee-directory access denied "
                f"for user {current_user['username']}."
            )
            return HTMLResponse(
                content="Access denied.",
                status_code=403,
            )

        employee_list = load_employee_records(
            database_file=database_file,
        )

        if employee_list is None:
            return templates.TemplateResponse(
                request=request,
                name="employees.html",
                context={
                    "page_title": "Employee directory",
                    "active_page": "employees",
                    "current_user": current_user,
                    "employee_list": [],
                    "error_message": (
                        "Employee records could not be loaded."
                    ),
                },
                status_code=500,
            )

        return templates.TemplateResponse(
            request=request,
            name="employees.html",
            context={
                "page_title": "Employee directory",
                "active_page": "employees",
                "current_user": current_user,
                "employee_list": employee_list,
                "error_message": None,
            },
        )

    @application.get("/health")
    def health_check() -> dict[str, str]:
        return {
            "status": "healthy",
        }

    return application


app = create_web_application()
