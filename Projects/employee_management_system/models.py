from typing import TypedDict


class Employee(TypedDict):
    employee_id: str
    name: str
    department: str
    position: str
    country: str
    salary: int
    email: str
    phone_number: str
    years_of_experience: int
    company: str
    employment_status: str
    performance_score: int


class UserAccount(TypedDict):
    user_id: int
    username: str
    password_hash: str
    role: str
    is_active: bool


class UserAccountSummary(TypedDict):
    user_id: int
    username: str
    role: str
    is_active: bool

WORKFLOW_STATUS_DRAFT = "draft"
WORKFLOW_STATUS_ACTIVE = "active"
WORKFLOW_STATUS_INACTIVE = "inactive"

VALID_WORKFLOW_STATUSES = frozenset(
    {
        WORKFLOW_STATUS_DRAFT,
        WORKFLOW_STATUS_ACTIVE,
        WORKFLOW_STATUS_INACTIVE,
    }
)


class Workflow(TypedDict):
    workflow_id: str
    name: str
    description: str
    status: str
    created_by_user_id: int
    created_at: str
    updated_at: str


WORKFLOW_TASK_TYPE_MANUAL = "manual"
VALID_WORKFLOW_TASK_TYPES = frozenset({WORKFLOW_TASK_TYPE_MANUAL})


class WorkflowTask(TypedDict):
    task_id: str
    workflow_id: str
    sequence_number: int
    title: str
    instructions: str
    task_type: str
    is_required: bool
    created_at: str
    updated_at: str


WORKFLOW_EXECUTION_STATUS_RUNNING = "running"
WORKFLOW_EXECUTION_STATUS_COMPLETED = "completed"
WORKFLOW_EXECUTION_STATUS_FAILED = "failed"
VALID_WORKFLOW_EXECUTION_STATUSES = frozenset(
    {
        WORKFLOW_EXECUTION_STATUS_RUNNING,
        WORKFLOW_EXECUTION_STATUS_COMPLETED,
        WORKFLOW_EXECUTION_STATUS_FAILED,
    }
)


class WorkflowExecution(TypedDict):
    execution_id: str
    workflow_id: str
    workflow_name: str
    status: str
    started_by_user_id: int
    started_at: str
    finished_at: str | None
    result_summary: str


class WorkflowTaskExecution(TypedDict):
    task_execution_id: str
    execution_id: str
    task_id: str
    sequence_number: int
    task_title: str
    status: str
    started_at: str
    finished_at: str | None
    result_summary: str


WORKFLOW_SCHEDULE_TYPE_MANUAL = "manual"
WORKFLOW_SCHEDULE_TYPE_DAILY = "daily"
WORKFLOW_SCHEDULE_TYPE_WEEKLY = "weekly"
VALID_WORKFLOW_SCHEDULE_TYPES = frozenset(
    {
        WORKFLOW_SCHEDULE_TYPE_MANUAL,
        WORKFLOW_SCHEDULE_TYPE_DAILY,
        WORKFLOW_SCHEDULE_TYPE_WEEKLY,
    }
)
VALID_WORKFLOW_SCHEDULE_WEEKDAYS = frozenset(
    {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
)


class WorkflowSchedule(TypedDict):
    schedule_id: str
    workflow_id: str
    schedule_type: str
    scheduled_time: str | None
    day_of_week: str | None
    is_enabled: bool
    created_by_user_id: int
    created_at: str
    updated_at: str


class WorkflowScheduleEvaluation(TypedDict):
    schedule_id: str
    workflow_id: str
    is_due: bool
    scheduled_for_utc: str | None
    next_eligible_at_utc: str | None
    time_zone: str


class WorkflowScheduleOccurrence(TypedDict):
    occurrence_id: str
    schedule_id: str
    workflow_id: str
    scheduled_for_utc: str
    claimed_at: str


class PayrollSummary(TypedDict):
    performance_rating: str
    bonus_rate: float
    annual_salary: int
    thirteenth_month_pay: int
    estimated_bonus: float
    monthly_tax: float
    net_monthly_salary: float
    allowance: int
    overtime: int
    monthly_income: int
    net_monthly_income: float
    total_compensation: float


class WorkforceSummary(TypedDict):
    total_employees: int
    total_departments: int
    total_monthly_payroll: int
    average_salary: float
    highest_paid_employee: Employee | None
    lowest_paid_employee: Employee | None
    salary_range: int
    department_counts: dict[str, int]
    department_payrolls: dict[str, int]
    department_average_salaries: dict[str, float]
    highest_payroll_department: str | None
    highest_average_salary_department: str | None
    lowest_payroll_department: str | None
    lowest_average_salary_department: str | None
    largest_department: str | None
    smallest_department: str | None
