# Day 81 Summary — FastAPI Web Foundation and First HTML Page

## Goal

Begin the Employee Management System web-interface phase without
breaking or replacing the existing console application.

The Day 81 goal was to create a small, tested FastAPI foundation that:

- Runs separately from the console application
- Provides a health-check endpoint
- Generates automatic API documentation
- Renders the first HTML page through Jinja2
- Uses an isolated Python environment
- Preserves all existing business, database, authentication,
  authorization, and console behavior

## Why FastAPI Was Selected

FastAPI was selected instead of Flask because it fits the long-term
direction of the AI Business Automation Platform.

FastAPI supports:

- Modern Python type hints
- Automatic request validation
- Automatic OpenAPI documentation
- Interactive Swagger documentation
- JSON APIs
- Server-rendered HTML templates
- Asynchronous workflows
- Dependency injection
- API integrations
- AI and automation services
- Automated web testing

FastAPI is primarily a backend and API framework, but it can also
return HTML pages through Jinja2 templates.

This allows the project to begin with a simple server-rendered
interface and later support external clients, JavaScript frontends,
mobile applications, automation tools, and AI services.

## Isolated Python Environment

A virtual environment was created at the repository root:

```text
AI-Business-Automation-Platform/
└── .venv/
```

The virtual environment keeps this project's external packages
separate from globally installed Python packages.

The environment was created with:

```powershell
python -m venv .venv
```

The FastAPI dependencies are recorded in:

```text
Projects/employee_management_system/requirements.txt
```

The dependency file contains:

```text
fastapi[standard]
httpx2>=2,<3
```

`fastapi[standard]` installs FastAPI and supporting packages such as:

- Uvicorn
- Jinja2
- HTTPX
- Form-parsing support
- FastAPI command-line tools

HTTPX2 was added because the installed Starlette test client reported
that its older HTTPX integration was deprecated.

After HTTPX2 was installed, the warning disappeared and all web tests
continued to pass.

## Dependency Installation

Because `requirements.txt` belongs specifically to the Employee
Management System, it is stored inside that project folder.

From the repository root, dependencies are installed with:

```powershell
.\.venv\Scripts\python.exe -m pip install -r Projects\employee_management_system\requirements.txt
```

The first installation attempt failed because the command searched
for `requirements.txt` in the repository root.

The correct relative path was:

```text
Projects\employee_management_system\requirements.txt
```

No files or environments needed to be deleted. Only the dependency
file path in the installation command needed correction.

## Web Application Separation

The existing console entry point remains:

```text
Projects/employee_management_system/main.py
```

The new FastAPI entry point is:

```text
Projects/employee_management_system/web_app.py
```

Keeping them separate means:

- The console interface continues to work
- The web interface can develop independently
- Existing business services can be reused
- Web changes do not require rewriting the console application
- Both interfaces can eventually call the same service layer

## FastAPI Application Factory

The web application is created through:

```python
def create_web_application() -> FastAPI:
```

This is an application factory.

An application factory is a function that creates and returns an
application object.

Benefits include:

- Each automated test can create a fresh application
- Application construction remains organized
- Future settings can be supplied during creation
- Routes and middleware can be configured in one place
- Tests do not need to start a real server

The module-level application is created with:

```python
app = create_web_application()
```

FastAPI's development server imports this `app` object when starting
the web application.

## Application Metadata

The FastAPI application includes:

```python
application = FastAPI(
    title="Employee Management System",
    description=(
        "Web application and API for managing "
        "employee and user-account information."
    ),
    version="1.0.0",
)
```

This metadata appears in the automatically generated API
documentation.

It identifies:

- The application name
- The application's purpose
- The current API version

## Health-Check Endpoint

The health endpoint is:

```python
@application.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
    }
```

A health check provides a small endpoint that confirms the
application is running and able to respond.

The route uses the HTTP `GET` method because it retrieves information
without changing application data.

Visiting:

```text
http://127.0.0.1:8000/health
```

returns:

```json
{"status":"healthy"}
```

HTTP status `200` means that the request succeeded.

## Automatic API Documentation

FastAPI automatically generates interactive documentation at:

```text
http://127.0.0.1:8000/docs
```

The documentation displayed:

- Employee Management System
- Version `1.0.0`
- OpenAPI information
- The registered `GET /health` endpoint

This documentation will expand automatically as more API routes are
added.

## Template Directory Resolution

The application locates its HTML templates with:

```python
APPLICATION_DIRECTORY = Path(__file__).resolve().parent
TEMPLATES_DIRECTORY = APPLICATION_DIRECTORY / "templates"
```

`__file__` refers to the current Python file.

`Path(__file__).resolve().parent` produces the absolute directory
containing `web_app.py`.

Adding `/ "templates"` creates the path to:

```text
Projects/employee_management_system/templates
```

This is safer than depending on whichever directory the user happens
to run the command from.

The template loader is created with:

```python
templates = Jinja2Templates(
    directory=TEMPLATES_DIRECTORY,
)
```

## First HTML Template

The first HTML template is stored at:

```text
Projects/employee_management_system/templates/home.html
```

It contains semantic HTML elements including:

- `<header>`
- `<main>`
- `<section>`
- Headings
- Paragraphs
- Page metadata
- Mobile viewport configuration

The viewport configuration is:

```html
<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>
```

This tells the browser to use the device's real display width and
provides the foundation for responsive styling.

## Jinja2 Template Variables

The HTML template contains Jinja2 placeholders:

```html
<title>{{ page_title }}</title>
<h1>{{ page_title }}</h1>
<p>{{ page_message }}</p>
```

The FastAPI route supplies their values through a context dictionary:

```python
context={
    "page_title": "Employee Management System",
    "page_message": (
        "Securely manage workforce information "
        "through a browser."
    ),
}
```

Jinja2 replaces the placeholders before returning the completed HTML
to the browser.

## Home-Page Route

The main page is served by:

```python
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
```

The route `/` represents the application's main address.

`response_class=HTMLResponse` documents that the route returns HTML
instead of JSON.

The `Request` object contains information about the incoming browser
request.

`TemplateResponse` loads `home.html`, inserts the context values, and
returns the rendered page.

## Starting the Development Server

The application is started from the repository root with:

```powershell
.\.venv\Scripts\python.exe -m fastapi dev Projects\employee_management_system\web_app.py
```

The development server uses Uvicorn.

The server reported:

```text
Application startup complete.
```

A successful home-page request was recorded as:

```text
GET / HTTP/1.1" 200
```

The development server automatically watches for saved code changes.

It is stopped by pressing:

```text
Ctrl+C
```

## Web Testing

The new test file is:

```text
Projects/employee_management_system/tests/test_web_app.py
```

FastAPI's `TestClient` behaves like a small test browser.

It sends requests directly to the application without requiring a
real server or opening a browser.

The test setup is:

```python
def setUp(self):
    application = create_web_application()
    self.client = TestClient(application)
```

`setUp()` runs before every test.

Each test therefore receives a newly created FastAPI application and
test client.

## Health-Check Test

The health test verifies:

- HTTP status `200`
- Exact JSON response data

```python
def test_health_check_returns_healthy_status(self):
    response = self.client.get("/health")

    self.assertEqual(response.status_code, 200)
    self.assertEqual(
        response.json(),
        {
            "status": "healthy",
        },
    )
```

## Documentation Test

The documentation test verifies:

- `/docs` is available
- It returns HTTP status `200`
- Its content type includes `text/html`

```python
def test_api_documentation_is_available(self):
    response = self.client.get("/docs")

    self.assertEqual(response.status_code, 200)
    self.assertIn(
        "text/html",
        response.headers["content-type"],
    )
```

`assertIn()` is used because the full header may contain:

```text
text/html; charset=utf-8
```

The test only needs to confirm that `text/html` appears inside it.

## Home-Page Test

The home-page test verifies:

- `/` is available
- It returns HTTP status `200`
- It returns HTML
- The application title was rendered
- The business message was rendered

```python
def test_home_page_returns_employee_management_html(self):
    response = self.client.get("/")

    self.assertEqual(response.status_code, 200)
    self.assertIn(
        "text/html",
        response.headers["content-type"],
    )
    self.assertIn(
        "Employee Management System",
        response.text,
    )
    self.assertIn(
        "Securely manage workforce information",
        response.text,
    )
```

## Test Results

The focused FastAPI test suite produced:

```text
Ran 3 tests
OK
```

The complete regression suite produced:

```text
Ran 218 tests in 20.351s
OK
```

This includes the previous `215` tests and the new `3` FastAPI web
tests.

The complete passing suite confirms that the web foundation did not
break:

- Employee management
- SQLite persistence
- Backup and restoration
- Authentication
- Authorization
- Viewer-account management
- Password management
- Reporting
- Exporting
- Console workflows
- Existing storage utilities

## Manual Verification

Manual browser verification confirmed:

1. FastAPI started successfully.
2. `/health` returned `{"status":"healthy"}`.
3. `/docs` displayed the automatic API documentation.
4. `/` rendered the first Jinja2 HTML page.
5. The terminal recorded the home-page request with status `200`.

The first page intentionally has no custom styling yet.

It proves the complete path:

```text
Browser
    ↓
FastAPI route
    ↓
Jinja2 template
    ↓
Rendered HTML response
```

## Files Added

```text
Projects/employee_management_system/requirements.txt
Projects/employee_management_system/web_app.py
Projects/employee_management_system/templates/home.html
Projects/employee_management_system/tests/test_web_app.py
```

## Files Updated

```text
README.md
```

## Main Concepts Practiced

- Python virtual environments
- Dependency files
- FastAPI application creation
- Application factories
- Uvicorn development serving
- HTTP GET routes
- HTTP status codes
- JSON responses
- HTML responses
- Automatic OpenAPI documentation
- Jinja2 template rendering
- Template context dictionaries
- Semantic HTML
- Mobile viewport configuration
- Reliable file paths with `pathlib`
- FastAPI `TestClient`
- Web endpoint tests
- Full regression testing
- Separation of console and web interfaces

## Business Value

The Employee Management System now has the foundation required for a
browser interface.

This improves the project because:

- Users will not need to operate the application entirely through a
  terminal
- Existing business services can be reused by multiple interfaces
- Future integrations can communicate through APIs
- The application now demonstrates a modern, in-demand Python web
  framework
- Automatic API documentation makes integration easier
- Automated tests reduce the risk of breaking existing workflows

## Day 81 Result

Day 81 successfully established the tested FastAPI web foundation
while preserving the complete console application.

The project now has:

- An isolated dependency environment
- Recorded FastAPI dependencies
- A separate FastAPI entry point
- An application factory
- A health-check endpoint
- Interactive API documentation
- A Jinja2 template system
- A working HTML home page
- Three automated web tests
- A complete passing suite of 218 tests

## Next Step

Day 82 will add a tested static-file foundation and responsive CSS
styling to the first web page.

No authentication, database access, or employee workflow will be
added to the web interface until the page structure and styling
foundation are tested.