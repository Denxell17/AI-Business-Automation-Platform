from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from agent_provider import AgentProvider
from authorization import (
    EXECUTE_AGENT_TEMPLATES,
    user_has_permission,
)
from database import (
    DATABASE_FILE,
    complete_agent_execution,
    fail_agent_execution,
    insert_agent_execution,
    load_agent_execution_by_id,
    load_agent_template_by_id,
    load_user_account_by_username,
)
from models import (
    AGENT_EXECUTION_STATUS_RUNNING,
    AGENT_TEMPLATE_STATUS_ACTIVE,
    AgentExecution,
    UserAccount,
)


MAX_AGENT_EXECUTION_INPUT_LENGTH = 10000
MAX_AGENT_EXECUTION_OUTPUT_LENGTH = 50000
SAFE_AGENT_PROVIDER_ERROR_MESSAGE = (
    "The AI provider could not complete the request."
)


def _load_finished_agent_execution(
    agent_execution_id: str,
    database_file: Path,
) -> AgentExecution | None:
    """Reload the final execution record from the database."""
    return load_agent_execution_by_id(
        agent_execution_id,
        database_file,
    )


def _record_failed_agent_execution(
    agent_execution_id: str,
    database_file: Path,
) -> AgentExecution | None:
    """Store a safe provider failure and reload the record."""
    failed = fail_agent_execution(
        agent_execution_id,
        SAFE_AGENT_PROVIDER_ERROR_MESSAGE,
        datetime.now(timezone.utc).isoformat(),
        database_file,
    )

    if not failed:
        return None

    return _load_finished_agent_execution(
        agent_execution_id,
        database_file,
    )


def execute_agent_template(
    current_user: UserAccount,
    agent_template_id: str,
    input_text: str,
    provider: AgentProvider,
    database_file: Path = DATABASE_FILE,
) -> AgentExecution | None:
    """Execute one Active Agent Template through a provider."""
    if (
        not current_user["is_active"]
        or not isinstance(agent_template_id, str)
        or not isinstance(input_text, str)
    ):
        return None

    normalized_template_id = (
        agent_template_id.strip().upper()
    )
    normalized_input = input_text.strip()

    if (
        not normalized_template_id
        or not normalized_input
        or len(normalized_input)
        > MAX_AGENT_EXECUTION_INPUT_LENGTH
    ):
        return None

    stored_user = load_user_account_by_username(
        current_user["username"],
        database_file,
    )

    if (
        stored_user is None
        or not stored_user["is_active"]
        or stored_user["user_id"]
        != current_user["user_id"]
        or not user_has_permission(
            stored_user,
            EXECUTE_AGENT_TEMPLATES,
        )
    ):
        return None

    agent_template = load_agent_template_by_id(
        normalized_template_id,
        database_file,
    )

    if (
        agent_template is None
        or agent_template["status"]
        != AGENT_TEMPLATE_STATUS_ACTIVE
    ):
        return None

    agent_execution_id = (
        f"AGENT-EXEC-{uuid4().hex.upper()}"
    )
    started_at = datetime.now(
        timezone.utc
    ).isoformat()

    running_execution: AgentExecution = {
        "agent_execution_id": agent_execution_id,
        "agent_template_id": agent_template[
            "agent_template_id"
        ],
        "agent_template_name": agent_template["name"],
        "model_name": agent_template["model_name"],
        "status": AGENT_EXECUTION_STATUS_RUNNING,
        "input_text": normalized_input,
        "output_text": None,
        "error_message": None,
        "requested_by_user_id": stored_user["user_id"],
        "started_at": started_at,
        "finished_at": None,
    }

    inserted = insert_agent_execution(
        running_execution,
        database_file,
    )

    if not inserted:
        return None

    try:
        provider_output = provider.generate_response(
            model_name=agent_template["model_name"],
            system_prompt=agent_template["system_prompt"],
            input_text=normalized_input,
        )
    except Exception:
        return _record_failed_agent_execution(
            agent_execution_id,
            database_file,
        )

    if not isinstance(provider_output, str):
        return _record_failed_agent_execution(
            agent_execution_id,
            database_file,
        )

    normalized_output = provider_output.strip()

    if (
        not normalized_output
        or len(normalized_output)
        > MAX_AGENT_EXECUTION_OUTPUT_LENGTH
    ):
        return _record_failed_agent_execution(
            agent_execution_id,
            database_file,
        )

    completed = complete_agent_execution(
        agent_execution_id,
        normalized_output,
        datetime.now(timezone.utc).isoformat(),
        database_file,
    )

    if not completed:
        return None

    return _load_finished_agent_execution(
        agent_execution_id,
        database_file,
    )