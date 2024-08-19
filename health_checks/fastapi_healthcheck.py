from __future__ import annotations
import typing

from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

from health_checks.base import HealthCheck


def build_fastapi_health_check_router(
    health_check: HealthCheck,
    health_check_endpoint: str = "/health/",
) -> APIRouter:
    fastapi_router: typing.Final = APIRouter(tags=["probes"])

    @fastapi_router.get(health_check_endpoint)
    async def health_check_handler() -> JSONResponse:
        health_check_data: typing.Final = await health_check.check_health()
        if not health_check_data["health_status"]:
            raise HTTPException(status_code=500, detail="Service is unhealthy.")
        return JSONResponse(content=health_check_data)

    return fastapi_router
