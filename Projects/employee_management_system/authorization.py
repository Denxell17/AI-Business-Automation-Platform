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
    },
    "viewer": {
        VIEW_EMPLOYEE,
        VIEW_PAYROLL,
        EXPORT_REPORT,
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