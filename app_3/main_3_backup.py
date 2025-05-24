from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from typing import List, Tuple
from datetime import datetime
from json import JSONEncoder

import uvicorn
from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import asyncpg
import aioredis
from neo4j import AsyncGraphDatabase
from pypika import Query as PypikaQuery, Table
from pypika.functions import Count, Sum


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class Settings(BaseSettings):
    postgres_dsn: str = Field(..., env="POSTGRES_DSN")
    redis_dsn: str = Field(..., env="REDIS_DSN")
    neo4j_uri: str = Field(..., env="NEO4J_URI")
    neo4j_user: str = Field(..., env="NEO4J_USER")
    neo4j_password: str = Field(..., env="NEO4J_PASSWORD")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

logger = logging.getLogger("lab3_service")
if not logger.handlers:
    fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = logging.StreamHandler()
    handler.setFormatter(fmt)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False

CACHE_TTL = 60


def generate_cache_key(prefix: str, *args) -> str:
    return ":".join([prefix, *map(str, args)])


async def get_cached_data(redis, key: str):
    raw = await redis.get(key)
    if raw:
        logger.info("Cache hit: %s", key)
        return json.loads(raw)
    logger.info("Cache miss: %s", key)
    return None

async def set_cached_data(redis, key: str, data, ttl: int = CACHE_TTL):
    await redis.set(key, json.dumps(data, cls=CustomJSONEncoder), ex=ttl)
    logger.info("Cached: %s (ttl=%ds)", key, ttl)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Lab-3 Service...")
    app.state.db = await asyncpg.create_pool(settings.postgres_dsn)
    app.state.redis = aioredis.from_url(settings.redis_dsn, decode_responses=True)
    app.state.neo4j = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password)
    )
    yield
    logger.info("Shutting down...")
    await app.state.db.close()
    await app.state.redis.close()
    await app.state.neo4j.close()


app = FastAPI(title="App3 Service", lifespan=lifespan)


class CourseInfo(BaseModel):
    course_id: int
    course_title: str
    planned_hours: int
    attended_hours: int


class StudentInfo(BaseModel):
    student_id: int
    student_name: str
    courses: List[CourseInfo]


class GroupReport(BaseModel):
    group_id: int
    group_name: str
    students: List[StudentInfo]


async def fetch_planned_hours(pool, group_id: int) -> dict[Tuple[int, int], dict]:
    g, s, c, cl = Table("groups"), Table("students"), Table("courses"), Table("classes")

    q = (
        PypikaQuery.from_(g)
        .join(s).on(s.group_id == g.group_id)
        .join(c).on(c.spec_id == g.spec_id)
        .join(cl).on(cl.course_id == c.course_id)
        .select(
            g.group_id,
            g.name.as_("group_name"),
            s.student_id,
            s.full_name.as_("student_name"),
            c.course_id,
            c.title.as_("course_title"),
            Sum(cl.duration / 60).as_("planned_hours"),
        )
        .where((g.group_id == group_id)
               & (cl.type == "Лекция")
               & (cl.tag == "специальная"))
        .groupby(g.group_id, g.name, s.student_id, s.full_name, c.course_id, c.title)
    )

    rows = await pool.fetch(q.get_sql())
    return {(r["student_id"], r["course_id"]): dict(r) for r in rows}


async def fetch_attended_hours(driver, group_code: str) -> dict[Tuple[int, int], int]:
    query = """
    MATCH (g:Group {code: $group_code})-[:HAS_SCHEDULE]->(sch:Schedule)
    WHERE sch.type = 'Лекция' AND sch.tag = 'специальная'
    MATCH (s:Student)-[:BELONGS_TO]->(g)
    OPTIONAL MATCH (s)-[:ATTENDED]->(sch)
    WITH s, sch, COUNT(sch) AS attended
    RETURN s.id AS student_id, sch.course_id AS course_id, attended * 2 AS hours
    """

    attended = {}
    try:
        async with driver.session() as session:
            result = await session.run(query, group_code=group_code)
            async for record in result:
                key = (record["student_id"], record["course_id"])
                attended[key] = record["hours"]
    except Exception as e:
        logger.error("Neo4j error: %s", e)
        raise HTTPException(500, "Neo4j query failed")

    return attended


@app.get("/api/group-hours/{group_id}", response_model=GroupReport)
async def get_group_hours(group_id: int = Path(..., ge=1)):
    cache_key = generate_cache_key("group_hours", group_id)

    if cached := await get_cached_data(app.state.redis, cache_key):
        return GroupReport.model_validate(cached)

    # Получаем базовую информацию о группе из PostgreSQL
    planned = await fetch_planned_hours(app.state.db, group_id)
    if not planned:
        raise HTTPException(404, "Group not found")

    first_group = next(iter(planned.values()))
    group_code = first_group["group_name"]

    # Получаем данные о посещениях из Neo4j
    attended = await fetch_attended_hours(app.state.neo4j, group_code)

    students = {}
    for (sid, cid), data in planned.items():
        course = CourseInfo(
            course_id=cid,
            course_title=data["course_title"],
            planned_hours=data["planned_hours"],
            attended_hours=attended.get((sid, cid), 0)
        )

        if sid not in students:
            students[sid] = StudentInfo(
                student_id=sid,
                student_name=data["student_name"],
                courses=[]
            )
        students[sid].courses.append(course)

    report = GroupReport(
        group_id=first_group["group_id"],
        group_name=group_code,
        students=list(students.values())
    )

    await set_cached_data(app.state.redis, cache_key, report.model_dump())
    return report


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8003,
        reload=True
    )