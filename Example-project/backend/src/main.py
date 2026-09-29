import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference

from application.readings.sampler import SimulationSampler
from application.readings.service import ReadingIngest
from infrastructure.db import SessionLocal
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.reading_repository import ReadingRepository
from infrastructure.settings import settings
from interfaces.api.devices import router as devices_router
from interfaces.api.health import router as health_router
from interfaces.api.locations import assign_router
from interfaces.api.locations import router as locations_router
from interfaces.api.sensors import router as sensors_router

async def _sample_loop(stop: asyncio.Event) -> None:
    while not stop.is_set():
        session = SessionLocal()
        try:
            devices = DeviceRepository(session)
            readings = ReadingRepository(session)
            SimulationSampler(devices, readings, ReadingIngest(devices, readings)).run_once(
                datetime.now(timezone.utc)
            )
        finally:
            session.close()
        try:
            await asyncio.wait_for(stop.wait(), timeout=5)
        except TimeoutError:
            continue


@asynccontextmanager
async def lifespan(_app: FastAPI):
    stop = asyncio.Event()
    task = None
    if os.environ.get("GREENHOUSE_DISABLE_SAMPLER") != "1":
        task = asyncio.create_task(_sample_loop(stop))
    yield
    stop.set()
    if task is not None:
        await task


app = FastAPI(
    title="Smart Greenhouse API",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)

origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(sensors_router)
app.include_router(devices_router)
app.include_router(locations_router)
app.include_router(assign_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Smart Greenhouse API",
        "api_reference": "/scalar",
        "openapi": "/openapi.json",
    }


@app.get("/scalar", include_in_schema=False)
def scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url or "/openapi.json",
        title=app.title,
    )
