from datetime import datetime, timezone
from pathlib import Path

from authorization import (
    MANAGE_WORKFLOWS,
    user_has_permission,
)
from database import (
    DATABASE_FILE,
    insert_workflow,
    insert_workflow_task,
    load_user_account_by_username,
    load_workflow_by_id,
    load_workflow_task_by_id,
    load_workflow_tasks,
    resequence_workflow_tasks,
    update_workflow_task,
    update_workflow_in_database,
)
from models import (
    UserAccount,
    VALID_WORKFLOW_STATUSES,
    Workflow,
    WorkflowTask,
    VALID_WORKFLOW_TASK_TYPES,
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
        or normalized_status == "active"
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


def create_workflow_task(
    current_user: UserAccount,
    task_id: str,
    workflow_id: str,
    sequence_number: int,
    title: str,
    instructions: str,
    task_type: str,
    is_required: bool,
    database_file: Path = DATABASE_FILE,
) -> bool:
    if not current_user["is_active"]:
        return False

    stored_user = load_user_account_by_username(
        current_user["username"], database_file,
    )
    if (
        stored_user is None
        or not stored_user["is_active"]
        or stored_user["user_id"] != current_user["user_id"]
        or not user_has_permission(stored_user, MANAGE_WORKFLOWS)
    ):
        return False

    if (
        not all(isinstance(value, str) for value in (
            task_id, workflow_id, title, instructions, task_type,
        ))
        or type(sequence_number) is not int
        or not 1 <= sequence_number <= 9223372036854775807
        or type(is_required) is not bool
    ):
        return False

    normalized_task_id = task_id.strip().upper()
    normalized_workflow_id = workflow_id.strip().upper()
    normalized_title = title.strip()
    normalized_task_type = task_type.strip().casefold()
    if (
        not normalized_task_id
        or not normalized_workflow_id
        or not normalized_title
        or normalized_task_type not in VALID_WORKFLOW_TASK_TYPES
        or load_workflow_by_id(normalized_workflow_id, database_file) is None
    ):
        return False

    timestamp = datetime.now(timezone.utc).isoformat()
    task: WorkflowTask = {
        "task_id": normalized_task_id,
        "workflow_id": normalized_workflow_id,
        "sequence_number": sequence_number,
        "title": normalized_title,
        "instructions": instructions.strip(),
        "task_type": normalized_task_type,
        "is_required": is_required,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    return insert_workflow_task(task, database_file)


def update_workflow_task_details(
    current_user: UserAccount,
    workflow_id: str,
    task_id: str,
    title: str,
    instructions: str,
    is_required: bool,
    database_file: Path = DATABASE_FILE,
) -> bool:
    if not current_user["is_active"] or type(is_required) is not bool:
        return False
    stored_user = load_user_account_by_username(current_user["username"], database_file)
    if (
        stored_user is None or not stored_user["is_active"]
        or stored_user["user_id"] != current_user["user_id"]
        or not user_has_permission(stored_user, MANAGE_WORKFLOWS)
        or not all(isinstance(value, str) for value in (workflow_id, task_id, title, instructions))
    ):
        return False
    task = load_workflow_task_by_id(task_id.strip().upper(), database_file)
    if task is None or task["workflow_id"] != workflow_id.strip().upper() or not title.strip():
        return False
    task["title"] = title.strip()
    task["instructions"] = instructions.strip()
    task["is_required"] = is_required
    task["updated_at"] = datetime.now(timezone.utc).isoformat()
    return update_workflow_task(task, database_file)


def resequence_workflow_task_list(
    current_user: UserAccount,
    workflow_id: str,
    task_ids: list[str],
    database_file: Path = DATABASE_FILE,
) -> bool:
    if not current_user["is_active"] or not isinstance(task_ids, list):
        return False
    stored_user = load_user_account_by_username(current_user["username"], database_file)
    if (
        stored_user is None or not stored_user["is_active"]
        or stored_user["user_id"] != current_user["user_id"]
        or not user_has_permission(stored_user, MANAGE_WORKFLOWS)
        or not isinstance(workflow_id, str)
        or not all(isinstance(task_id, str) and task_id.strip() for task_id in task_ids)
    ):
        return False
    normalized_workflow_id = workflow_id.strip().upper()
    if load_workflow_by_id(normalized_workflow_id, database_file) is None:
        return False
    normalized_task_ids = [task_id.strip().upper() for task_id in task_ids]
    if len(set(normalized_task_ids)) != len(normalized_task_ids):
        return False
    return resequence_workflow_tasks(
        normalized_workflow_id, normalized_task_ids,
        datetime.now(timezone.utc).isoformat(), database_file,
    )


def update_workflow(
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
        or normalized_status not in VALID_WORKFLOW_STATUSES
    ):
        return False

    existing_workflow = load_workflow_by_id(
        normalized_workflow_id,
        database_file,
    )

    if existing_workflow is None:
        return False

    if (
        normalized_status == "active"
        and not load_workflow_tasks(normalized_workflow_id, database_file)
    ):
        return False

    updated_workflow: Workflow = {
        "workflow_id": existing_workflow["workflow_id"],
        "name": normalized_name,
        "description": normalized_description,
        "status": normalized_status,
        "created_by_user_id": existing_workflow[
            "created_by_user_id"
        ],
        "created_at": existing_workflow["created_at"],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    return update_workflow_in_database(
        updated_workflow,
        database_file,
    )
