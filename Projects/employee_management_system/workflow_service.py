from datetime import datetime, timezone
from pathlib import Path
import re
from uuid import uuid4

from authorization import (
    MANAGE_WORKFLOWS,
    user_has_permission,
)
from database import (
    DATABASE_FILE,
    delete_workflow_task,
    finish_workflow_execution,
    finish_workflow_task_execution,
    insert_workflow,
    insert_workflow_execution,
    insert_workflow_task_executions,
    insert_workflow_task,
    insert_workflow_schedule,
    load_user_account_by_username,
    load_workflow_by_id,
    load_workflow_task_by_id,
    load_workflow_tasks,
    load_workflow_schedule_by_id,
    resequence_workflow_tasks,
    update_workflow_task,
    update_workflow_in_database,
    update_workflow_schedule_enabled,
)
from models import (
    UserAccount,
    VALID_WORKFLOW_STATUSES,
    Workflow,
    WorkflowExecution,
    WorkflowTaskExecution,
    WorkflowTask,
    WorkflowSchedule,
    VALID_WORKFLOW_TASK_TYPES,
    VALID_WORKFLOW_SCHEDULE_TYPES,
    VALID_WORKFLOW_SCHEDULE_WEEKDAYS,
)


SCHEDULE_TIME_PATTERN = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d")


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


def create_workflow_schedule(
    current_user: UserAccount,
    schedule_id: str,
    workflow_id: str,
    schedule_type: str,
    scheduled_time: str,
    day_of_week: str,
    is_enabled: bool,
    database_file: Path = DATABASE_FILE,
) -> bool:
    """Create a validated stored schedule for an active workflow."""
    if (
        not current_user["is_active"]
        or not all(isinstance(value, str) for value in (
            schedule_id, workflow_id, schedule_type, scheduled_time, day_of_week,
        ))
        or type(is_enabled) is not bool
    ):
        return False
    stored_user = load_user_account_by_username(current_user["username"], database_file)
    if (
        stored_user is None or not stored_user["is_active"]
        or stored_user["user_id"] != current_user["user_id"]
        or stored_user["role"] != "admin"
        or not user_has_permission(stored_user, MANAGE_WORKFLOWS)
    ):
        return False

    normalized_schedule_id = schedule_id.strip().upper()
    normalized_workflow_id = workflow_id.strip().upper()
    normalized_type = schedule_type.strip().casefold()
    normalized_time = scheduled_time.strip()
    normalized_day = day_of_week.strip().casefold()
    workflow = load_workflow_by_id(normalized_workflow_id, database_file)
    if (
        not normalized_schedule_id
        or normalized_type not in VALID_WORKFLOW_SCHEDULE_TYPES
        or workflow is None
        or workflow["status"] != "active"
    ):
        return False
    if normalized_type == "manual":
        stored_time = None
        stored_day = None
    elif normalized_type == "daily":
        if SCHEDULE_TIME_PATTERN.fullmatch(normalized_time) is None:
            return False
        stored_time = normalized_time
        stored_day = None
    else:
        if (
            SCHEDULE_TIME_PATTERN.fullmatch(normalized_time) is None
            or normalized_day not in VALID_WORKFLOW_SCHEDULE_WEEKDAYS
        ):
            return False
        stored_time = normalized_time
        stored_day = normalized_day

    timestamp = datetime.now(timezone.utc).isoformat()
    schedule: WorkflowSchedule = {
        "schedule_id": normalized_schedule_id,
        "workflow_id": normalized_workflow_id,
        "schedule_type": normalized_type,
        "scheduled_time": stored_time,
        "day_of_week": stored_day,
        "is_enabled": is_enabled,
        "created_by_user_id": stored_user["user_id"],
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    return insert_workflow_schedule(schedule, database_file)


def set_workflow_schedule_enabled(
    current_user: UserAccount,
    workflow_id: str,
    schedule_id: str,
    is_enabled: bool,
    database_file: Path = DATABASE_FILE,
) -> bool:
    """Enable or disable one schedule after live administrator validation."""
    if (
        not current_user["is_active"]
        or not all(isinstance(value, str) and value.strip() for value in (
            workflow_id, schedule_id,
        ))
        or type(is_enabled) is not bool
    ):
        return False
    stored_user = load_user_account_by_username(current_user["username"], database_file)
    if (
        stored_user is None or not stored_user["is_active"]
        or stored_user["user_id"] != current_user["user_id"]
        or stored_user["role"] != "admin"
        or not user_has_permission(stored_user, MANAGE_WORKFLOWS)
    ):
        return False
    normalized_workflow_id = workflow_id.strip().upper()
    normalized_schedule_id = schedule_id.strip().upper()
    schedule = load_workflow_schedule_by_id(normalized_schedule_id, database_file)
    if schedule is None or schedule["workflow_id"] != normalized_workflow_id:
        return False
    return update_workflow_schedule_enabled(
        normalized_workflow_id, normalized_schedule_id, is_enabled,
        datetime.now(timezone.utc).isoformat(), database_file,
    )


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


def remove_workflow_task(current_user: UserAccount, workflow_id: str, task_id: str,
                         database_file: Path = DATABASE_FILE) -> bool:
    if not current_user["is_active"]:
        return False
    stored_user = load_user_account_by_username(current_user["username"], database_file)
    if (
        stored_user is None or not stored_user["is_active"]
        or stored_user["user_id"] != current_user["user_id"]
        or not user_has_permission(stored_user, MANAGE_WORKFLOWS)
        or not all(isinstance(value, str) and value.strip() for value in (workflow_id, task_id))
    ):
        return False
    return delete_workflow_task(
        workflow_id.strip().upper(), task_id.strip().upper(),
        datetime.now(timezone.utc).isoformat(), database_file,
    )


def start_workflow_execution(
    current_user: UserAccount,
    workflow_id: str,
    database_file: Path = DATABASE_FILE,
) -> WorkflowExecution | None:
    """Record an administrator-started run of an active workflow."""
    if (
        not current_user["is_active"]
        or not isinstance(workflow_id, str)
        or not workflow_id.strip()
    ):
        return None
    stored_user = load_user_account_by_username(
        current_user["username"], database_file,
    )
    if (
        stored_user is None
        or not stored_user["is_active"]
        or stored_user["user_id"] != current_user["user_id"]
        or not user_has_permission(stored_user, MANAGE_WORKFLOWS)
    ):
        return None
    workflow = load_workflow_by_id(workflow_id.strip().upper(), database_file)
    if workflow is None or workflow["status"] != "active":
        return None
    started_at = datetime.now(timezone.utc).isoformat()
    execution: WorkflowExecution = {
        "execution_id": f"WFE-{uuid4().hex.upper()}",
        "workflow_id": workflow["workflow_id"],
        "workflow_name": workflow["name"],
        "status": "running",
        "started_by_user_id": stored_user["user_id"],
        "started_at": started_at,
        "finished_at": None,
        "result_summary": "Execution started.",
    }
    if not insert_workflow_execution(execution, database_file):
        return None
    task_records: list[WorkflowTaskExecution] = [
        {"task_execution_id": f"WFTE-{uuid4().hex.upper()}", "execution_id": execution["execution_id"],
         "task_id": task["task_id"], "sequence_number": task["sequence_number"],
         "task_title": task["title"], "status": "running", "started_at": started_at,
         "finished_at": None, "result_summary": "Task execution started."}
        for task in load_workflow_tasks(workflow["workflow_id"], database_file)
    ]
    return execution if insert_workflow_task_executions(task_records, database_file) else None


def finish_workflow_task_execution_record(
    current_user: UserAccount,
    workflow_id: str,
    execution_id: str,
    task_execution_id: str,
    status: str,
    result_summary: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
    """Validate the live administrator and a task's terminal outcome."""
    values = (workflow_id, execution_id, task_execution_id, status, result_summary)
    if (
        not current_user["is_active"]
        or not all(isinstance(value, str) and value.strip() for value in values)
        or status.strip().casefold() not in {"completed", "failed"}
    ):
        return False
    stored_user = load_user_account_by_username(current_user["username"], database_file)
    if (
        stored_user is None or not stored_user["is_active"]
        or stored_user["user_id"] != current_user["user_id"]
        or stored_user["role"] != "admin"
        or not user_has_permission(stored_user, MANAGE_WORKFLOWS)
    ):
        return False
    return finish_workflow_task_execution(
        workflow_id.strip().upper(), execution_id.strip().upper(),
        task_execution_id.strip().upper(), status.strip().casefold(),
        datetime.now(timezone.utc).isoformat(), result_summary.strip(), database_file,
    )


def finish_workflow_execution_record(
    current_user: UserAccount,
    execution_id: str,
    status: str,
    result_summary: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
    if (
        not current_user["is_active"]
        or not all(isinstance(value, str) for value in (execution_id, status, result_summary))
        or status.strip().casefold() not in {"completed", "failed"}
    ):
        return False
    stored_user = load_user_account_by_username(current_user["username"], database_file)
    if (
        stored_user is None or not stored_user["is_active"]
        or stored_user["user_id"] != current_user["user_id"]
        or not user_has_permission(stored_user, MANAGE_WORKFLOWS)
    ):
        return False
    return finish_workflow_execution(
        execution_id.strip().upper(), status.strip().casefold(),
        datetime.now(timezone.utc).isoformat(), result_summary.strip(), database_file,
    )
