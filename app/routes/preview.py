from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path
from app.services import preview_data, analysis_service
from app.config import get_settings

router = APIRouter(tags=["preview"])
_STATIC = Path(__file__).parent.parent / "static"


def _preview_html() -> str:
    return (_STATIC / "preview.html").read_text()


@router.get("/app", response_class=HTMLResponse, include_in_schema=False)
async def mobile_app():
    return HTMLResponse(_preview_html())


@router.get("/preview", response_class=HTMLResponse, include_in_schema=False)
async def preview_ui():
    return HTMLResponse(_preview_html())


@router.get("/preview/manifest.json", include_in_schema=False)
async def preview_manifest():
    return FileResponse(_STATIC / "manifest.json", media_type="application/json")


@router.get("/preview/dashboard")
async def preview_dashboard():
    return preview_data.DASHBOARD


@router.get("/preview/workouts")
async def preview_workouts():
    return preview_data.WORKOUTS


@router.get("/preview/nutrition")
async def preview_nutrition():
    return preview_data.NUTRITION


@router.get("/preview/recovery")
async def preview_recovery():
    return preview_data.RECOVERY


@router.get("/preview/body-metrics")
async def preview_body_metrics():
    return preview_data.BODY_METRICS


@router.get("/preview/program/week/{week}")
async def preview_program_week(week: int):
    phase = analysis_service.get_phase(week)
    program = {}
    for day_name, exercises in analysis_service.PROGRAM.items():
        program[day_name] = {}
        for ex_name, target in exercises.items():
            program[day_name][ex_name] = {
                "sets": target["sets"],
                "reps": f'{target["rep_low"]}-{target["rep_high"]}',
                "weight": target["weekly_weights"].get(week, 0),
                "rest_seconds": target["rest"],
            }
    return {"week": week, "phase": phase, "program": program, "preview": True}
