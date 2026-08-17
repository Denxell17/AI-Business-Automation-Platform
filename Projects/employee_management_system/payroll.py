from config import (
    DEFAULT_ALLOWANCE,
    DEFAULT_OVERTIME,
    MONTHS_PER_YEAR,
    TAX_RATE,
)
from models import (
    Employee,
    PayrollSummary,
)


def determine_performance(
    performance_score: int,
) -> tuple[str, float]:
    if performance_score < 0 or performance_score > 100:
        return "Invalid Score", 0
    elif performance_score >= 90:
        return "Outstanding", 0.15
    elif performance_score >= 80:
        return "Very Good", 0.10
    elif performance_score >= 70:
        return "Good", 0.05
    else:
        return "Needs Improvement", 0


def calculate_payroll(
    employee: Employee,
) -> PayrollSummary:
    salary = employee["salary"]

    performance_rating, bonus_rate = determine_performance(
        employee["performance_score"]
    )

    annual_salary = salary * MONTHS_PER_YEAR
    thirteenth_month_pay = salary
    estimated_bonus = annual_salary * bonus_rate
    monthly_tax = salary * TAX_RATE
    net_monthly_salary = salary - monthly_tax
    allowance = DEFAULT_ALLOWANCE
    overtime = DEFAULT_OVERTIME
    monthly_income = salary + allowance

    net_monthly_income = (
        salary
        + allowance
        + overtime
        - monthly_tax
    )

    total_compensation = (
        annual_salary
        + thirteenth_month_pay
        + estimated_bonus
    )

    return {
        "performance_rating": performance_rating,
        "bonus_rate": bonus_rate,
        "annual_salary": annual_salary,
        "thirteenth_month_pay": thirteenth_month_pay,
        "estimated_bonus": estimated_bonus,
        "monthly_tax": monthly_tax,
        "net_monthly_salary": net_monthly_salary,
        "allowance": allowance,
        "overtime": overtime,
        "monthly_income": monthly_income,
        "net_monthly_income": net_monthly_income,
        "total_compensation": total_compensation,
    }