# HealthChecks

Welcome to the healthiest library of all times! It provides a simple interface to check the health of your application.

We have base classes for HTTP and FILE based health checks.

# Installation

TODO

### If you want to check health of your **FastAPI** application, run:

```bash
poetry run health-checks -E fastapi
```

### If you want to check health of your **Litestar** application, run:

```bash
poetry run health-checks -E litestar
```

### If you want to check health of your **consumer**, run:

```bash
poetry run health-checks -E file
```

## HTTP based quickstart

Let's begin with http based healthchecks for **Litestar** application:

```python
from health_checks.http_based import DefaultHTTPHealthCheck
from health_checks.litestar_healthcheck import build_litestar_health_check_router
import litestar


litestar_application = litestar.Litestar(
    route_handlers=[
        build_litestar_health_check_router(
            healthcheck_endpoint="/health/",
            health_check=DefaultHTTPHealthCheck(),
        ),
    ],
)
```

This is it! Now if your go to `/health/` you will notice a 200 HTTP status code if everything is alright. Otherwise you will face a 500 HTTP status code.

Similar to litestar, here is the **FastAPI** example

```python
import fastapi
from health_checks.fastapi_healthcheck import build_fastapi_health_check_router
from health_checks.http_based import DefaultHTTPHealthCheck


fastapi_app = fastapi.FastAPI()
fastapi_app.include_router(
    build_fastapi_health_check_router(
        health_check_endpoint="/health/",
        health_check=DefaultHTTPHealthCheck(),
    ),
)
```

This is also it! How wonderful, isn't it? You can navigate to `/health/` and meet your 200 HTTP status code.

## FILE based quickstart

Here things are starting to get complicated.
Let's imagine a simple consumer

```python
import dataclasses

from health_checks.base import HealthCheck


@dataclasses.dataclass
class SimpleConsumer:
    health_check: HealthCheck

    async def startup(self):
        await self.health_check.startup()

    async def shutdown(self):
        await self.health_check.shutdown()

    async def listen(self):
        while True:
            # Here we receive our messages from some queue
            try:
                # Non-blocking message processing
                await self.process_message()

                # Be attentive! We call update_health method, not update_health_status.
                await health_check.update_health()
            except Exception:
                continue
```

This is very **important** to place your health check inside infinite loop or something like that in your consumer.
You cannot use it inside your message processing function or method because if there will be no messages - your consumer will die eventually. And this is not the case we are looking for.
So, your update_health method call should be independent from message processing, also it should not be locked by it.

So, here how your code could look like

```python
# directory/some_file.py
import asyncio

from health_checks import file_based


health_check_object = file_based.DefaultFileHealthCheck()
consumer = SimpleConsumer(health_check_object)

if __name__ == '__main__':
    asyncio.run(consumer.run_consumer())
```

Cool! Now during your consumer process health will be updated. But how to check it and where?

In this package we have a cli, that allows you to check health of certain **HealthCheck** object. Here, how you can use it

```bash
python -m health_checks directory.some_file:health_check_object
```

Here `some_file` is the name of file and `health_check_object` is the name of file_based.DefaultFileHealthCheck object.
If everything is alright, then there will be no exception, but if it is not - there will be

And you use it inside your k8s manifest like this:

```yaml
livenessProbe:
  exec:
    command:
      - python
      - "-m"
      - health_checks
      - directory.some_file:health_check_object
```

Now let's look at FILE health check accepted arguments.

```python
@dataclasses.dataclass
class BaseFileHealthCheck(base.HealthCheck):
    failure_threshold: int = 60
    health_check_period: int = 30
    healthcheck_file_name: str | None = None
    base_folder: str = "./tmp/health-checks"
    ...
```

- `base_folder` - folder, where health check file will be created.
- `failure_threshold` - time after which health check won't pass
- `health_check_period` - delay time before updating health check file
- `healthcheck_file_name` - you can pass an explicit file name to your health check.

> IMPORTANT: You actually have to pass `healthcheck_file_name` it if your are not running in k8s environment.
> In that case your health check file will be named randomly and you cannot check health with provided script.
> If you are running in k8s, then file name will be made of `HOSTNAME` env variable a.k.a. pod id.

> IMPORTANT: Consider putting your health check into separate file to prevent useless imports during health check script execution.

## FAQ

- **Why do i even need `health_check_period` in FILE based health check?**
  This parameter helps to throttle calls to `update_health` method. By default `update_health` will be called every 30 seconds.
- **Custom health checks**
  There are two options. You can inherit from `BaseFileHealthCheck` or `BaseHTTPHealthCheck`. Another way is to implement class according to HealthCheck protocol. More information about protocols [here](https://peps.python.org/pep-0544/).
