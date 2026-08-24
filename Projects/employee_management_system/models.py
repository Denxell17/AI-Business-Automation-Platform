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