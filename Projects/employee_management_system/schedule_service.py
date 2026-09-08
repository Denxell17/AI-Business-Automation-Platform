"""Deterministic workflow-schedule eligibility and occurrence claiming."""

from datetime import datetime, time, timedelta, timezone, tzinfo
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from database import (
    DATABASE_FILE,
    claim_workflow_schedule_occurrence,
    load_enabled_workflow_schedules,
)
from config import WORKFLOW_TIME_ZONE
from models import (
    WORKFLOW_SCHEDULE_TYPE_DAILY,
    WORKFLOW_SCHEDULE_TYPE_MANUAL,
    WORKFLOW_SCHEDULE_TYPE_WEEKLY,
    WorkflowSchedule,
    WorkflowScheduleEvaluation,
    WorkflowScheduleOccurrence,
)


DEFAULT_WORKFLOW_TIME_ZONE = WORKFLOW_TIME_ZONE
DEFAULT_SCHEDULE_GRACE_MINUTES = 5


def _time_zone(time_zone_name: str) -> tzinfo:
    try:
        return ZoneInfo(time_zone_name)
    except (TypeError, ZoneInfoNotFoundError) as error:
        if time_zone_name == "Asia/Shanghai":
            return timezone(timedelta(hours=8), name="Asia/Shanghai")
        raise ValueError("A valid IANA time-zone name is required.") from error


def _aware_current_time(current_time: datetime) -> datetime:
    if not isinstance(current_time, datetime) or current_time.tzinfo is None:
        raise ValueError("The current time must include a time zone.")
    return current_time


def _schedule_time(schedule: WorkflowSchedule) -> time | None:
    stored_time = schedule["scheduled_time"]
    if schedule["schedule_type"] == WORKFLOW_SCHEDULE_TYPE_MANUAL:
        return None
    if stored_time is None:
        return None
    try:
        return time.fromisoformat(stored_time)
    except ValueError:
        return None


def _candidate_for_local_date(
    schedule: WorkflowSchedule,
    local_time: datetime,
    time_zone: tzinfo,
) -> datetime | None:
    scheduled_clock = _schedule_time(schedule)
    if scheduled_clock is None:
        return None
    if (
        schedule["schedule_type"] == WORKFLOW_SCHEDULE_TYPE_WEEKLY
        and schedule["day_of_week"] != local_time.strftime("%A").casefold()
    ):
        return None
    return datetime.combine(local_time.date(), scheduled_clock, time_zone)


def evaluate_workflow_schedule(
    schedule: WorkflowSchedule,
    current_time: datetime,
    time_zone_name: str = DEFAULT_WORKFLOW_TIME_ZONE,
    grace_minutes: int = DEFAULT_SCHEDULE_GRACE_MINUTES,
) -> WorkflowScheduleEvaluation:
    """Evaluate one schedule without reading or changing application data."""
    if type(grace_minutes) is not int or grace_minutes <= 0:
        raise ValueError("The schedule grace period must be a positive integer.")
    aware_time = _aware_current_time(current_time)
    selected_zone = _time_zone(time_zone_name)
    local_now = aware_time.astimezone(selected_zone)
    utc_now = aware_time.astimezone(timezone.utc)
    candidate = _candidate_for_local_date(schedule, local_now, selected_zone)

    scheduled_for_utc = candidate.astimezone(timezone.utc) if candidate else None
    is_due = bool(
        schedule["is_enabled"]
        and scheduled_for_utc is not None
        and scheduled_for_utc <= utc_now
        < scheduled_for_utc + timedelta(minutes=grace_minutes)
    )

    next_candidate = candidate
    if next_candidate is not None and utc_now >= (
        next_candidate.astimezone(timezone.utc)
        + timedelta(minutes=grace_minutes)
    ):
        interval = 1 if schedule["schedule_type"] == WORKFLOW_SCHEDULE_TYPE_DAILY else 7
        next_candidate += timedelta(days=interval)
    elif next_candidate is None and schedule["schedule_type"] == WORKFLOW_SCHEDULE_TYPE_WEEKLY:
        weekday = schedule["day_of_week"]
        if weekday:
            weekday_number = (
                "monday", "tuesday", "wednesday", "thursday",
                "friday", "saturday", "sunday",
            ).index(weekday)
            days_ahead = (weekday_number - local_now.weekday()) % 7
            scheduled_clock = _schedule_time(schedule)
            if scheduled_clock is not None:
                next_candidate = datetime.combine(
                    local_now.date() + timedelta(days=days_ahead),
                    scheduled_clock,
                    selected_zone,
                )
                if utc_now >= (
                    next_candidate.astimezone(timezone.utc)
                    + timedelta(minutes=grace_minutes)
                ):
                    next_candidate += timedelta(days=7)

    next_eligible = None
    if schedule["is_enabled"] and next_candidate is not None:
        next_eligible = next_candidate.astimezone(timezone.utc).isoformat()
    return {
        "schedule_id": schedule["schedule_id"],
        "workflow_id": schedule["workflow_id"],
        "is_due": is_due,
        "scheduled_for_utc": (
            scheduled_for_utc.isoformat() if scheduled_for_utc else None
        ),
        "next_eligible_at_utc": next_eligible,
        "time_zone": time_zone_name,
    }


def find_due_workflow_schedules(
    current_time: datetime,
    database_file: Path = DATABASE_FILE,
    time_zone_name: str = DEFAULT_WORKFLOW_TIME_ZONE,
    grace_minutes: int = DEFAULT_SCHEDULE_GRACE_MINUTES,
) -> list[WorkflowScheduleEvaluation]:
    """Return due enabled schedules without claiming or starting them."""
    return [
        evaluation
        for schedule in load_enabled_workflow_schedules(database_file)
        if (
            evaluation := evaluate_workflow_schedule(
                schedule, current_time, time_zone_name, grace_minutes,
            )
        )["is_due"]
    ]


def evaluate_workflow_schedule_list(
    schedules: list[WorkflowSchedule],
    current_time: datetime,
    time_zone_name: str = DEFAULT_WORKFLOW_TIME_ZONE,
    grace_minutes: int = DEFAULT_SCHEDULE_GRACE_MINUTES,
) -> dict[str, WorkflowScheduleEvaluation]:
    """Build schedule-ID keyed display information without changing data."""
    return {
        schedule["schedule_id"]: evaluate_workflow_schedule(
            schedule, current_time, time_zone_name, grace_minutes,
        )
        for schedule in schedules
    }


def claim_due_workflow_schedules(
    current_time: datetime,
    database_file: Path = DATABASE_FILE,
    time_zone_name: str = DEFAULT_WORKFLOW_TIME_ZONE,
    grace_minutes: int = DEFAULT_SCHEDULE_GRACE_MINUTES,
) -> list[WorkflowScheduleOccurrence]:
    """Claim each due occurrence once without starting workflow tasks."""
    claimed_at = _aware_current_time(current_time).astimezone(timezone.utc).isoformat()
    claimed: list[WorkflowScheduleOccurrence] = []
    for due_schedule in find_due_workflow_schedules(
        current_time, database_file, time_zone_name, grace_minutes,
    ):
        scheduled_for_utc = due_schedule["scheduled_for_utc"]
        if scheduled_for_utc is None:
            continue
        occurrence: WorkflowScheduleOccurrence = {
            "occurrence_id": f"WFSO-{uuid4().hex.upper()}",
            "schedule_id": due_schedule["schedule_id"],
            "workflow_id": due_schedule["workflow_id"],
            "scheduled_for_utc": scheduled_for_utc,
            "claimed_at": claimed_at,
        }
        if claim_workflow_schedule_occurrence(occurrence, database_file):
            claimed.append(occurrence)
    return claimed
