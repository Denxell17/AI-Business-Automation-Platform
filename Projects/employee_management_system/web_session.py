from pathlib import Path

from fastapi import Request

from database import (
    DATABASE_FILE,
    load_user_account_by_username,
)
from models import UserAccount


SESSION_USER_ID = "user_id"
SESSION_USERNAME = "username"
SESSION_VERSION = "session_version"


def begin_authenticated_session(
    request: Request,
    user_account: UserAccount,
) -> None:
    request.session.clear()
    request.session[SESSION_USER_ID] = (
        user_account["user_id"]
    )
    request.session[SESSION_USERNAME] = (
        user_account["username"]
    )
    request.session[SESSION_VERSION] = (
        user_account["session_version"]
    )


def clear_authenticated_session(
    request: Request,
) -> None:
    request.session.clear()


def load_authenticated_session_user(
    request: Request,
    database_file: Path = DATABASE_FILE,
) -> UserAccount | None:
    session_user_id = request.session.get(
        SESSION_USER_ID
    )
    session_username = request.session.get(
        SESSION_USERNAME
    )
    session_version = request.session.get(
        SESSION_VERSION
    )

    if (
        not isinstance(session_user_id, int)
        or not isinstance(session_username, str)
        or not session_username
        or not isinstance(session_version, int)
        or isinstance(session_version, bool)
        or session_version <= 0
    ):
        clear_authenticated_session(request)
        return None

    stored_user = load_user_account_by_username(
        session_username,
        database_file,
    )

    if stored_user is None:
        clear_authenticated_session(request)
        return None

    if not stored_user["is_active"]:
        clear_authenticated_session(request)
        return None

    if stored_user["user_id"] != session_user_id:
        clear_authenticated_session(request)
        return None

    if stored_user["session_version"] != session_version:
        clear_authenticated_session(request)
        return None

    return stored_user
