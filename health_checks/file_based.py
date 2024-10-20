from __future__ import annotations
import dataclasses
import datetime
import os
import pathlib
import typing
import uuid
import warnings

import aiofiles

from health_checks import base


@dataclasses.dataclass
class BaseFileHealthCheck(base.HealthCheck):
    failure_threshold: int = 60
    health_check_period: int = 30
    healthcheck_file_name: str | None = None
    base_folder: str = "./tmp/health-checks"
    service_version_env: str = "APP_VERSION"
    service_name_env: str = "APP_NAME"
    service_version: str | None = None
    service_name: str | None = None
    _health_check_file_path: pathlib.Path = dataclasses.field(init=False)
    _last_health_check_time: float | None = dataclasses.field(init=False, default=None)

    def __post_init__(self) -> None:
        if self.health_check_period > self.failure_threshold:
            raise ValueError(
                "Please provide failure_threshold greater than health_check_period. Or health check will always fail.",
            )
        health_check_file_name: str | None = self.healthcheck_file_name or os.environ.get(
            base.POD_IDENTIFIER_ENVIRONMENT_NAME,
        )
        if health_check_file_name is None:
            warnings.warn(
                """
                You have not provided healthcheck filename and running not in k8s enviornment.
                Healthcheck filename will be generated randomly.
                """,
                stacklevel=1,
            )
            health_check_file_name = str(uuid.uuid4())

        self._health_check_file_path = pathlib.Path(
            self.base_folder,
            base.HEALTH_CHECK_FILE_NAME_TEMPLATE.format(file_name=health_check_file_name),
        )

    @property
    def health_check_file_path(self) -> pathlib.Path:
        return self._health_check_file_path

    async def startup(self) -> None:
        base_folder_path: typing.Final = pathlib.Path(self.base_folder)
        if base_folder_path.exists() and self._health_check_file_path.is_file():
            return

        if not base_folder_path.exists():
            base_folder_path.mkdir(parents=True)

        await self.touch_health_check_file()

    async def shutdown(self) -> None:
        self._health_check_file_path.unlink()

    def _is_time_to_update(self) -> bool:
        return (
            self._last_health_check_time is None
            or self.health_check_period + self._last_health_check_time
            < datetime.datetime.now(datetime.timezone.utc).timestamp()
        )

    async def touch_health_check_file(
        self,
    ) -> None:
        await (await aiofiles.open(self._health_check_file_path, "w+")).close()

    def _get_health_check_last_update_time(self) -> float:
        return self._health_check_file_path.stat().st_mtime

    async def update_health_status(self) -> bool:
        if not self._is_time_to_update():
            return False

        await self.update_health()
        self._last_health_check_time = datetime.datetime.now(datetime.timezone.utc).timestamp()
        return True

    async def update_health(self) -> None:
        raise NotImplementedError

    async def check_health(self) -> base.HealthCheckTypedDict:
        last_update_time: typing.Final = self._get_health_check_last_update_time()
        return self._get_health_check_data(
            health_status=last_update_time + self.failure_threshold
            >= datetime.datetime.now(datetime.timezone.utc).timestamp(),
        )


class DefaultFileHealthCheck(BaseFileHealthCheck):
    """Default 200 OK health check by file."""

    async def update_health(self) -> None:
        await self.touch_health_check_file()
