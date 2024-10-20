from __future__ import annotations
import dataclasses

from health_checks import base


@dataclasses.dataclass
class BaseHTTPHealthCheck(base.HealthCheck):
    service_version_env: str = "APP_VERSION"
    service_name_env: str = "APP_NAME"
    service_version: str | None = None
    service_name: str | None = None

    async def update_health_status(self) -> bool:
        raise NotImplementedError

    async def check_health(self) -> base.HealthCheckTypedDict:
        return self._get_health_check_data(health_status=await self.update_health_status())

    async def startup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass


class DefaultHTTPHealthCheck(BaseHTTPHealthCheck):
    """Default 200 OK health check by http."""

    async def update_health_status(self) -> bool:
        return True
