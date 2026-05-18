"""
Preview/demo data — used when PREVIEW_MODE=true.
Mirrors production API shapes but uses realistic placeholder data.
Body metrics are empty until real data comes in from Apple Health.
"""

from datetime import date

PROGRAM_START = "2026-05-22"


def _get_today_schedule():
    weekday = date.today().weekday()
    schedule = {3: "Upper A", 4: "Lower A", 0: "Upper B", 1: "Lower B"}
    return schedule.get(weekday)


def get_dashboard():
    today = date.today()
    expected = _get_today_schedule()
    is_rest_day = expected is None

    dashboard = {
        "date": str(today),
        "week": 1,
        "phase": "cut",
        "expected_workout": expected,
        "score": None,
        "workout": None,
        "nutrition": None,
        "recovery": None,
        "recommendations": [],
    }

    if is_rest_day:
        dashboard["recommendations"] = [
            "Rest day. Light cardio (30 min incline walk) for recovery.",
        ]
        dashboard["score"] = 0
    else:
        dashboard["recommendations"] = [
            f"Today is {expected}. Log your workout in Hevy and it will sync automatically.",
            "Program starts Thursday May 22. Weights and targets are set for week 1.",
        ]

    return dashboard


DASHBOARD = get_dashboard()

WORKOUTS = []

NUTRITION = []

RECOVERY = []

BODY_METRICS = []
