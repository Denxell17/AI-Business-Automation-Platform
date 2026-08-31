# Day 82 Summary — Responsive CSS and FastAPI Static Files

## Goal

Build a tested static-file foundation and apply responsive CSS styling
to the Employee Management System home page.

The Day 82 work remained intentionally limited to presentation and
static-file delivery.

No login, database, employee-management, or authorization workflow
was added to the web interface.

## Starting Point

Day 81 provided:

- A FastAPI application factory
- A `/health` JSON endpoint
- Automatic OpenAPI documentation at `/docs`
- A Jinja2 template system
- A plain HTML home page at `/`
- Three FastAPI web tests
- A complete suite of 218 passing tests

The Day 81 home page worked correctly but used the browser's default
unstyled appearance.

## Architecture Decision

The existing FastAPI, Jinja2, HTML, and Python architecture was
preserved.

No React, JavaScript framework, CSS framework, or additional frontend
dependency was introduced.

This keeps the current learning scope focused on:

- Native HTML
- Native CSS
- FastAPI static-file handling
- Responsive browser behavior
- Automated testing

The website-building guidance influenced this decision by favoring
the smallest coherent improvement to the existing application instead
of replacing its working architecture.

## Static Directory

A new static directory was created:

```text
Projects/employee_management_system/static/
```

The stylesheet is stored at:

```text
Projects/employee_management_system/static/styles.css
```

Static files are resources that the server sends without dynamically
building their contents for every request.

Examples include:

- CSS stylesheets
- Images
- Browser JavaScript
- Fonts
- Downloadable documents

Day 82 uses only a CSS stylesheet.

## FastAPI StaticFiles

`web_app.py` imports:

```python
from fastapi.staticfiles import StaticFiles
```

The application identifies the static directory with:

```python
STATIC_DIRECTORY = APPLICATION_DIRECTORY / "static"
```

Because the path is based on:

```python
Path(__file__).resolve().parent
```

FastAPI can find the directory reliably regardless of the current
terminal directory.

The directory is mounted with:

```python
application.mount(
    "/static",
    StaticFiles(directory=STATIC_DIRECTORY),
    name="static",
)
```

## Meaning of Mounting

Mounting connects a physical directory to a browser URL.

The physical file:

```text
Projects/employee_management_system/static/styles.css
```

becomes available through:

```text
http://127.0.0.1:8000/static/styles.css
```

The mount configuration has three important parts:

```python
"/static"
```

This is the URL prefix used by the browser.

```python
StaticFiles(directory=STATIC_DIRECTORY)
```

This identifies the directory containing the files.

```python
name="static"
```

This assigns a route name that Jinja2 can use with `url_for()`.

## Connecting HTML to CSS

The Jinja2 home-page template connects to the stylesheet with:

```html
<link
    rel="stylesheet"
    href="{{ url_for('static', path='/styles.css') }}"
>
```

`rel="stylesheet"` tells the browser that the linked resource contains
CSS.

`url_for()` asks the application to generate the correct URL for the
named `static` mount.

The generated HTML includes a stylesheet address containing:

```text
/static/styles.css
```

Without the `<link>` element, the stylesheet could exist and be
downloadable while the page remained unstyled.

## CSS Custom Properties

The stylesheet begins with reusable values inside:

```css
:root {
    --color-background: #f4f7fb;
    --color-surface: #ffffff;
    --color-header: #10233f;
    --color-primary: #0f766e;
    --color-primary-light: #ccfbf1;
    --color-text: #172033;
    --color-muted: #5f6b7a;
    --color-border: #dbe3ec;
    --shadow-card: 0 16px 40px rgba(15, 35, 63, 0.10);
    --content-width: 1120px;
}
```

These are CSS custom properties, commonly called CSS variables.

They allow the same design value to be reused.

For example:

```css
background: var(--color-background);
```

uses the value stored in:

```css
--color-background
```

Benefits include:

- Consistent colors and measurements
- Easier maintenance
- Fewer repeated values
- Simpler future theme changes

## Universal Box Sizing

The stylesheet contains:

```css
* {
    box-sizing: border-box;
}
```

The `*` selector targets every HTML element.

`box-sizing: border-box` makes an element's declared width include its
padding and border.

This makes page sizing more predictable and helps prevent accidental
overflow.

## Body Foundation

The body style establishes the overall page:

```css
body {
    min-height: 100vh;
    margin: 0;
    background: var(--color-background);
    color: var(--color-text);
    font-family:
        "Segoe UI",
        Arial,
        sans-serif;
    line-height: 1.6;
}
```

Important properties include:

- `min-height: 100vh` — fills at least the viewport height
- `margin: 0` — removes the browser's default outer margin
- `background` — applies the light page background
- `color` — sets the default text color
- `font-family` — provides a system-friendly font fallback sequence
- `line-height` — improves text readability

## HTML Container Element

The page uses:

```html
<div class="header-content">
```

A `<div>` is a general-purpose HTML container.

It groups the product name and application title so the two elements
can share the same width and alignment rules.

The `<header>` keeps the semantic meaning, while the inner `<div>`
controls layout.

## Constrained Content Width

The header and page content use:

```css
.header-content,
.page-content {
    width: min(
        calc(100% - 2rem),
        var(--content-width)
    );
    margin: 0 auto;
}
```

`calc(100% - 2rem)` keeps content away from the left and right screen
edges.

`var(--content-width)` limits the content to 1120 pixels on large
screens.

`min()` selects the smaller of those two values.

`margin: 0 auto` centers the constrained content horizontally.

## Responsive Heading

The title uses:

```css
font-size: clamp(2rem, 5vw, 3.25rem);
```

`clamp()` provides:

1. A minimum value: `2rem`
2. A flexible value: `5vw`
3. A maximum value: `3.25rem`

The title can grow or shrink with the screen without becoming too
small or too large.

## Welcome Card

The welcome section uses the `welcome-card` class.

Its CSS provides:

- A white surface
- Internal spacing
- A light border
- Rounded corners
- A soft shadow
- A controlled maximum width

This separates the primary content from the page background and
creates a professional working-surface appearance.

## Status Presentation

The system status is displayed as a pill:

```html
<p class="status-message">
    <span
        class="status-indicator"
        aria-hidden="true"
    ></span>
    Web interface foundation is running.
</p>
```

The status message uses:

- An inline-flex layout
- Teal text
- A pale teal background
- Rounded pill-shaped corners
- A circular status indicator

The circle is decorative, so it uses:

```html
aria-hidden="true"
```

This prevents a screen reader from announcing an element that adds no
meaning beyond the written status message.

## Labelled Section

The welcome section contains:

```html
<section
    class="welcome-card"
    aria-labelledby="welcome-heading"
>
```

Its heading uses:

```html
<h2 id="welcome-heading">
```

`aria-labelledby` tells assistive technology that the heading with
that ID names the section.

## Mobile Media Query

The stylesheet contains:

```css
@media (max-width: 600px) {
    .site-header {
        padding: 1.5rem 0;
    }

    .page-content {
        padding: 1.5rem 0;
    }

    .welcome-card {
        padding: 1.5rem;
        border-radius: 0.75rem;
    }
}
```

This media query applies when the viewport is 600 pixels wide or
smaller.

It reduces:

- Header spacing
- Page spacing
- Card padding
- Card corner radius

The content therefore fits more comfortably on narrow screens.

## Static Stylesheet Test

The static-file test sends a request to:

```text
/static/styles.css
```

It verifies:

```python
self.assertEqual(response.status_code, 200)
```

This confirms that the file was found and returned successfully.

It also verifies:

```python
self.assertIn(
    "text/css",
    response.headers["content-type"],
)
```

This confirms that the server identifies the response as CSS.

Finally, it checks for an expected design variable:

```python
self.assertIn(
    "--color-primary",
    response.text,
)
```

This helps confirm that the intended stylesheet content was returned.

## HTML-to-CSS Connection Test

A separate test requests the home page and checks:

```python
self.assertIn(
    "/static/styles.css",
    response.text,
)
```

This verifies that the rendered HTML links to the stylesheet.

The two static-related tests cover different responsibilities:

1. The CSS file is available.
2. The HTML page connects to that CSS file.

## Focused Test Result

The FastAPI web test suite now contains five tests:

```text
Ran 5 tests
OK
```

They verify:

- API documentation availability
- Health-check behavior
- Home-page HTML content
- Home-page stylesheet connection
- Static stylesheet availability and content type

## Complete Regression Result

The previous complete suite contained 218 tests.

Day 82 added two tests, bringing the new result to:

```text
Ran 220 tests in 12.673s
OK
```

This confirms that responsive styling and static-file delivery did
not break the console application or existing business workflows.

## Desktop Verification

The desktop browser view confirmed:

- A full-width navy header
- A teal uppercase product label
- A large white application title
- A light page background
- A white bordered welcome card
- A soft card shadow
- A readable description
- A teal status pill and indicator
- Consistent constrained content alignment

## Narrow-Window Verification

The browser was manually narrowed to approximate a phone-sized view.

The narrow view confirmed:

- The application title wrapped cleanly
- Text remained readable
- The welcome card stayed inside the viewport
- Page margins remained visible
- The description wrapped naturally
- The status presentation remained usable
- No horizontal overflow was visible
- The mobile spacing rules were applied

## Files Added

```text
Projects/employee_management_system/static/styles.css
```

## Files Updated

```text
Projects/employee_management_system/web_app.py
Projects/employee_management_system/templates/home.html
Projects/employee_management_system/tests/test_web_app.py
README.md
```

## Main Concepts Practiced

- Static-file directories
- FastAPI `StaticFiles`
- Mounted routes
- Named static routes
- Jinja2 `url_for()`
- HTML stylesheet links
- CSS custom properties
- Universal selectors
- Box sizing
- System font stacks
- Constrained responsive widths
- `min()`
- `calc()`
- `clamp()`
- CSS cards, borders, shadows, and radius
- Flexbox alignment
- Mobile media queries
- Semantic HTML
- Accessible section labelling
- Decorative-element hiding
- MIME content types
- Static-resource testing
- HTML-to-CSS integration testing
- Desktop visual verification
- Narrow-screen verification
- Full regression testing

## Business Value

The Employee Management System now has a professional and responsive
browser presentation instead of a plain HTML proof of concept.

The static-file foundation can later serve:

- Additional stylesheets
- Application icons
- Approved images
- Browser JavaScript
- Downloadable interface resources

The responsive foundation makes future login, dashboard, employee,
and account-management pages usable across different screen sizes.

## Day 82 Result

Day 82 successfully added:

- A dedicated static directory
- A responsive CSS stylesheet
- FastAPI static-file mounting
- A stylesheet connection through Jinja2
- Reusable design variables
- A professional navy-and-teal visual system
- Accessible page structure
- Desktop and narrow-screen behavior
- Two new FastAPI web tests
- A complete passing suite of 220 tests

## Next Step

Day 83 will introduce a tested reusable base template and navigation
foundation for the growing web interface.

This will reduce repeated HTML as additional pages are introduced,
while preserving the existing FastAPI application, responsive design,
and console workflows.