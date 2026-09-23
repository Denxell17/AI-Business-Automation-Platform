from models import UserAccount


REGISTER_EMPLOYEE = "employee.register"
VIEW_EMPLOYEE = "employee.view"
VIEW_PAYROLL = "payroll.view"
UPDATE_EMPLOYEE = "employee.update"
DELETE_EMPLOYEE = "employee.delete"
EXPORT_REPORT = "report.export"
BACKUP_DATABASE = "database.backup"
RESTORE_DATABASE = "database.restore"
MANAGE_USER_ACCOUNTS = "users.manage"
MANAGE_WORKFLOWS = "workflows.manage"
VIEW_WORKFLOWS = "workflows.view"
MANAGE_AGENT_TEMPLATES = "agent_templates.manage"
EXECUTE_AGENT_TEMPLATES = "agent_templates.execute"
VIEW_AGENT_TEMPLATES = "agent_templates.view"
VIEW_ACTIVITY_LOG = "activity_log.view"
VIEW_INTEGRATION_STATUS = "integrations.view"
VIEW_CRM = "crm.view"
MANAGE_CRM = "crm.manage"
VIEW_INVOICES = "invoices.view"
MANAGE_INVOICES = "invoices.manage"


ROLE_PERMISSIONS = {
    "admin": {
        REGISTER_EMPLOYEE,
        VIEW_EMPLOYEE,
        VIEW_PAYROLL,
        UPDATE_EMPLOYEE,
        DELETE_EMPLOYEE,
        EXPORT_REPORT,
        BACKUP_DATABASE,
        RESTORE_DATABASE,
        MANAGE_USER_ACCOUNTS,
        MANAGE_WORKFLOWS,
        VIEW_WORKFLOWS,
        MANAGE_AGENT_TEMPLATES,
        EXECUTE_AGENT_TEMPLATES,
        VIEW_AGENT_TEMPLATES,
        VIEW_ACTIVITY_LOG,
        VIEW_INTEGRATION_STATUS,
        VIEW_CRM,
        MANAGE_CRM,
        VIEW_INVOICES,
        MANAGE_INVOICES,
    },
    "viewer": {
        VIEW_EMPLOYEE,
        VIEW_PAYROLL,
        EXPORT_REPORT,
        VIEW_WORKFLOWS,
        VIEW_AGENT_TEMPLATES,
        VIEW_CRM,
        VIEW_INVOICES,
    },
}


def user_has_permission(
    user_account: UserAccount,
    permission: str,
) -> bool:
    allowed_permissions = ROLE_PERMISSIONS.get(
        user_account["role"],
        set(),
    )

    return permission in allowed_permissions
