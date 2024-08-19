from __future__ import annotations
import typing

import litestar
import litestar.exceptions

from health_checks import base


def build_litestar_health_check_router(
    health_check: base.HealthCheck,
    health_check_endpoint: str = "/health/",
) -> litestar.Router:
    @litestar.get(media_type=litestar.MediaType.JSON)
    async def health_check_handler() -> base.HealthCheckTypedDict:
        health_check_data: typing.Final = await health_check.check_health()
        if not health_check_data["health_status"]:
            raise litestar.exceptions.HTTPException(status_code=500, detail="Service is unhealthy.")
        return health_check_data

    return litestar.Router(path=health_check_endpoint, route_handlers=[health_check_handler], tags=["probes"])