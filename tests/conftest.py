from __future__ import annotations
import os
import typing
import uuid

import pytest
from faker import Faker
from fastapi import FastAPI
from httpx import AsyncClient
from litestar import Litestar

from health_checks import base, file_based, http_based
from health_checks.fastapi_healthcheck import build_fastapi_health_check_router
from health_checks.litestar_healthcheck import build_litestar_health_check_router


os.environ[base.POD_IDENTIFIER_ENVIRONMENT_NAME] = str(uuid.uuid4())
file_health_check_for_main_testing: typing.Final = file_based.DefaultFileHealthCheck()


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture()
def health_check_endpoint() -> str:
    return "/test_health/"


@pytest.fixture()
def fake_service_name(faker: Faker) -> str:
    """Return name of the service."""
    return faker.name()


@pytest.fixture()
def fake_service_version(faker: Faker) -> str:
    """Return version of the service."""
    return faker.numerify("%!!.%!!.%!!")


@pytest.fixture()
def default_file_health_check() -> file_based.DefaultFileHealthCheck:
    return file_based.DefaultFileHealthCheck()


@pytest.fixture()
def short_lived_default_file_health_check(short_live_time: int) -> file_based.DefaultFileHealthCheck:
    return file_based.DefaultFileHealthCheck(failure_threshold=short_live_time, health_check_period=0)


@pytest.fixture()
def http_default_health_check(fake_service_version: str, fake_service_name: str) -> http_based.DefaultHTTPHealthCheck:
    return http_based.DefaultHTTPHealthCheck(service_version=fake_service_version, service_name=fake_service_name)


@pytest.fixture()
def short_live_time() -> int:
    return 1


@pytest.fixture()
def expected_response(fake_service_version: str, fake_service_name: str) -> base.HealthCheckTypedDict:
    return {
        "service_version": fake_service_version,
        "service_name": fake_service_name,
        "health_status": True,
    }


@pytest.fixture()
def failed_response(fake_service_version: str, fake_service_name: str) -> base.HealthCheckTypedDict:
    return {
        "service_version": fake_service_version,
        "service_name": fake_service_name,
        "health_status": False,
    }


@pytest.fixture()
async def litestar_client(litestar_app: Litestar) -> typing.AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=litestar_app, base_url="http://test", timeout=200) as async_client:
        yield async_client


@pytest.fixture()
async def fastapi_client(fastapi_app: FastAPI) -> typing.AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=fastapi_app, base_url="http://test", timeout=200) as async_client:
        yield async_client


@pytest.fixture()
def fastapi_app(
    health_check_endpoint: str,
    http_default_health_check: http_based.DefaultHTTPHealthCheck,
) -> FastAPI:
    fastapi_app: FastAPI = FastAPI()
    fastapi_app.include_router(
        build_fastapi_health_check_router(
            health_check_endpoint=health_check_endpoint,
            health_check=http_default_health_check,
        ),
    )
    return fastapi_app


@pytest.fixture()
def litestar_app(
    health_check_endpoint: str,
    http_default_health_check: http_based.DefaultHTTPHealthCheck,
) -> Litestar:
    return Litestar(
        route_handlers=[
            build_litestar_health_check_router(
                health_check_endpoint=health_check_endpoint,
                health_check=http_default_health_check,
            ),
        ],
    )
