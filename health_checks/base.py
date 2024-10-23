from __future__ import annotations
import os
import typing


POD_IDENTIFIER_ENVIRONMENT_NAME: typing.Final = "HOSTNAME"
HEALTH_CHECK_FILE_NAME_TEMPLATE: typing.Final = "health-check-{file_name}.json"


class HealthCheckTypedDict(typing.TypedDict, total=False):
    service_version: typing.Optional[str]  # noqa: UP007 (Litestar fails to build OpenAPI schema on Python 3.9)
    service_name: typing.Optional[str]  # noqa: UP007 (Litestar fails to build OpenAPI schema on Python 3.9)
    health_status: bool


class HealthCheck(typing.Protocol):
    service_version_env: str
    service_name_env: str
    service_version: str | None
    service_name: str | None

    def _get_health_check_data(
        self,
        health_status: bool,
    ) -> HealthCheckTypedDict:
        return {
            "service_version": self.service_version or os.environ.get(self.service_version_env),
            "service_name": self.service_name or os.environ.get(self.service_name_env),
            "health_status": health_status,
        }

    async def update_health_status(self) -> bool:
        raise NotImplementedError

    async def check_health(self) -> HealthCheckTypedDict:
        raise NotImplementedError

    async def startup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass
