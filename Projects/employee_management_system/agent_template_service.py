from datetime import datetime, timezone
from pathlib import Path

from authorization import (
    MANAGE_AGENT_TEMPLATES,
    user_has_permission,
)
from database import (
    DATABASE_FILE,
    insert_agent_template,
    load_agent_template_by_id,
    load_user_account_by_username,
    update_agent_template_in_database,
)
from models import (
    AGENT_TEMPLATE_STATUS_ACTIVE,
    AGENT_TEMPLATE_STATUS_DRAFT,
    AGENT_TEMPLATE_STATUS_INACTIVE,
    AgentTemplate,
    UserAccount,
    VALID_AGENT_TEMPLATE_STATUSES,
)


MAX_AGENT_TEMPLATE_ID_LENGTH = 100
MAX_AGENT_TEMPLATE_NAME_LENGTH = 120
MAX_AGENT_TEMPLATE_DESCRIPTION_LENGTH = 1000
MAX_AGENT_TEMPLATE_SYSTEM_PROMPT_LENGTH = 10000
MAX_AGENT_TEMPLATE_MODEL_NAME_LENGTH = 100
ALLOWED_AGENT_TEMPLATE_STATUS_TRANSITIONS = {
    AGENT_TEMPLATE_STATUS_DRAFT: frozenset(
        {
            AGENT_TEMPLATE_STATUS_DRAFT,
            AGENT_TEMPLATE_STATUS_ACTIVE,
        }
    ),
    AGENT_TEMPLATE_STATUS_ACTIVE: frozenset(
        {
            AGENT_TEMPLATE_STATUS_ACTIVE,
            AGENT_TEMPLATE_STATUS_INACTIVE,
        }
    ),
    AGENT_TEMPLATE_STATUS_INACTIVE: frozenset(
        {
            AGENT_TEMPLATE_STATUS_INACTIVE,
            AGENT_TEMPLATE_STATUS_ACTIVE,
        }
    ),
}


def create_agent_template(
    current_user: UserAccount,
    agent_template_id: str,
    name: str,
    description: str,
    system_prompt: str,
    model_name: str,
    status: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
    """Create a normalized draft agent template."""
    text_values = (
        agent_template_id,
        name,
        description,
        system_prompt,
        model_name,
        status,
    )

    if (
        not current_user["is_active"]
        or not all(
            isinstance(value, str)
            for value in text_values
        )
    ):
        return False

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
            MANAGE_AGENT_TEMPLATES,
        )
    ):
        return False

    normalized_template_id = (
        agent_template_id.strip().upper()
    )
    normalized_name = name.strip()
    normalized_description = description.strip()
    normalized_system_prompt = system_prompt.strip()
    normalized_model_name = model_name.strip()
    normalized_status = status.strip().casefold()

    if (
        not normalized_template_id
        or len(normalized_template_id)
        > MAX_AGENT_TEMPLATE_ID_LENGTH
        or not normalized_name
        or len(normalized_name)
        > MAX_AGENT_TEMPLATE_NAME_LENGTH
        or len(normalized_description)
        > MAX_AGENT_TEMPLATE_DESCRIPTION_LENGTH
        or not normalized_system_prompt
        or len(normalized_system_prompt)
        > MAX_AGENT_TEMPLATE_SYSTEM_PROMPT_LENGTH
        or not normalized_model_name
        or len(normalized_model_name)
        > MAX_AGENT_TEMPLATE_MODEL_NAME_LENGTH
        or normalized_status
        not in VALID_AGENT_TEMPLATE_STATUSES
        or normalized_status
        != AGENT_TEMPLATE_STATUS_DRAFT
    ):
        return False

    timestamp = datetime.now(timezone.utc).isoformat()

    agent_template: AgentTemplate = {
        "agent_template_id": normalized_template_id,
        "name": normalized_name,
        "description": normalized_description,
        "system_prompt": normalized_system_prompt,
        "model_name": normalized_model_name,
        "status": normalized_status,
        "created_by_user_id": stored_user["user_id"],
        "created_at": timestamp,
        "updated_at": timestamp,
    }

    return insert_agent_template(
        agent_template,
        database_file,
    )


def update_agent_template(
    current_user: UserAccount,
    agent_template_id: str,
    name: str,
    description: str,
    system_prompt: str,
    model_name: str,
    status: str,
    expected_status: str,
    database_file: Path = DATABASE_FILE,
) -> bool:
    """Update a template through an allowed lifecycle transition."""
    text_values = (
        agent_template_id,
        name,
        description,
        system_prompt,
        model_name,
        status,
        expected_status,
    )

    if (
        not current_user["is_active"]
        or not all(
            isinstance(value, str)
            for value in text_values
        )
    ):
        return False

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
            MANAGE_AGENT_TEMPLATES,
        )
    ):
        return False

    normalized_template_id = (
        agent_template_id.strip().upper()
    )
    normalized_name = name.strip()
    normalized_description = description.strip()
    normalized_system_prompt = system_prompt.strip()
    normalized_model_name = model_name.strip()
    normalized_status = status.strip().casefold()
    normalized_expected_status = (
        expected_status.strip().casefold()
    )

    if (
        not normalized_template_id
        or len(normalized_template_id)
        > MAX_AGENT_TEMPLATE_ID_LENGTH
        or not normalized_name
        or len(normalized_name)
        > MAX_AGENT_TEMPLATE_NAME_LENGTH
        or len(normalized_description)
        > MAX_AGENT_TEMPLATE_DESCRIPTION_LENGTH
        or not normalized_system_prompt
        or len(normalized_system_prompt)
        > MAX_AGENT_TEMPLATE_SYSTEM_PROMPT_LENGTH
        or not normalized_model_name
        or len(normalized_model_name)
        > MAX_AGENT_TEMPLATE_MODEL_NAME_LENGTH
        or normalized_status
        not in VALID_AGENT_TEMPLATE_STATUSES
        or normalized_expected_status
        not in VALID_AGENT_TEMPLATE_STATUSES
    ):
        return False

    existing_template = load_agent_template_by_id(
        normalized_template_id,
        database_file,
    )

    if (
        existing_template is None
        or existing_template["status"]
        != normalized_expected_status
    ):
        return False

    allowed_statuses = (
        ALLOWED_AGENT_TEMPLATE_STATUS_TRANSITIONS[
            normalized_expected_status
        ]
    )

    if normalized_status not in allowed_statuses:
        return False

    updated_template: AgentTemplate = {
        "agent_template_id": existing_template[
            "agent_template_id"
        ],
        "name": normalized_name,
        "description": normalized_description,
        "system_prompt": normalized_system_prompt,
        "model_name": normalized_model_name,
        "status": normalized_status,
        "created_by_user_id": existing_template[
            "created_by_user_id"
        ],
        "created_at": existing_template["created_at"],
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    return update_agent_template_in_database(
        updated_template,
        normalized_expected_status,
        database_file,
    )
