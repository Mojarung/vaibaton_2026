"""Админ-маршруты: системы и перезагрузка детекции."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response

from ..errors import ApiError
from .deps import require_admin

router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)])


@router.get("/systems")
async def list_systems(request: Request) -> dict:
    systems = request.app.state.ctx.systems
    return {
        "default_system": systems.default_system,
        "version": systems.version,
        "systems": [
            {
                "id": sid,
                "policy": system.policy.model_dump(),
                "types": sorted(system.entity_types),
            }
            for sid, system in systems._systems.items()
        ],
    }


@router.put("/systems/{system_id}")
async def update_system(request: Request, system_id: str, patch: dict) -> dict:
    systems = request.app.state.ctx.systems
    try:
        system = systems.update_system(system_id, patch)
    except ValueError as exc:
        message = str(exc).splitlines()[0][:300]
        raise ApiError("invalid_policy", 422, message) from exc
    return {"id": system.id, "types": sorted(system.entity_types)}


@router.delete("/systems/{system_id}", status_code=204)
async def delete_system(request: Request, system_id: str) -> Response:
    request.app.state.ctx.systems.delete_system(system_id)
    return Response(status_code=204)


@router.post("/reload")
async def reload(request: Request) -> dict:
    ctx = request.app.state.ctx
    ctx.reload_detection()
    return {
        "version": ctx.systems.version,
        "rules": len(ctx.detector.rules),
    }
