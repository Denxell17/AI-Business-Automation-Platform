from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


APPLICATION_DIRECTORY = Path(__file__).resolve().parent
TEMPLATES_DIRECTORY = APPLICATION_DIRECTORY / "templates"

templates = Jinja2Templates(
    directory=TEMPLATES_DIRECTORY,
)


def create_web_application() -> FastAPI:
    application = FastAPI(
        title="Employee Management System",
        description=(
            "Web application and API for managing "
            "employee and user-account information."
        ),
        version="1.0.0",
    )

    @application.get(
        "/",
        response_class=HTMLResponse,
    )
    def home_page(request: Request):
        return templates.TemplateResponse(
            request=request,
            name="home.html",
            context={
                "page_title": "Employee Management System",
                "page_message": (
                    "Securely manage workforce information "
                    "through a browser."
                ),
            },
        )

    @application.get("/health")
    def health_check() -> dict[str, str]:
        return {
            "status": "healthy",
        }

    return application


app = create_web_application()