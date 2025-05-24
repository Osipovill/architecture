from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from typing import List, Tuple, Dict
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


async def fetch_group_code(pg_pool, group_id: int) -> str:
    groups = Table("groups")
    q = (
        PypikaQuery.from_(groups)
        .select(groups.name)
        .where(groups.group_id == group_id)
    )
    row = await pg_pool.fetchrow(q.get_sql())
    if not row:
        raise HTTPException(404, "Group not found in PostgreSQL")
    return row["name"]


async def fetch_neo4j_planned_hours(driver, group_code: str) -> Dict[Tuple[int, int], Dict]:
    """
    Для каждого студента из группы считает запланированные часы
    (каждое занятие — 2 часа).
    """
    query = """
    MATCH (g:Group {code: $group_code})<-[:BELONGS_TO]-(s:Student)
    MATCH (g)-[:HAS_SCHEDULE]->(sch:Schedule)
    WITH
      s.id            AS student_id,
      id(sch)         AS course_id,
      sch.title       AS course_title,
      COUNT(sch) * 2  AS planned_hours
    RETURN student_id, course_id, course_title, planned_hours
    """

    planned = {}
    try:
        async with driver.session() as session:
            result = await session.run(query, group_code=group_code)
            async for record in result:
                key = (record["student_id"], record["course_id"])
                planned[key] = {
                    "course_title":  record["course_title"],
                    "planned_hours": record["planned_hours"],
                }
    except Exception as e:
        logger.error("Neo4j error: %s", e)
        raise HTTPException(500, "Failed to fetch planned hours")
    return planned




async def fetch_course_titles(pg_pool, course_ids: List[int]) -> Dict[int, str]:
    if not course_ids:
        return {}

    courses = Table("courses")
    q = (
        PypikaQuery.from_(courses)
        .select(courses.course_id, courses.title)
        .where(courses.course_id.isin(course_ids))
    )
    rows = await pg_pool.fetch(q.get_sql())

    return {r["course_id"]: r["title"] for r in rows}


async def fetch_neo4j_attended_hours(driver, group_code: str) -> Dict[Tuple[int, int], int]:
    query = """
    MATCH (g:Group {code: $group_code})<-[:BELONGS_TO]-(s:Student)
    MATCH (g)-[:HAS_SCHEDULE]->(sch:Schedule)
    OPTIONAL MATCH (s)-[a:ATTENDED]->(sch)
    WITH
      s.id                   AS student_id,
      id(sch)                AS course_id,
      COUNT(a) * 2           AS attended_hours
    RETURN student_id, course_id, attended_hours
    """

    attended = {}
    try:
        async with driver.session() as session:
            result = await session.run(query, group_code=group_code)
            async for record in result:
                key = (record["student_id"], record["course_id"])
                attended[key] = record["attended_hours"]
    except Exception as e:
        logger.error("Neo4j error: %s", e)
        raise HTTPException(500, "Failed to fetch attended hours")
    return attended


async def fetch_neo4j_students(driver, group_code: str) -> Dict[int, str]:
    query = """
    MATCH (g:Group {code: $group_code})<-[:BELONGS_TO]-(s:Student)
    RETURN s.id AS student_id, s.name AS student_name
    """

    students = {}
    try:
        async with driver.session() as session:
            result = await session.run(query, group_code=group_code)
            async for record in result:
                students[record["student_id"]] = record["student_name"]
    except Exception as e:
        logger.error("Neo4j error: %s", e)
        raise HTTPException(500, "Failed to fetch students")
    return students


@app.get("/api/group-hours/{group_id}", response_model=GroupReport)
async def get_group_hours(group_id: int = Path(..., ge=1)):
    cache_key = generate_cache_key("group_hours", group_id)

    if cached := await get_cached_data(app.state.redis, cache_key):
        return GroupReport.model_validate(cached)

    group_code = await fetch_group_code(app.state.db, group_id)

    planned   = await fetch_neo4j_planned_hours(app.state.neo4j, group_code)
    if not planned:
        raise HTTPException(404, "No planned lectures found")

    attended  = await fetch_neo4j_attended_hours(app.state.neo4j, group_code)
    students  = await fetch_neo4j_students(app.state.neo4j, group_code)


    students_map: Dict[int, StudentInfo] = {}
    for (stu_id, crs_id), data in planned.items():
        info = students_map.setdefault(
            stu_id,
            StudentInfo(
                student_id=stu_id,
                student_name=students.get(stu_id, "Unknown Student"),
                courses=[]
            )
        )
        info.courses.append(
            CourseInfo(
                course_id      = crs_id,
                course_title   = data["course_title"],
                planned_hours  = data["planned_hours"],
                attended_hours = attended.get((stu_id, crs_id), 0)
            )
        )

    report = GroupReport(
        group_id=group_id,
        group_name=group_code,
        students=list(students_map.values())
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