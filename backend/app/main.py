import asyncio
from contextlib import asynccontextmanager
from typing import Any

import asyncpg
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from starlette.responses import JSONResponse

from app.config import get_settings


settings = get_settings()


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=120)


class Task(BaseModel):
    id: int
    title: str
    created_at: str


async def initialize_database(app: FastAPI) -> None:
    if getattr(app.state, "db_pool", None):
        return

    pool = None
    try:
        pool = await asyncpg.create_pool(
            dsn=settings.database_url,
            min_size=1,
            max_size=5,
            command_timeout=10,
        )
        async with pool.acquire() as connection:
            await connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
        app.state.db_pool = pool
        app.state.startup_error = None
    except Exception as exc:
        if pool:
            await pool.close()
        app.state.db_pool = None
        app.state.startup_error = f"Database startup failed: {exc}"


async def ensure_database_pool(app: FastAPI) -> asyncpg.Pool:
    pool = getattr(app.state, "db_pool", None)
    if pool:
        return pool

    async with app.state.db_init_lock:
        pool = getattr(app.state, "db_pool", None)
        if pool:
            return pool

        await initialize_database(app)
        pool = getattr(app.state, "db_pool", None)
        if pool:
            return pool

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Database connection pool is not available.",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.startup_error = None
    app.state.db_pool = None
    app.state.db_init_lock = asyncio.Lock()
    app.state.redis = Redis.from_url(settings.redis_url, decode_responses=True)
    await initialize_database(app)

    yield

    if getattr(app.state, "db_pool", None):
        await app.state.db_pool.close()
    if getattr(app.state, "redis", None):
        await app.state.redis.aclose()


app = FastAPI(
    title=settings.app_name,
    description="FastAPI service for the microservices deployment demo.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_redis(request: Request) -> Redis:
    client = getattr(request.app.state, "redis", None)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis client is not available.",
        )
    return client


@app.get("/api/info")
async def service_info() -> dict[str, Any]:
    return {
        "service": settings.app_name,
        "environment": settings.environment,
        "message": "API is reachable.",
    }


@app.get("/health")
async def health(request: Request) -> JSONResponse:
    checks: dict[str, str] = {
        "api": "ok",
        "database": "unknown",
        "redis": "unknown",
    }

    pool = getattr(request.app.state, "db_pool", None)
    if not pool:
        try:
            pool = await ensure_database_pool(request.app)
        except HTTPException:
            pool = None

    if pool:
        try:
            async with pool.acquire() as connection:
                await connection.fetchval("SELECT 1")
            checks["database"] = "ok"
        except Exception as exc:
            checks["database"] = f"error: {exc}"
    else:
        checks["database"] = getattr(
            request.app.state,
            "startup_error",
            "database pool unavailable",
        )

    redis_client = getattr(request.app.state, "redis", None)
    if redis_client:
        try:
            await redis_client.ping()
            checks["redis"] = "ok"
        except Exception as exc:
            checks["redis"] = f"error: {exc}"
    else:
        checks["redis"] = "redis client unavailable"

    is_healthy = all(value == "ok" for value in checks.values())
    return JSONResponse(
        status_code=status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "ok" if is_healthy else "degraded",
            "service": settings.app_name,
            "environment": settings.environment,
            "checks": checks,
        },
    )


@app.get("/api/tasks", response_model=list[Task])
async def list_tasks(request: Request) -> list[dict[str, Any]]:
    pool = await ensure_database_pool(request.app)
    async with pool.acquire() as connection:
        rows = await connection.fetch(
            """
            SELECT id, title, created_at
            FROM tasks
            ORDER BY created_at DESC
            LIMIT 20;
            """
        )
    return [
        {
            "id": row["id"],
            "title": row["title"],
            "created_at": row["created_at"].isoformat(),
        }
        for row in rows
    ]


@app.post("/api/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate, request: Request) -> dict[str, Any]:
    pool = await ensure_database_pool(request.app)
    async with pool.acquire() as connection:
        row = await connection.fetchrow(
            """
            INSERT INTO tasks (title)
            VALUES ($1)
            RETURNING id, title, created_at;
            """,
            task.title,
        )
    return {
        "id": row["id"],
        "title": row["title"],
        "created_at": row["created_at"].isoformat(),
    }


@app.get("/api/cache")
async def cache_counter(request: Request) -> dict[str, Any]:
    redis_client = get_redis(request)
    hits = await redis_client.incr("portfolio:cache:hits")
    return {
        "cache": "redis",
        "hits": hits,
        "message": "Counter updated.",
    }
