"""Request-safe internationalization helpers for ABAP's browser UI."""

import gettext
import re
from contextvars import ContextVar
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from starlette.responses import HTMLResponse


DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = frozenset({"en", "ja"})
LANGUAGE_OPTIONS = (
    {"code": "en", "label": "English", "direction": "ltr"},
    {"code": "ja", "label": "日本語", "direction": "ltr"},
)
LANGUAGE_DIRECTIONS = {
    option["code"]: option["direction"]
    for option in LANGUAGE_OPTIONS
}
TRANSLATIONS_DIRECTORY = Path(__file__).with_name("translations")
CURRENT_REQUEST_LANGUAGE: ContextVar[str] = ContextVar(
    "current_request_language",
    default=DEFAULT_LANGUAGE,
)


def N_(message: str) -> str:
    """Mark a deferred message for Babel extraction."""
    return message


PAGE_TITLE_MESSAGES = frozenset(
    {
        N_("Activity log"),
        N_("Add employee"),
        N_("Add viewer account"),
        N_("Add workflow schedule"),
        N_("Add workflow task"),
        N_("Agent Execution not found"),
        N_("Agent Template not found"),
        N_("Agent template directory"),
        N_("Agent template not found"),
        N_("Agent template unavailable"),
        N_("AI Assistant"),
        N_("Create agent template"),
        N_("Create workflow"),
        N_("Dashboard"),
        N_("Delete employee"),
        N_("Delete workflow task"),
        N_("Edit employee"),
        N_("Edit workflow"),
        N_("Edit workflow task"),
        N_("Employee directory"),
        N_("Employee not found"),
        N_("Employee payroll"),
        N_("Employee profile"),
        N_("Resequence workflow tasks"),
        N_("Sign in"),
        N_("User accounts"),
        N_("Webhook deliveries"),
        N_("Workflow directory"),
        N_("Workforce report"),
    }
)


# Fixed browser messages are explicitly allowlisted so arbitrary service,
# database, user, and business text is never treated as a translation key.
BROWSER_MESSAGE_KEYS = frozenset(
    {
        N_("A viewer account could not be created."),
        N_("Access denied."),
        N_("Activity log entries could not be loaded."),
        N_("Agent Execution history could not be loaded."),
        N_("Agent template could not be created. Verify the template ID, name, system prompt, model name, and draft status."),
        N_("Agent template could not be updated. Verify the submitted fields and lifecycle transition, or refresh the page if another update was completed first."),
        N_("Agent template records could not be loaded."),
        N_("Agent-template status filter is invalid."),
        N_("An employee with that ID already exists."),
        N_("An invoice needs between one and twenty line items."),
        N_("Converted leads cannot be edited."),
        N_("Customer filter is invalid."),
        N_("Customer is required."),
        N_("Customer not found."),
        N_("Customer status is invalid."),
        N_("Department, position, email, and phone number are required."),
        N_("Document is unavailable."),
        N_("Document not found."),
        N_("Due date is invalid."),
        N_("Email is invalid."),
        N_("Employee changes could not be saved. Please try again later."),
        N_("Employee could not be deleted."),
        N_("Employee could not be saved. Please try again later."),
        N_("Employee deletion could not be saved. Please try again later."),
        N_("Employee records could not be loaded."),
        N_("Employee records could not be loaded. Please try again later."),
        N_("Execution could not be finished."),
        N_("Execution could not be started. Only active workflows can run."),
        N_("Generated document is invalid."),
        N_("Invalid CSRF token."),
        N_("Invoice customer must be active."),
        N_("Invoice document could not be generated."),
        N_("Invoice line item is invalid."),
        N_("Invoice not found."),
        N_("Invoice number is invalid."),
        N_("Invoice status could not be changed."),
        N_("Invoice status transition is invalid."),
        N_("Invoice workflow could not start."),
        N_("Language preference could not be saved."),
        N_("Lead cannot accept notes."),
        N_("Lead cannot be edited."),
        N_("Lead not found."),
        N_("Lead stage is invalid."),
        N_("Lead stage transition is invalid."),
        N_("Line description is invalid."),
        N_("Only active workflows can have schedules."),
        N_("Only an Active Agent Template can be executed."),
        N_("Only qualified leads can be converted."),
        N_("Owner is invalid."),
        N_("Owner must be an active user."),
        N_("Password confirmation does not match."),
        N_("Schedule could not be created. Verify its ID, type, time, weekday, and that the workflow is active."),
        N_("Schedule status could not be updated."),
        N_("Search is too long."),
        N_("Task could not be created. Verify the task ID, title, and sequence number."),
        N_("Task could not be deleted. An active workflow must retain at least one task."),
        N_("Task could not be updated. Verify the title and required setting."),
        N_("Task execution could not be finished."),
        N_("Task execution could not be saved."),
        N_("Tax rate is invalid."),
        N_("The AI Assistant could not complete the request."),
        N_("The AI provider could not complete the request."),
        N_("The Agent Execution could not be loaded."),
        N_("The Agent Template could not be loaded."),
        N_("The agent template could not be loaded."),
        N_("The agent template could not be saved because the database is unavailable."),
        N_("The requested Agent Execution was not found."),
        N_("The requested Agent Template was not found."),
        N_("The requested account status is invalid."),
        N_("The requested agent template was not found."),
        N_("The requested employee record was not found."),
        N_("The viewer account status could not be changed."),
        N_("Too many AI requests. Try again shortly."),
        N_("Unsupported interface language."),
        N_("User accounts could not be loaded."),
        N_("Username or password is incorrect."),
        N_("Username, password, and password confirmation are required."),
        N_("Webhook delivery records could not be loaded."),
        N_("Workflow could not be created. Verify the workflow ID, name, and status."),
        N_("Workflow could not be updated. Verify the workflow name and status."),
        N_("Workflow must be active."),
        N_("Workflow not found."),
        N_("Workflow records could not be loaded."),
        N_("Workflow schedules could not be saved."),
        N_("Workflow status filter is invalid."),
        N_("Workflow task not found."),
        N_("Workflow tasks could not be resequenced."),
        N_("Your form could not be verified."),
    }
)

VALIDATION_FIELD_LABELS = {
    "Company": N_("Company"),
    "Email": N_("Email"),
    "Name": N_("Name"),
    "Note": N_("Note"),
    "Phone number": N_("Phone number"),
    "Quantity": N_("Quantity"),
    "Stage": N_("Stage"),
    "Status": N_("Status"),
    "Unit price": N_("Unit price"),
}
VALIDATION_MESSAGE_PATTERN = re.compile(
    r"^(?P<field>Company|Email|Name|Note|Phone number|Quantity|Stage|Status|Unit price) "
    r"(?P<rule>is invalid|is required|has too many decimal places)\.$"
)
VALIDATION_RULE_MESSAGES = {
    "is invalid": N_("%(field)s is invalid."),
    "is required": N_("%(field)s is required."),
    "has too many decimal places": N_("%(field)s has too many decimal places."),
}


# Only stable application codes belong here. User and business values must
# never be passed through this mapping as translation keys.
CONTROLLED_VALUE_LABELS = {
    "active": "Active",
    "accepted": "Accepted",
    "admin": N_("Administrator"),
    "completed": "Completed",
    "contacted": N_("Contacted"),
    "converted": N_("Converted"),
    "daily": "Daily",
    "disabled": "Disabled",
    "draft": "Draft",
    "enabled": "Enabled",
    "failed": "Failed",
    "friday": "Friday",
    "inactive": "Inactive",
    "inbound": "Inbound",
    "manual": "Manual",
    "monday": "Monday",
    "new": N_("New"),
    "note_added": "Note added",
    "once": "Once",
    "outbound": "Outbound",
    "paid": "Paid",
    "pending": "Pending",
    "qualified": N_("Qualified"),
    "retrying": "Retrying",
    "running": "Running",
    "saturday": "Saturday",
    "schedule": "Schedule",
    "scheduled": "Scheduled",
    "sent": "Sent",
    "sunday": "Sunday",
    "succeeded": "Succeeded",
    "thursday": "Thursday",
    "tuesday": "Tuesday",
    "unqualified": N_("Unqualified"),
    "viewer": N_("Viewer"),
    "void": "Void",
    "wednesday": "Wednesday",
    "weekly": "Weekly",
    "created": "Created",
    "updated": "Updated",
}


def validated_language(value: object) -> str | None:
    """Return an exact supported language code or None."""
    return value if isinstance(value, str) and value in SUPPORTED_LANGUAGES else None


def resolve_interface_language(
    session_language: object,
    persisted_language: object = None,
) -> str:
    """Resolve language using the frozen session/account/English order."""
    return (
        validated_language(session_language)
        or validated_language(persisted_language)
        or DEFAULT_LANGUAGE
    )


@lru_cache(maxsize=len(SUPPORTED_LANGUAGES))
def translation_for(language: str) -> gettext.NullTranslations:
    """Load a catalog defensively, falling back to English source text."""
    selected_language = validated_language(language) or DEFAULT_LANGUAGE
    if selected_language == DEFAULT_LANGUAGE:
        return gettext.NullTranslations()

    try:
        return gettext.translation(
            "messages",
            localedir=TRANSLATIONS_DIRECTORY,
            languages=[selected_language],
            fallback=True,
        )
    except (OSError, UnicodeError):
        return gettext.NullTranslations()


def controlled_value_label(
    code: object,
    gettext_function: Callable[[str], str],
) -> str:
    """Translate a known stable code without treating arbitrary data as a key."""
    if not isinstance(code, str):
        return ""
    message = CONTROLLED_VALUE_LABELS.get(code.casefold())
    return gettext_function(message) if message is not None else code


def browser_message_label(
    value: object,
    gettext_function: Callable[..., str],
) -> object:
    """Translate only known browser messages; preserve all other data."""
    if not isinstance(value, str):
        return value
    if value in BROWSER_MESSAGE_KEYS:
        return gettext_function(value)

    match = VALIDATION_MESSAGE_PATTERN.fullmatch(value)
    if match is None:
        return value

    field_message = VALIDATION_FIELD_LABELS[match.group("field")]
    rule_message = VALIDATION_RULE_MESSAGES[match.group("rule")]
    return gettext_function(
        rule_message,
        field=gettext_function(field_message),
    )


def _request_translation_callables(
    translations: gettext.NullTranslations,
) -> dict[str, Callable[..., str]]:
    """Return Jinja new-style gettext callables for one request."""

    def interpolate(message: str, variables: dict[str, Any]) -> str:
        return message % variables if variables else message

    def gettext_function(message: str, **variables: Any) -> str:
        return interpolate(translations.gettext(message), variables)

    def ngettext_function(
        singular: str,
        plural: str,
        num: int,
        **variables: Any,
    ) -> str:
        variables.setdefault("num", num)
        return interpolate(translations.ngettext(singular, plural, num), variables)

    def pgettext_function(
        context: str,
        message: str,
        **variables: Any,
    ) -> str:
        return interpolate(translations.pgettext(context, message), variables)

    def npgettext_function(
        context: str,
        singular: str,
        plural: str,
        num: int,
        **variables: Any,
    ) -> str:
        variables.setdefault("num", num)
        return interpolate(
            translations.npgettext(context, singular, plural, num),
            variables,
        )

    return {
        "gettext": gettext_function,
        "ngettext": ngettext_function,
        "pgettext": pgettext_function,
        "npgettext": npgettext_function,
    }


def request_i18n_context(request: Any) -> dict[str, Any]:
    """Build locale metadata and callables for one request only."""
    current_user = getattr(request.state, "authenticated_user", None)
    persisted_language = (
        current_user.get("interface_language")
        if isinstance(current_user, dict)
        else None
    )
    language = resolve_interface_language(
        request.session.get("interface_language"),
        persisted_language,
    )
    translations = translation_for(language)
    callables = _request_translation_callables(translations)
    gettext_function = callables["gettext"]

    return {
        "interface_language": language,
        "text_direction": LANGUAGE_DIRECTIONS[language],
        "language_options": LANGUAGE_OPTIONS,
        "gettext": gettext_function,
        "_": gettext_function,
        "ngettext": callables["ngettext"],
        "pgettext": callables["pgettext"],
        "npgettext": callables["npgettext"],
        "controlled_label": lambda code: controlled_value_label(
            code,
            gettext_function,
        ),
        "browser_message": lambda value: browser_message_label(
            value,
            gettext_function,
        ),
        "page_title_label": lambda value: (
            gettext_function(value)
            if value in PAGE_TITLE_MESSAGES
            else value
        ),
    }


def gettext_for_request(request: Any) -> Callable[[str], str]:
    """Return the request's translator for browser-facing Python messages."""
    return request_i18n_context(request)["gettext"]


def bind_request_language(request: Any) -> None:
    """Refresh the task-local language after account resolution."""
    current_user = getattr(request.state, "authenticated_user", None)
    persisted_language = (
        current_user.get("interface_language")
        if isinstance(current_user, dict)
        else None
    )
    CURRENT_REQUEST_LANGUAGE.set(
        resolve_interface_language(
            request.session.get("interface_language"),
            persisted_language,
        )
    )


class RequestLanguageMiddleware:
    """Bind a validated session locale to the current async request task."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        session = scope.get("session", {})
        language = resolve_interface_language(
            session.get("interface_language")
            if isinstance(session, dict)
            else None
        )
        token = CURRENT_REQUEST_LANGUAGE.set(language)
        try:
            await self.app(scope, receive, send)
        finally:
            CURRENT_REQUEST_LANGUAGE.reset(token)


class LocalizedHTMLResponse(HTMLResponse):
    """Translate an allowlisted plain browser message for this request."""

    def render(self, content: Any) -> bytes:
        if isinstance(content, str):
            translations = translation_for(CURRENT_REQUEST_LANGUAGE.get())
            gettext_function = _request_translation_callables(translations)[
                "gettext"
            ]
            content = browser_message_label(content, gettext_function)
        return super().render(content)
