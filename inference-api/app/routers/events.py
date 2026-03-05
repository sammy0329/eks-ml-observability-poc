from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter(prefix="/events", tags=["events"])


# ── Pydantic 요청 모델 ────────────────────────────────────────────────────────

class DeploymentCreate(BaseModel):
    service_name: str
    version: str
    deployed_by: str = "system"
    notes: str | None = None


class IncidentCreate(BaseModel):
    sensor_id: str
    reason: str
    anomaly_score: float
    severity: str = "warning"


class ScenarioRunCreate(BaseModel):
    scenario: str
    profile: str
    notes: str | None = None


# ── 엔드포인트 ────────────────────────────────────────────────────────────────

@router.post("/deployments", status_code=201)
async def create_deployment(
    payload: DeploymentCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            INSERT INTO deployments (service_name, version, deployed_by, notes)
            VALUES (:service_name, :version, :deployed_by, :notes)
            RETURNING id, service_name, version, deployed_at, status
        """),
        payload.model_dump(),
    )
    await db.commit()
    return dict(result.mappings().one())


@router.post("/incidents", status_code=201)
async def create_incident(
    payload: IncidentCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            INSERT INTO incidents (sensor_id, reason, anomaly_score, severity)
            VALUES (:sensor_id, :reason, :anomaly_score, :severity)
            RETURNING id, sensor_id, reason, anomaly_score, detected_at, severity
        """),
        payload.model_dump(),
    )
    await db.commit()
    return dict(result.mappings().one())


@router.post("/scenario_runs", status_code=201)
async def create_scenario_run(
    payload: ScenarioRunCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            INSERT INTO scenario_runs (scenario, profile, notes)
            VALUES (:scenario, :profile, :notes)
            RETURNING id, scenario, profile, started_at
        """),
        payload.model_dump(),
    )
    await db.commit()
    return dict(result.mappings().one())


@router.get("/scenario_runs")
async def list_scenario_runs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("""
            SELECT id, scenario, profile, started_at, ended_at, notes
            FROM scenario_runs
            ORDER BY started_at DESC
            LIMIT 100
        """),
    )
    return [dict(r) for r in result.mappings().all()]
