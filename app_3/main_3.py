from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from typing import List
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
from pypika.functions import Sum


class CustomJSONEncoder(JSONEncoder):
    """Сериализация datetime → ISO."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class Settings(BaseSettings):
    postgres_dsn: str = Field(..., env="POSTGRES_DSN")
    redis_dsn:    str = Field(..., env="REDIS_DSN")
    neo4j_uri:    str = Field(..., env="NEO4J_URI")
    neo4j_user:   str = Field(..., env="NEO4J_USER")
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
    logger.info("Starting Lab-3 Service…")
    app.state.db    = await asyncpg.create_pool(settings.postgres_dsn)
    app.state.neo4j = AsyncGraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )
    app.state.redis = aioredis.from_url(settings.redis_dsn, decode_responses=True)
    logger.info("Connected to Postgres, Redis & Neo4j")
    yield
    logger.info("Shutting down Lab-3 Service…")
    await app.state.db.close()
    await app.state.neo4j.close()         
    await app.state.redis.close()
    logger.info("All connections closed")


app = FastAPI(title="App3 Service", lifespan=lifespan)


class CourseInfo(BaseModel):
    course_id:      int
    course_title:   str
    planned_hours:  float
    attended_hours: int

class StudentInfo(BaseModel):
    student_id:   int
    student_name: str
    courses:      List[CourseInfo]

class GroupReport(BaseModel):
    group_id:   int
    group_name: str
    students:   List[StudentInfo]



async def fetch_planned_hours(pool, group_id: int) -> dict[tuple[int,int], dict]:
    """
    Оптимальный подсчёт запланированных часов из Postgres:
    — суммируем duration/60 (акад. часа) для специальных лекций
    """
    logger.info("Fetch planned hours for group_id=%s", group_id)
    g, s, c, cl = Table("groups"), Table("students"), Table("courses"), Table("classes")

    acad_hours = (cl.duration / 60)

    q = (
        PypikaQuery
        .from_(g)
        .join(s).on(s.group_id == g.group_id)
        .join(c).on(c.spec_id  == g.spec_id)
        .join(cl).on(cl.course_id == c.course_id)
        .select(
            g.group_id,
            g.name.as_("group_name"),
            s.student_id,
            s.full_name.as_("student_name"),
            c.course_id,
            c.title.as_("course_title"),
            Sum(acad_hours).as_("planned_hours"),
        )
        .where(g.group_id == group_id)
        .where(cl.type == "Лекция")
        .where(cl.tag  == "специальная")
        .groupby(
            g.group_id, g.name,
            s.student_id, s.full_name,
            c.course_id, c.title
        )
    )

    sql = q.get_sql()
    rows = await pool.fetch(sql)
    logger.info("Planned rows: %d", len(rows))
    return {(r["student_id"], r["course_id"]): dict(r) for r in rows}


async def fetch_attended_hours(neo4j_driver, group_code: str) -> dict[int, int]:
    """
    Подсчёт посещённых академических часов из Neo4j:
    — match по Group.code,
    — считаем все ATTENDED-рёбра к Schedule,
    — домножаем на 2 (1 лекция = 2 акад. часа).
    """
    logger.info("Fetch attended hours from Neo4j for group_code=%s", group_code)
    cypher = """
    MATCH (g:Group {code: $group_code})
          <-[:BELONGS_TO]-(s:Student)
          -[:ATTENDED]->(sch:Schedule)
    WITH s.id AS student_id, COUNT(*) * 2 AS attended_hours
    RETURN student_id, attended_hours
    """
    async with neo4j_driver.session() as session:
        result = await session.run(cypher, group_code=group_code)
        records = await result.data()  

    return { rec["student_id"]: rec["attended_hours"] for rec in records }


@app.get(
    "/api/group-hours/{group_id}",
    response_model=GroupReport
)
async def get_group_hours(
    group_id: int = Path(..., ge=1, description="ID группы")
):
    logger.info("Generate report for group_id=%s", group_id)
    cache_key = generate_cache_key("group_hours", group_id)

    # 1) Попробовать из кэша
    if cached := await get_cached_data(app.state.redis, cache_key):
        logger.info("Report served from cache")
        return GroupReport.model_validate(cached)

    # 2) Собрать запланированные и посещённые часы
    planned  = await fetch_planned_hours(app.state.db, group_id)
    if not planned:
        logger.warning("Group %s not found or no special lectures", group_id)
        raise HTTPException(404, "Group not found or no special lectures")

    first = next(iter(planned.values()))
    group_code = first["group_name"]

    attended_map = await fetch_attended_hours(app.state.neo4j, group_code)

    students_map: dict[int, dict] = {}
    for (stu_id, crs_id), data in planned.items():
        hours = attended_map.get(stu_id, 0)
        course = CourseInfo(
            course_id      = data["course_id"],
            course_title   = data["course_title"],
            planned_hours  = data["planned_hours"],
            attended_hours = min(hours, int(data["planned_hours"]))
        )
        students_map.setdefault(stu_id, {
            "student_id":   stu_id,
            "student_name": data["student_name"],
            "courses":      []
        })["courses"].append(course)

    report = GroupReport(
        group_id   = first["group_id"],
        group_name = group_code,
        students   = [StudentInfo(**si) for si in students_map.values()]
    )

    await set_cached_data(app.state.redis, cache_key, report.model_dump())
    logger.info("Report generated, students=%d", len(report.students))
    return report

if __name__ == "__main__":
    uvicorn.run(
        "app_3.main_3:app",
        host="127.0.0.1",
        port=8003,
        workers=1
    )
