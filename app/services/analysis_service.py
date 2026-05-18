from datetime import datetime, date, timedelta
from app.database import workouts_col, nutrition_col, recovery_col, body_metrics_col

# Program targets by week and phase
PHASES = {
    "cut": {"weeks": (1, 12), "calories": 2200, "protein_g": 180, "carbs_g": 155, "fat_g": 60},
    "cut_late": {"weeks": (9, 12), "calories": 2300, "protein_g": 180, "carbs_g": 175, "fat_g": 60},
    "reverse": {"weeks": (13, 16), "calories_start": 2500, "calories_end": 2900, "protein_g": 190},
    "bulk": {"weeks": (17, 33), "calories": 3100, "protein_g": 200},
}

# Exercise targets per day with weekly weight progression
PROGRAM = {
    "Upper A": {
        "Bench Press (Barbell)": {"sets": 4, "rep_low": 6, "rep_high": 8, "rest": 180,
            "weekly_weights": {1:215,2:215,3:215,4:220,5:215,6:220,7:225,8:225,9:230,10:220,11:230,12:235}},
        "Bent Over Row (Barbell)": {"sets": 3, "rep_low": 6, "rep_high": 8, "rest": 120,
            "weekly_weights": {1:205,2:205,3:210,4:210,5:205,6:210,7:215,8:215,9:220,10:210,11:220,12:225}},
        "Incline DB Press": {"sets": 3, "rep_low": 8, "rep_high": 12, "rest": 90,
            "weekly_weights": {1:90,2:90,3:95,4:95,5:90,6:95,7:100,8:100,9:100,10:95,11:105,12:105}},
        "Seated Cable Row (V-Grip)": {"sets": 3, "rep_low": 8, "rep_high": 12, "rest": 90,
            "weekly_weights": {1:195,2:200,3:200,4:205,5:195,6:205,7:210,8:210,9:215,10:205,11:215,12:220}},
        "Lateral Raise (Cable)": {"sets": 3, "rep_low": 12, "rep_high": 15, "rest": 60,
            "weekly_weights": {1:55,2:55,3:60,4:60,5:55,6:60,7:60,8:65,9:65,10:60,11:65,12:70}},
        "Triceps Pushdown": {"sets": 3, "rep_low": 10, "rep_high": 12, "rest": 60,
            "weekly_weights": {1:50,2:50,3:55,4:55,5:50,6:55,7:55,8:60,9:60,10:55,11:60,12:60}},
        "Preacher Curl (Machine)": {"sets": 3, "rep_low": 10, "rep_high": 12, "rest": 60,
            "weekly_weights": {1:85,2:85,3:90,4:90,5:85,6:90,7:90,8:95,9:95,10:90,11:95,12:100}},
    },
    "Lower A": {
        "Hack Squat (Machine)": {"sets": 3, "rep_low": 6, "rep_high": 8, "rest": 120,
            "weekly_weights": {1:250,2:250,3:260,4:260,5:250,6:260,7:270,8:270,9:280,10:260,11:280,12:290}},
        "Leg Press (Machine)": {"sets": 3, "rep_low": 8, "rep_high": 12, "rest": 120,
            "weekly_weights": {1:520,2:530,3:530,4:540,5:520,6:540,7:550,8:550,9:560,10:540,11:560,12:570}},
        "Leg Extension (Machine)": {"sets": 3, "rep_low": 10, "rep_high": 15, "rest": 60,
            "weekly_weights": {1:430,2:440,3:440,4:450,5:430,6:450,7:460,8:460,9:470,10:450,11:470,12:480}},
        "Lying Leg Curl (Machine)": {"sets": 3, "rep_low": 8, "rep_high": 12, "rest": 90,
            "weekly_weights": {1:200,2:200,3:210,4:210,5:200,6:210,7:210,8:220,9:220,10:210,11:220,12:230}},
        "Standing Calf Raise": {"sets": 4, "rep_low": 8, "rep_high": 12, "rest": 60,
            "weekly_weights": {1:340,2:340,3:350,4:350,5:340,6:350,7:360,8:360,9:370,10:350,11:370,12:380}},
        "Cable Crunch": {"sets": 3, "rep_low": 10, "rep_high": 15, "rest": 60,
            "weekly_weights": {1:210,2:210,3:220,4:220,5:210,6:220,7:230,8:230,9:240,10:220,11:240,12:240}},
    },
    "Upper B": {
        "Close-Grip Bench Press": {"sets": 3, "rep_low": 6, "rep_high": 8, "rest": 150,
            "weekly_weights": {1:200,2:200,3:205,4:205,5:200,6:205,7:210,8:210,9:215,10:205,11:215,12:220}},
        "Iso-Lateral Row (Machine)": {"sets": 3, "rep_low": 8, "rep_high": 10, "rest": 90,
            "weekly_weights": {1:310,2:310,3:320,4:320,5:310,6:320,7:330,8:330,9:340,10:320,11:340,12:350}},
        "Shoulder Press (Machine)": {"sets": 3, "rep_low": 8, "rep_high": 10, "rest": 90,
            "weekly_weights": {1:200,2:200,3:210,4:210,5:200,6:210,7:210,8:220,9:220,10:210,11:220,12:230}},
        "Butterfly (Pec Deck)": {"sets": 3, "rep_low": 10, "rep_high": 15, "rest": 60,
            "weekly_weights": {1:270,2:280,3:280,4:290,5:270,6:290,7:290,8:300,9:300,10:280,11:300,12:310}},
        "OH Triceps Extension (Cable)": {"sets": 3, "rep_low": 10, "rep_high": 12, "rest": 60,
            "weekly_weights": {1:85,2:85,3:90,4:90,5:85,6:90,7:90,8:95,9:95,10:90,11:95,12:100}},
        "Behind the Back Curl (Cable)": {"sets": 3, "rep_low": 10, "rep_high": 12, "rest": 60,
            "weekly_weights": {1:75,2:75,3:80,4:80,5:75,6:80,7:80,8:85,9:85,10:80,11:85,12:90}},
        "Lateral Raise (Cable)": {"sets": 3, "rep_low": 12, "rep_high": 15, "rest": 60,
            "weekly_weights": {1:55,2:55,3:60,4:60,5:55,6:60,7:60,8:65,9:65,10:60,11:65,12:70}},
    },
    "Lower B": {
        "Romanian Deadlift (Barbell)": {"sets": 3, "rep_low": 6, "rep_high": 8, "rest": 120,
            "weekly_weights": {1:185,2:185,3:195,4:195,5:185,6:195,7:205,8:205,9:210,10:195,11:210,12:215}},
        "Hip Thrust (Machine)": {"sets": 3, "rep_low": 8, "rep_high": 12, "rest": 90,
            "weekly_weights": {1:220,2:220,3:230,4:230,5:220,6:230,7:230,8:240,9:240,10:230,11:240,12:250}},
        "Lying Leg Curl (Machine)": {"sets": 3, "rep_low": 8, "rep_high": 12, "rest": 90,
            "weekly_weights": {1:200,2:200,3:210,4:210,5:200,6:210,7:210,8:220,9:220,10:210,11:220,12:230}},
        "Leg Extension (Machine)": {"sets": 3, "rep_low": 10, "rep_high": 15, "rest": 60,
            "weekly_weights": {1:430,2:440,3:440,4:450,5:430,6:450,7:460,8:460,9:470,10:450,11:470,12:480}},
        "Standing Calf Raise": {"sets": 4, "rep_low": 8, "rep_high": 12, "rest": 60,
            "weekly_weights": {1:340,2:340,3:350,4:350,5:340,6:350,7:360,8:360,9:370,10:350,11:370,12:380}},
        "Cable Twist (Up to Down)": {"sets": 3, "rep_low": 10, "rep_high": 12, "rest": 60,
            "weekly_weights": {1:130,2:130,3:140,4:140,5:130,6:140,7:140,8:150,9:150,10:140,11:150,12:160}},
    },
}

SCHEDULE = {0: "Upper A", 1: "Lower A", 3: "Upper B", 4: "Lower B"}  # Mon=0, Tue=1, Thu=3, Fri=4


def get_program_week(start_date: date, current_date: date) -> int:
    delta = (current_date - start_date).days
    return min(max(delta // 7 + 1, 1), 12)


def get_phase(week: int) -> dict:
    if week <= 8:
        return PHASES["cut"]
    elif week <= 12:
        return PHASES["cut_late"]
    elif week <= 16:
        return PHASES["reverse"]
    else:
        return PHASES["bulk"]


async def analyze_day(target_date: date, program_start: date) -> dict:
    week = get_program_week(program_start, target_date)
    phase = get_phase(week)
    weekday = target_date.weekday()
    expected_day = SCHEDULE.get(weekday)

    dt = datetime.combine(target_date, datetime.min.time())
    result = {
        "date": str(target_date),
        "week": week,
        "phase": "cut" if week <= 12 else "reverse" if week <= 16 else "bulk",
        "expected_workout": expected_day,
        "workout": None,
        "nutrition": None,
        "recovery": None,
        "recommendations": [],
        "score": 0,
    }
    score_components = []

    # --- Workout Analysis ---
    if expected_day:
        workout = await workouts_col.find_one({
            "date": {"$gte": dt, "$lt": dt + timedelta(days=1)}
        })
        if workout:
            targets = PROGRAM.get(expected_day, {})
            exercise_results = []
            for ex_name, target in targets.items():
                target_weight = target["weekly_weights"].get(week, 0)
                # fuzzy match exercise name
                actual_ex = None
                for ex in workout.get("exercises", []):
                    if _fuzzy_match(ex_name, ex.get("name", "")):
                        actual_ex = ex
                        break

                if actual_ex:
                    actual_sets = actual_ex.get("sets", [])
                    actual_weight = actual_sets[0]["weight_lbs"] if actual_sets else 0
                    actual_reps = [s["reps"] for s in actual_sets]
                    target_vol = target_weight * target["sets"] * ((target["rep_low"] + target["rep_high"]) / 2)
                    actual_vol = sum(s["weight_lbs"] * s["reps"] for s in actual_sets)
                    vol_delta = ((actual_vol - target_vol) / target_vol * 100) if target_vol else 0

                    if actual_weight >= target_weight and all(r >= target["rep_low"] for r in actual_reps):
                        status = "hit"
                    elif actual_weight >= target_weight * 0.95:
                        status = "close"
                    else:
                        status = "missed"

                    exercise_results.append({
                        "exercise": ex_name,
                        "target_weight": target_weight,
                        "actual_weight": round(actual_weight, 1),
                        "target_reps": f'{target["rep_low"]}-{target["rep_high"]}',
                        "actual_reps": actual_reps,
                        "status": status,
                        "volume_delta_pct": round(vol_delta, 1),
                    })
                else:
                    exercise_results.append({
                        "exercise": ex_name, "status": "no_data",
                        "target_weight": target_weight,
                        "target_reps": f'{target["rep_low"]}-{target["rep_high"]}',
                    })

            hit_rate = sum(1 for e in exercise_results if e["status"] == "hit") / max(len(exercise_results), 1)
            score_components.append(hit_rate * 40)
            result["workout"] = {"exercises": exercise_results, "hit_rate": round(hit_rate, 2)}

            if hit_rate < 0.5:
                result["recommendations"].append("More than half your lifts missed targets. Check sleep and nutrition from yesterday.")
            missed = [e["exercise"] for e in exercise_results if e["status"] == "missed"]
            if missed:
                result["recommendations"].append(f"Missed targets on: {', '.join(missed)}. Consider staying at current weight next week.")
        else:
            result["recommendations"].append(f"No workout logged. Today should be {expected_day}.")
            score_components.append(0)
    else:
        result["recommendations"].append("Rest day. Light cardio (30 min incline walk) for 200 cal burn if cutting.")
        score_components.append(30)

    # --- Nutrition Analysis ---
    nutrition = await nutrition_col.find_one({"date": dt})
    if nutrition:
        cal_target = phase.get("calories", 2200)
        pro_target = phase.get("protein_g", 180)
        actual_cal = nutrition.get("calories", 0)
        actual_pro = nutrition.get("protein_g", 0)

        cal_delta = actual_cal - cal_target
        pro_delta = actual_pro - pro_target

        cal_score = max(0, 30 - abs(cal_delta) / 50 * 5)  # lose 5 points per 50 cal off
        pro_score = max(0, 30 - max(0, -pro_delta) / 10 * 5)  # only penalize if under
        score_components.append(cal_score)
        score_components.append(pro_score)

        result["nutrition"] = {
            "calories": round(actual_cal), "target_calories": cal_target,
            "protein_g": round(actual_pro), "target_protein_g": pro_target,
            "carbs_g": round(nutrition.get("carbs_g", 0)),
            "fat_g": round(nutrition.get("fat_g", 0)),
            "calorie_delta": round(cal_delta),
            "protein_delta": round(pro_delta),
        }

        if actual_pro < pro_target:
            result["recommendations"].append(f"Protein {round(actual_pro)}g is {abs(round(pro_delta))}g below target. Prioritize protein in remaining meals.")
        if actual_cal > cal_target + 200:
            result["recommendations"].append(f"Calories {round(cal_delta)} over target. Add 10 min to tomorrow's cardio.")
        if actual_cal < cal_target - 300:
            result["recommendations"].append(f"Undereating by {abs(round(cal_delta))} cal. Don't go below 2000 on training days.")
    else:
        result["recommendations"].append("No nutrition data for today. Make sure MFP is syncing to Apple Health.")

    # --- Recovery Analysis ---
    recovery = await recovery_col.find_one({"date": dt})
    if recovery:
        hrv = recovery.get("hrv_ms")
        rhr = recovery.get("resting_heart_rate")
        sleep = recovery.get("sleep", {})
        sleep_hours = sleep.get("total_hours", 0) if sleep else 0

        result["recovery"] = {
            "sleep_hours": round(sleep_hours, 1) if sleep_hours else None,
            "hrv_ms": round(hrv, 1) if hrv else None,
            "resting_heart_rate": rhr,
            "steps": recovery.get("steps"),
        }

        if sleep_hours and sleep_hours < 7:
            result["recommendations"].append(f"Only {round(sleep_hours, 1)}h sleep. Aim for 7+. Recovery is compromised.")
            score_components.append(0)
        elif sleep_hours and sleep_hours >= 7:
            score_components.append(10)

    result["score"] = round(sum(score_components) / max(len(score_components), 1) * (100 / 30), 0)
    result["score"] = min(100, max(0, result["score"]))

    return result


async def weekly_summary(program_start: date, week_num: int) -> dict:
    start = program_start + timedelta(weeks=week_num - 1)
    end = start + timedelta(days=7)
    days = []
    for i in range(7):
        d = start + timedelta(days=i)
        if d <= date.today():
            days.append(await analyze_day(d, program_start))

    avg_score = sum(d["score"] for d in days) / max(len(days), 1)
    total_workouts = sum(1 for d in days if d.get("workout"))
    avg_cal = 0
    avg_pro = 0
    n_days = 0
    for d in days:
        if d.get("nutrition"):
            avg_cal += d["nutrition"]["calories"]
            avg_pro += d["nutrition"]["protein_g"]
            n_days += 1
    if n_days:
        avg_cal /= n_days
        avg_pro /= n_days

    return {
        "week": week_num,
        "start": str(start),
        "end": str(end),
        "avg_score": round(avg_score),
        "workouts_completed": total_workouts,
        "workouts_expected": 4,
        "avg_calories": round(avg_cal),
        "avg_protein_g": round(avg_pro),
        "daily_breakdown": days,
    }


def _fuzzy_match(target: str, actual: str) -> bool:
    t = target.lower().replace("(", "").replace(")", "").split()
    a = actual.lower().replace("(", "").replace(")", "")
    return sum(1 for w in t if w in a) >= len(t) * 0.6
