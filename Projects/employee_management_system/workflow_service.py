from datetime import datetime, timezone
from pathlib import Path

from authorization import (
    MANAGE_WORKFLOWS,
    user_has_permission,
)
from database import (
    DATABASE_FILE,
    insert_workflow,
    load_user_account_by_username,
)
from models import (
    UserAccount,
    VALID_WORKFLOW_STATUSES,
    Workflow,
)


def create_workflow(
    current_user: UserAccount,
    workflow_id: str,
    name: str,
    description: str,
    status: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
    if not current_user["is_active"]:
        return False

    stored_user = load_user_account_by_username(
        current_user["username"],
        database_file,
    )

    if (
        stored_user is None
        or not stored_user["is_active"]
        or stored_user["user_id"] != current_user["user_id"]
        or not user_has_permission(
            stored_user,
            MANAGE_WORKFLOWS,
        )
    ):
        return False

    normalized_workflow_id = workflow_id.strip().upper()
    normalized_name = name.strip()
    normalized_description = description.strip()
    normalized_status = status.strip().casefold()

    if (
        not normalized_workflow_id
        or not normalized_name
        or normalized_status
        not in VALID_WORKFLOW_STATUSES
    ):
        return False

    timestamp = datetime.now(timezone.utc).isoformat()

    workflow: Workflow = {
        "workflow_id": normalized_workflow_id,
        "name": normalized_name,
        "description": normalized_description,
        "status": normalized_status,
        "created_by_user_id": stored_user["user_id"],
        "created_at": timestamp,
        "updated_at": timestamp,
    }

    return insert_workflow(
        workflow,
        database_file,
    )