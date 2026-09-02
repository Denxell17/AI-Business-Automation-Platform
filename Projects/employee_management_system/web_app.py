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
    DELETE_EMPLOYEE,
    REGISTER_EMPLOYEE,
    UPDATE_EMPLOYEE,
    VIEW_EMPLOYEE,
    VIEW_PAYROLL,
    user_has_permission,
)
from database import DATABASE_FILE
from data_validation import get_employee_record_errors
from employee_repository import (
    load_employee_records,
    save_employee_records,
)
from employee_service import (
    filter_employees_by_department,
    filter_employees_by_salary_range,
    find_employee_by_id,
    remove_employee,
    search_employees_by_name,
    sort_employees_by_name,
    sort_employees_by_salary,
    update_employee_contact_details,
    update_employee_details,
)
from payroll import calculate_payroll
from models import Employee
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

CSRF_SESSION_KEY = "csrf_token"


def get_or_create_csrf_token(request: Request) -> str:
    csrf_token = request.session.get(CSRF_SESSION_KEY)

    if not isinstance(csrf_token, str):
        csrf_token = secrets.token_urlsafe(32)
        request.session[CSRF_SESSION_KEY] = csrf_token

    return csrf_token


def csrf_token_is_valid(
    request: Request,
    submitted_token: str,
) -> bool:
    session_token = request.session.get(CSRF_SESSION_KEY)

    if not isinstance(session_token, str):
        return False

    return secrets.compare_digest(
        session_token,
        submitted_token,
    )


def build_employee_from_form(
    employee_id: str,
    name: str,
    department: str,
    position: str,
    country: str,
    salary: str,
    email: str,
    phone_number: str,
    years_of_experience: str,
    company: str,
    employment_status: str,
    performance_score: str,
) -> tuple[dict[str, str], Employee | None, str | None]:
    form_values = {
        "employee_id": employee_id.strip().upper(),
        "name": name.strip(),
        "department": department.strip(),
        "position": position.strip(),
        "country": country.strip(),
        "salary": salary.strip(),
        "email": email.strip(),
        "phone_number": phone_number.strip(),
        "years_of_experience": years_of_experience.strip(),
        "company": company.strip(),
        "employment_status": employment_status.strip(),
        "performance_score": performance_score.strip(),
    }

    try:
        employee: Employee = {
            "employee_id": form_values["employee_id"],
            "name": form_values["name"],
            "department": form_values["department"],
            "position": form_values["position"],
            "country": form_values["country"],
            "salary": int(form_values["salary"]),
            "email": form_values["email"],
            "phone_number": form_values["phone_number"],
            "years_of_experience": int(
                form_values["years_of_experience"]
            ),
            "company": form_values["company"],
            "employment_status": form_values[
                "employment_status"
            ],
            "performance_score": int(
                form_values["performance_score"]
            ),
        }
    except ValueError:
        return (
            form_values,
            None,
            "Salary, years of experience, and performance "
            "score must be whole numbers.",
        )

    validation_errors = get_employee_record_errors(employee)

    if employee["years_of_experience"] > 60:
        validation_errors.append(
            "Years of experience must be between 0 and 60."
        )

    if validation_errors:
        return (
            form_values,
            None,
            " ".join(validation_errors),
        )

    return form_values, employee, None


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
        "/employees/new",
        response_class=HTMLResponse,
    )
    def employee_create_form(request: Request) -> Response:
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
            REGISTER_EMPLOYEE,
        ):
            log_activity(
                "User "
                f"{current_user['username']} was denied "
                "web employee-registration access."
            )
            return Response(
                content="Employee registration access is denied.",
                status_code=403,
            )

        return templates.TemplateResponse(
            request=request,
            name="employee_form.html",
            context={
                "page_title": "Add employee",
                "active_page": "employees",
                "current_user": current_user,
                "csrf_token": get_or_create_csrf_token(
                    request
                ),
                "form_values": {},
                "error_message": None,
            },
        )

    @application.post("/employees/new")
    def employee_create(
        request: Request,
        csrf_token: Annotated[str, Form()],
        employee_id: Annotated[str, Form()],
        name: Annotated[str, Form()],
        department: Annotated[str, Form()],
        position: Annotated[str, Form()],
        country: Annotated[str, Form()],
        salary: Annotated[str, Form()],
        email: Annotated[str, Form()],
        phone_number: Annotated[str, Form()],
        years_of_experience: Annotated[str, Form()],
        company: Annotated[str, Form()],
        employment_status: Annotated[str, Form()],
        performance_score: Annotated[str, Form()],
    ) -> Response:
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
            REGISTER_EMPLOYEE,
        ):
            log_activity(
                "User "
                f"{current_user['username']} was denied "
                "web employee-registration access."
            )
            return Response(
                content="Employee registration access is denied.",
                status_code=403,
            )

        if not csrf_token_is_valid(request, csrf_token):
            log_activity(
                "User "
                f"{current_user['username']} submitted an "
                "invalid employee-registration CSRF token."
            )
            return Response(
                content="Your form could not be verified.",
                status_code=403,
            )

        (
            form_values,
            employee,
            validation_error,
        ) = build_employee_from_form(
            employee_id,
            name,
            department,
            position,
            country,
            salary,
            email,
            phone_number,
            years_of_experience,
            company,
            employment_status,
            performance_score,
        )

        if validation_error is not None:
            return templates.TemplateResponse(
                request=request,
                name="employee_form.html",
                context={
                    "page_title": "Add employee",
                    "active_page": "employees",
                    "current_user": current_user,
                    "csrf_token": get_or_create_csrf_token(
                        request
                    ),
                    "form_values": form_values,
                    "error_message": validation_error,
                },
                status_code=400,
            )

        employee_list = load_employee_records(
            database_file=database_file,
        )

        if employee_list is None:
            return templates.TemplateResponse(
                request=request,
                name="employee_form.html",
                context={
                    "page_title": "Add employee",
                    "active_page": "employees",
                    "current_user": current_user,
                    "csrf_token": get_or_create_csrf_token(
                        request
                    ),
                    "form_values": form_values,
                    "error_message": (
                        "Employee records could not be loaded. "
                        "Please try again later."
                    ),
                },
                status_code=500,
            )

        existing_employee = find_employee_by_id(
            employee_list,
            employee["employee_id"],
        )

        if existing_employee is not None:
            return templates.TemplateResponse(
                request=request,
                name="employee_form.html",
                context={
                    "page_title": "Add employee",
                    "active_page": "employees",
                    "current_user": current_user,
                    "csrf_token": get_or_create_csrf_token(
                        request
                    ),
                    "form_values": form_values,
                    "error_message": (
                        "An employee with that ID already exists."
                    ),
                },
                status_code=400,
            )

        employee_list.append(employee)

        if not save_employee_records(
            employee_list,
            database_file=database_file,
        ):
            return templates.TemplateResponse(
                request=request,
                name="employee_form.html",
                context={
                    "page_title": "Add employee",
                    "active_page": "employees",
                    "current_user": current_user,
                    "csrf_token": get_or_create_csrf_token(
                        request
                    ),
                    "form_values": form_values,
                    "error_message": (
                        "Employee could not be saved. "
                        "Please try again later."
                    ),
                },
                status_code=500,
            )

        log_activity(
            f"User {current_user['username']} registered "
            f"employee {employee['employee_id']} through "
            "the web application."
        )

        return RedirectResponse(
            url=request.url_for(
                "employee_profile",
                employee_id=employee["employee_id"],
            ),
            status_code=303,
        )

    @application.get(
        "/employees",
        response_class=HTMLResponse,
    )
    def employee_directory(
        request: Request,
        search_text: str = "",
        department: str = "",
        minimum_salary: str = "",
        maximum_salary: str = "",
        sort_by: str = "",
    ) -> Response:
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

        search_text = search_text.strip()
        department = department.strip()
        minimum_salary = minimum_salary.strip()
        maximum_salary = maximum_salary.strip()
        sort_by = sort_by.strip().casefold()

        if sort_by not in ("", "name", "salary"):
            sort_by = ""

        minimum_salary_value: int | None = None
        maximum_salary_value: int | None = None
        filter_error: str | None = None

        if bool(minimum_salary) != bool(maximum_salary):
            filter_error = (
                "Enter both minimum and maximum salary values."
            )
        elif minimum_salary and maximum_salary:
            try:
                minimum_salary_value = int(minimum_salary)
                maximum_salary_value = int(maximum_salary)
            except ValueError:
                filter_error = (
                    "Salary values must be whole numbers."
                )
            else:
                if (
                    minimum_salary_value < 0
                    or maximum_salary_value < 0
                ):
                    filter_error = (
                        "Salary values cannot be negative."
                    )
                elif minimum_salary_value > maximum_salary_value:
                    filter_error = (
                        "Minimum salary cannot exceed "
                        "maximum salary."
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
                    "can_register_employee": (
                        user_has_permission(
                            current_user,
                            REGISTER_EMPLOYEE,
                        )
                    ),
                    "employee_list": [],
                    "filter_values": {
                        "search_text": search_text,
                        "department": department,
                        "minimum_salary": minimum_salary,
                        "maximum_salary": maximum_salary,
                        "sort_by": sort_by,
                    },
                    "filter_error": filter_error,
                    "filters_applied": any(
                        (
                            search_text,
                            department,
                            minimum_salary,
                            maximum_salary,
                            sort_by,
                        )
                    ),
                    "error_message": (
                        "Employee records could not be loaded."
                    ),
                },
                status_code=500,
            )

        filtered_employee_list = employee_list

        if filter_error is None:
            if search_text:
                filtered_employee_list = search_employees_by_name(
                    filtered_employee_list,
                    search_text,
                )

            if department:
                filtered_employee_list = (
                    filter_employees_by_department(
                        filtered_employee_list,
                        department,
                    )
                )

            if (
                minimum_salary_value is not None
                and maximum_salary_value is not None
            ):
                filtered_employee_list = (
                    filter_employees_by_salary_range(
                        filtered_employee_list,
                        minimum_salary_value,
                        maximum_salary_value,
                    )
                )

        if sort_by == "name":
            filtered_employee_list = sort_employees_by_name(
                filtered_employee_list
            )
        elif sort_by == "salary":
            filtered_employee_list = sort_employees_by_salary(
                filtered_employee_list
            )

        filter_values = {
            "search_text": search_text,
            "department": department,
            "minimum_salary": minimum_salary,
            "maximum_salary": maximum_salary,
            "sort_by": sort_by,
        }

        filters_applied = any(filter_values.values())

        return templates.TemplateResponse(
            request=request,
            name="employees.html",
            context={
                "page_title": "Employee directory",
                "active_page": "employees",
                "current_user": current_user,
                "can_register_employee": (
                    user_has_permission(
                        current_user,
                        REGISTER_EMPLOYEE,
                    )
                ),
                "employee_list": filtered_employee_list,
                "filter_values": filter_values,
                "filter_error": filter_error,
                "filters_applied": filters_applied,
                "error_message": None,
            },
        )

    @application.get(
        "/employees/{employee_id}/delete",
        response_class=HTMLResponse,
    )
    def employee_delete_confirmation(
        request: Request,
        employee_id: str,
    ) -> Response:
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
            DELETE_EMPLOYEE,
        ):
            log_activity(
                f"Web employee-deletion access denied "
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
                name="employee_delete.html",
                context={
                    "page_title": "Delete employee",
                    "active_page": "employees",
                    "current_user": current_user,
                    "employee": None,
                    "csrf_token": get_or_create_csrf_token(
                        request
                    ),
                    "error_message": (
                        "Employee records could not be loaded."
                    ),
                },
                status_code=500,
            )

        employee = find_employee_by_id(
            employee_list,
            employee_id,
        )

        if employee is None:
            return templates.TemplateResponse(
                request=request,
                name="employee_delete.html",
                context={
                    "page_title": "Employee not found",
                    "active_page": "employees",
                    "current_user": current_user,
                    "employee": None,
                    "csrf_token": get_or_create_csrf_token(
                        request
                    ),
                    "error_message": (
                        "The requested employee record "
                        "was not found."
                    ),
                },
                status_code=404,
            )

        return templates.TemplateResponse(
            request=request,
            name="employee_delete.html",
            context={
                "page_title": f"Delete {employee['name']}",
                "active_page": "employees",
                "current_user": current_user,
                "employee": employee,
                "csrf_token": get_or_create_csrf_token(
                    request
                ),
                "error_message": None,
            },
        )

    @application.post("/employees/{employee_id}/delete")
    def employee_delete(
        request: Request,
        employee_id: str,
        csrf_token: Annotated[str, Form()],
    ) -> Response:
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
            DELETE_EMPLOYEE,
        ):
            log_activity(
                f"Web employee-deletion access denied "
                f"for user {current_user['username']}."
            )
            return HTMLResponse(
                content="Access denied.",
                status_code=403,
            )

        if not csrf_token_is_valid(request, csrf_token):
            log_activity(
                f"User {current_user['username']} submitted an "
                "invalid employee-deletion CSRF token."
            )
            return Response(
                content="Your form could not be verified.",
                status_code=403,
            )

        employee_list = load_employee_records(
            database_file=database_file,
        )

        if employee_list is None:
            return templates.TemplateResponse(
                request=request,
                name="employee_delete.html",
                context={
                    "page_title": "Delete employee",
                    "active_page": "employees",
                    "current_user": current_user,
                    "employee": None,
                    "csrf_token": get_or_create_csrf_token(
                        request
                    ),
                    "error_message": (
                        "Employee records could not be loaded."
                    ),
                },
                status_code=500,
            )

        employee = find_employee_by_id(
            employee_list,
            employee_id,
        )

        if employee is None:
            return templates.TemplateResponse(
                request=request,
                name="employee_delete.html",
                context={
                    "page_title": "Employee not found",
                    "active_page": "employees",
                    "current_user": current_user,
                    "employee": None,
                    "csrf_token": get_or_create_csrf_token(
                        request
                    ),
                    "error_message": (
                        "The requested employee record "
                        "was not found."
                    ),
                },
                status_code=404,
            )

        if not remove_employee(employee_list, employee):
            return templates.TemplateResponse(
                request=request,
                name="employee_delete.html",
                context={
                    "page_title": "Delete employee",
                    "active_page": "employees",
                    "current_user": current_user,
                    "employee": employee,
                    "csrf_token": get_or_create_csrf_token(
                        request
                    ),
                    "error_message": (
                        "Employee could not be deleted."
                    ),
                },
                status_code=500,
            )

        if not save_employee_records(
            employee_list,
            database_file=database_file,
        ):
            return templates.TemplateResponse(
                request=request,
                name="employee_delete.html",
                context={
                    "page_title": f"Delete {employee['name']}",
                    "active_page": "employees",
                    "current_user": current_user,
                    "employee": employee,
                    "csrf_token": get_or_create_csrf_token(
                        request
                    ),
                    "error_message": (
                        "Employee deletion could not be saved. "
                        "Please try again later."
                    ),
                },
                status_code=500,
            )

        log_activity(
            f"User {current_user['username']} deleted "
            f"employee {employee['employee_id']} through "
            "the web application."
        )

        return RedirectResponse(
            url=request.url_for("employee_directory"),
            status_code=303,
        )

    @application.get(
        "/employees/{employee_id}/edit",
        response_class=HTMLResponse,
    )
    def employee_edit_form(
        request: Request,
        employee_id: str,
    ) -> Response:
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
            UPDATE_EMPLOYEE,
        ):
            log_activity(
                f"Web employee-update access denied "
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
                name="employee_edit.html",
                context={
                    "page_title": "Edit employee",
                    "active_page": "employees",
                    "current_user": current_user,
                    "employee": None,
                    "form_values": {},
                    "csrf_token": get_or_create_csrf_token(
                        request
                    ),
                    "error_message": (
                        "Employee records could not be loaded."
                    ),
                },
                status_code=500,
            )

        employee = find_employee_by_id(
            employee_list,
            employee_id,
        )

        if employee is None:
            return templates.TemplateResponse(
                request=request,
                name="employee_edit.html",
                context={
                    "page_title": "Employee not found",
                    "active_page": "employees",
                    "current_user": current_user,
                    "employee": None,
                    "form_values": {},
                    "csrf_token": get_or_create_csrf_token(
                        request
                    ),
                    "error_message": (
                        "The requested employee record "
                        "was not found."
                    ),
                },
                status_code=404,
            )

        return templates.TemplateResponse(
            request=request,
            name="employee_edit.html",
            context={
                "page_title": f"Edit {employee['name']}",
                "active_page": "employees",
                "current_user": current_user,
                "employee": employee,
                "form_values": {
                    "department": employee["department"],
                    "position": employee["position"],
                    "email": employee["email"],
                    "phone_number": employee["phone_number"],
                },
                "csrf_token": get_or_create_csrf_token(
                    request
                ),
                "error_message": None,
            },
        )

    @application.post("/employees/{employee_id}/edit")
    def employee_update(
        request: Request,
        employee_id: str,
        csrf_token: Annotated[str, Form()],
        department: Annotated[str, Form()],
        position: Annotated[str, Form()],
        email: Annotated[str, Form()],
        phone_number: Annotated[str, Form()],
    ) -> Response:
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
            UPDATE_EMPLOYEE,
        ):
            log_activity(
                f"Web employee-update access denied "
                f"for user {current_user['username']}."
            )
            return HTMLResponse(
                content="Access denied.",
                status_code=403,
            )

        if not csrf_token_is_valid(request, csrf_token):
            log_activity(
                f"User {current_user['username']} submitted an "
                "invalid employee-update CSRF token."
            )
            return Response(
                content="Your form could not be verified.",
                status_code=403,
            )

        form_values = {
            "department": department.strip(),
            "position": position.strip(),
            "email": email.strip(),
            "phone_number": phone_number.strip(),
        }

        if not all(form_values.values()):
            return templates.TemplateResponse(
                request=request,
                name="employee_edit.html",
                context={
                    "page_title": "Edit employee",
                    "active_page": "employees",
                    "current_user": current_user,
                    "employee": {
                        "employee_id": employee_id.strip().upper(),
                        "name": "Employee",
                    },
                    "form_values": form_values,
                    "csrf_token": get_or_create_csrf_token(
                        request
                    ),
                    "error_message": (
                        "Department, position, email, and phone "
                        "number are required."
                    ),
                },
                status_code=400,
            )

        employee_list = load_employee_records(
            database_file=database_file,
        )

        if employee_list is None:
            return templates.TemplateResponse(
                request=request,
                name="employee_edit.html",
                context={
                    "page_title": "Edit employee",
                    "active_page": "employees",
                    "current_user": current_user,
                    "employee": None,
                    "form_values": form_values,
                    "csrf_token": get_or_create_csrf_token(
                        request
                    ),
                    "error_message": (
                        "Employee records could not be loaded."
                    ),
                },
                status_code=500,
            )

        employee = find_employee_by_id(
            employee_list,
            employee_id,
        )

        if employee is None:
            return templates.TemplateResponse(
                request=request,
                name="employee_edit.html",
                context={
                    "page_title": "Employee not found",
                    "active_page": "employees",
                    "current_user": current_user,
                    "employee": None,
                    "form_values": form_values,
                    "csrf_token": get_or_create_csrf_token(
                        request
                    ),
                    "error_message": (
                        "The requested employee record "
                        "was not found."
                    ),
                },
                status_code=404,
            )

        update_employee_details(
            employee,
            form_values["department"],
            form_values["position"],
        )

        update_employee_contact_details(
            employee,
            form_values["email"],
            form_values["phone_number"],
        )

        if not save_employee_records(
            employee_list,
            database_file=database_file,
        ):
            return templates.TemplateResponse(
                request=request,
                name="employee_edit.html",
                context={
                    "page_title": f"Edit {employee['name']}",
                    "active_page": "employees",
                    "current_user": current_user,
                    "employee": employee,
                    "form_values": form_values,
                    "csrf_token": get_or_create_csrf_token(
                        request
                    ),
                    "error_message": (
                        "Employee changes could not be saved. "
                        "Please try again later."
                    ),
                },
                status_code=500,
            )

        log_activity(
            f"User {current_user['username']} updated "
            f"employee {employee['employee_id']} through "
            "the web application."
        )

        return RedirectResponse(
            url=request.url_for(
                "employee_profile",
                employee_id=employee["employee_id"],
            ),
            status_code=303,
        )

    @application.get(
        "/employees/{employee_id}",
        response_class=HTMLResponse,
    )
    def employee_profile(
        request: Request,
        employee_id: str,
    ) -> Response:
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
                f"Web employee-profile access denied "
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
                name="employee_profile.html",
                context={
                    "page_title": "Employee profile",
                    "active_page": "employees",
                    "current_user": current_user,
                    "employee": None,
                    "error_message": (
                        "Employee records could not be loaded."
                    ),
                },
                status_code=500,
            )

        employee = find_employee_by_id(
            employee_list,
            employee_id,
        )

        if employee is None:
            return templates.TemplateResponse(
                request=request,
                name="employee_profile.html",
                context={
                    "page_title": "Employee not found",
                    "active_page": "employees",
                    "current_user": current_user,
                    "employee": None,
                    "error_message": (
                        "The requested employee record "
                        "was not found."
                    ),
                },
                status_code=404,
            )

        return templates.TemplateResponse(
            request=request,
            name="employee_profile.html",
            context={
                "page_title": employee["name"],
                "active_page": "employees",
                "current_user": current_user,
                "employee": employee,
                "can_update_employee": user_has_permission(
                    current_user,
                    UPDATE_EMPLOYEE,
                ),
                "can_delete_employee": user_has_permission(
                    current_user,
                    DELETE_EMPLOYEE,
                ),
                "can_view_payroll": user_has_permission(
                    current_user,
                    VIEW_PAYROLL,
                ),
                "error_message": None,
            },
        )

    @application.get(
        "/employees/{employee_id}/payroll",
        response_class=HTMLResponse,
    )
    def employee_payroll(
        request: Request,
        employee_id: str,
    ) -> Response:
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
            VIEW_PAYROLL,
        ):
            log_activity(
                f"Web payroll access denied "
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
                name="employee_payroll.html",
                context={
                    "page_title": "Employee payroll",
                    "active_page": "employees",
                    "current_user": current_user,
                    "employee": None,
                    "payroll": None,
                    "error_message": (
                        "Employee records could not be loaded."
                    ),
                },
                status_code=500,
            )

        employee = find_employee_by_id(
            employee_list,
            employee_id,
        )

        if employee is None:
            return templates.TemplateResponse(
                request=request,
                name="employee_payroll.html",
                context={
                    "page_title": "Employee not found",
                    "active_page": "employees",
                    "current_user": current_user,
                    "employee": None,
                    "payroll": None,
                    "error_message": (
                        "The requested employee record "
                        "was not found."
                    ),
                },
                status_code=404,
            )

        payroll_summary = calculate_payroll(employee)

        return templates.TemplateResponse(
            request=request,
            name="employee_payroll.html",
            context={
                "page_title": (
                    f"{employee['name']} payroll"
                ),
                "active_page": "employees",
                "current_user": current_user,
                "employee": employee,
                "payroll": payroll_summary,
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
