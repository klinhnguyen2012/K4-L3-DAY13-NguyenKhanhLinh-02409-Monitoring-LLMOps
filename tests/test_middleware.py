from __future__ import annotations

import asyncio
import re

import httpx
import pytest
from fastapi import FastAPI, Request
from structlog.contextvars import bind_contextvars, get_contextvars

from app.middleware import CorrelationIdMiddleware


def test_middleware_clears_stale_structlog_context() -> None:
    test_app = FastAPI()
    test_app.add_middleware(CorrelationIdMiddleware)

    @test_app.get("/context")
    async def get_context() -> dict[str, str | None]:
        from structlog.contextvars import get_contextvars

        return {"stale_value": get_contextvars().get("stale_value")}

    async def send_request() -> httpx.Response:
        transport = httpx.ASGITransport(app=test_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/context")

    bind_contextvars(stale_value="must-not-leak")
    response = asyncio.run(send_request())

    assert response.status_code == 200
    assert response.json() == {"stale_value": None}


def test_middleware_propagates_correlation_id_to_request_context() -> None:
    test_app = FastAPI()
    test_app.add_middleware(CorrelationIdMiddleware)

    @test_app.get("/context")
    async def get_context(request: Request) -> dict[str, str | None]:
        return {
            "request_id": request.state.correlation_id,
            "log_id": get_contextvars().get("correlation_id"),
        }

    async def send_request() -> httpx.Response:
        transport = httpx.ASGITransport(app=test_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/context", headers={"x-request-id": "req-a1b2c3d4"})

    response = asyncio.run(send_request())

    assert response.status_code == 200
    assert response.json() == {
        "request_id": "req-a1b2c3d4",
        "log_id": "req-a1b2c3d4",
    }


@pytest.mark.parametrize(
    ("request_id", "expected"),
    [
        ("req-a1b2c3d4", "req-a1b2c3d4"),
        (None, None),
        ("invalid-id", None),
    ],
)
def test_middleware_accepts_or_generates_request_id(
    request_id: str | None, expected: str | None
) -> None:
    test_app = FastAPI()
    test_app.add_middleware(CorrelationIdMiddleware)

    @test_app.get("/correlation-id")
    async def get_correlation_id(request: Request) -> dict[str, str]:
        return {"correlation_id": request.state.correlation_id}

    async def send_request() -> httpx.Response:
        transport = httpx.ASGITransport(app=test_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            headers = {"x-request-id": request_id} if request_id is not None else None
            return await client.get("/correlation-id", headers=headers)

    response = asyncio.run(send_request())
    correlation_id = response.json()["correlation_id"]

    assert response.status_code == 200
    if expected is not None:
        assert correlation_id == expected
    else:
        assert re.fullmatch(r"req-[0-9a-f]{8}", correlation_id)


@pytest.mark.parametrize("request_id", ["req-a1b2c3d4", None])
def test_middleware_returns_correlation_id_and_processing_time_headers(
    request_id: str | None,
) -> None:
    test_app = FastAPI()
    test_app.add_middleware(CorrelationIdMiddleware)

    @test_app.get("/correlation-id")
    async def get_correlation_id(request: Request) -> dict[str, str]:
        return {"correlation_id": request.state.correlation_id}

    async def send_request() -> httpx.Response:
        transport = httpx.ASGITransport(app=test_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            headers = {"x-request-id": request_id} if request_id is not None else None
            return await client.get("/correlation-id", headers=headers)

    response = asyncio.run(send_request())

    assert response.status_code == 200
    assert response.headers["x-request-id"] == response.json()["correlation_id"]
    assert re.fullmatch(r"req-[0-9a-fA-F]{8}", response.headers["x-request-id"])
    assert float(response.headers["x-response-time-ms"]) >= 0
