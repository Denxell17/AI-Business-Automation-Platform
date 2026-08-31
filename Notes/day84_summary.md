# Day 84 Summary — Web Authentication and Login Foundation

## Goal

Add a secure, tested, accessible browser login workflow that reuses the existing SQLite authentication system.

## Completed Work

### Session Dependency

Added ItsDangerous to `requirements.txt`.

ItsDangerous allows Starlette to sign session cookies so the application can detect unauthorized cookie changes.

### Web Session Helper

Created `web_session.py`.

The helper:

- Starts an authenticated session
- Clears old session information before login
- Stores only the user ID and username
- Reloads the real account from SQLite
- Rejects missing accounts
- Rejects inactive accounts
- Rejects mismatched user identities
- Never stores passwords or password hashes in the browser session

### Template Structure

Changed the template structure into three layers:

- `base.html` provides the global HTML foundation
- `application_base.html` provides the authenticated sidebar and top bar
- `home.html` provides dashboard-specific content

This prevents the login page from displaying protected application navigation.

### Login Page

Created `templates/login.html`.

The login page includes:

- Visible username and password labels
- Hidden password entry
- Username autocomplete
- Current-password autocomplete
- Required fields
- Visible keyboard focus
- Accessible error messages
- Responsive Warm Charcoal styling
- No protected navigation before authentication

### Login Styling

Added authentication styles to `static/styles.css`.

The design includes:

- A centered desktop login card
- A full-height mobile layout
- Warm Charcoal surfaces
- Teal primary action
- Warm off-white text
- Clear input focus
- Icon-supported written error feedback
- Keyboard- and touch-friendly controls

### FastAPI Authentication Routes

Updated `web_app.py` through targeted additions and changes.

Added:

- `GET /login` to render the login form
- `POST /login` to authenticate submitted credentials
- Signed session middleware
- An eight-hour session duration
- `HttpOnly` cookie protection
- `SameSite=Lax` protection
- A generic authentication failure message
- Success and failure activity logging
- Dashboard authentication protection

The existing `authenticate_user_account()` service performs the real credential validation.

### Protected Dashboard

Opening `/` without an authenticated session returns a `303` redirect to `/login`.

After successful authentication, the user receives a signed session and is redirected to the dashboard.

The dashboard reloads the current account from SQLite before granting access.

### Automated Tests

Expanded the FastAPI web tests from 8 to 14.

The new tests cover:

- Accessible login form
- Unauthenticated redirect
- Valid login
- Invalid login
- Inactive-account rejection
- Signed session-cookie properties
- Authenticated username and role display

## Verification

Targeted web suite:

- 14 tests passed
- Runtime: 1.150 seconds

Complete automated suite:

- 229 tests passed
- Runtime: 10.748 seconds

Manual verification confirmed:

- `/` redirects unauthenticated visitors to `/login`
- The login page renders correctly
- Invalid credentials return one generic error
- The password remains hidden and clears after failure
- Correct credentials open the dashboard
- Responsive styling works at narrow widths
- Activity logs contain no passwords or password hashes

## Important Concepts

### Jinja2

Jinja2 combines HTML templates with data supplied by FastAPI.

### Signed Session

A signed session allows the server to detect whether someone modified session information stored in a browser cookie.

### HttpOnly

`HttpOnly` prevents normal browser JavaScript from reading the session cookie.

### SameSite

`SameSite=Lax` limits when the browser sends the cookie during requests originating from other websites.

### HTTP 401

Status `401` means authentication failed or valid authentication is required.

### HTTP 303

Status `303` tells the browser to make a new GET request at another address after an action such as login.

### Generic Authentication Failure

A generic error prevents attackers from learning whether a username exists, an account is inactive, or only the password was incorrect.

### Temporary Test Database

The web tests create accounts inside a temporary SQLite database so they cannot change real application data.

## Working-Agreement Update

Existing source files now receive targeted additions and changes. Complete contents are provided for new files and whole README Project Status replacements.

## Next Milestone

Day 85 will add tested logout and authenticated-session termination.