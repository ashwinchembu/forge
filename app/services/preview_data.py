"""Sample payloads for preview/demo mode — mirrors production API shapes."""

PROGRAM_START = "2026-05-19"

DASHBOARD = {
    "date": "2026-05-18",
    "week": 1,
    "phase": "cut",
    "expected_workout": "Upper A",
    "score": 78,
    "workout": {
        "exercises": [
            {
                "exercise": "Bench Press (Barbell)",
                "target_weight": 215,
                "actual_weight": 215,
                "target_reps": "6-8",
                "actual_reps": [8, 7, 6, 6],
                "status": "hit",
                "volume_delta_pct": 2.1,
            },
            {
                "exercise": "Bent Over Row (Barbell)",
                "target_weight": 205,
                "actual_weight": 205,
                "target_reps": "6-8",
                "actual_reps": [8, 8, 7],
                "status": "hit",
                "volume_delta_pct": 4.0,
            },
            {
                "exercise": "Incline DB Press",
                "target_weight": 90,
                "actual_weight": 85,
                "target_reps": "8-12",
                "actual_reps": [10, 10, 9],
                "status": "close",
                "volume_delta_pct": -5.2,
            },
        ],
        "hit_rate": 0.67,
    },
    "nutrition": {
        "calories": 2085,
        "target_calories": 2200,
        "protein_g": 172,
        "target_protein_g": 180,
        "carbs_g": 148,
        "fat_g": 58,
        "calorie_delta": -115,
        "protein_delta": -8,
    },
    "recovery": {
        "sleep_hours": 7.4,
        "hrv_ms": 42.5,
        "resting_heart_rate": 54,
        "steps": 8420,
    },
    "recommendations": [
        "Protein 172g is 8g below target. Prioritize protein in remaining meals.",
        "Incline DB Press was close — consider staying at 85 lbs next session if form breaks down.",
    ],
}

WORKOUTS = [
    {
        "_id": "preview-w1",
        "date": "2026-05-18T17:30:00",
        "name": "Upper A",
        "duration_minutes": 62,
        "source": "hevy",
        "exercises": [
            {"name": "Bench Press (Barbell)", "sets": [{"set_number": 1, "weight_lbs": 215, "reps": 8}]},
        ],
        "total_volume_lbs": 12450,
    }
]

NUTRITION = [
    {
        "_id": "preview-n1",
        "date": "2026-05-18T00:00:00",
        "calories": 2085,
        "protein_g": 172,
        "carbs_g": 148,
        "fat_g": 58,
        "fiber_g": 28,
    }
]

RECOVERY = [
    {
        "_id": "preview-r1",
        "date": "2026-05-18T00:00:00",
        "sleep": {"total_hours": 7.4, "deep_hours": 1.8, "rem_hours": 1.6},
        "hrv_ms": 42.5,
        "resting_heart_rate": 54,
        "steps": 8420,
    }
]

BODY_METRICS = [
    {"_id": "preview-b1", "date": "2026-05-18T00:00:00", "weight_lbs": 198.2, "body_fat_pct": 14.1},
    {"_id": "preview-b2", "date": "2026-05-11T00:00:00", "weight_lbs": 199.0, "body_fat_pct": 14.3},
]
