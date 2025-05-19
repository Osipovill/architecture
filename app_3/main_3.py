from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

import aioredis
import asyncpg
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Path, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from neo4j import AsyncGraphDatabase
from pydantic import BaseModel, BaseSettings, Field
from pypika import Query, Table

# ─────────────────── settings ────────────────────
class Settings(BaseSettings):
    postgres_dsn: str = Field(..., env="POSTGRES_DSN")
    redis_dsn: str = Field(..., env="REDIS_DSN")
    neo4j_uri: str = Field(..., env="NEO4J_URI")
    neo4j_user: str = Field(..., env="NEO4J_USER")
    neo4j_password: str = Field(..., env="NEO4J_PASSWORD")

    jwt_secret: str = Field("change-me", env="JWT_SECRET")
    jwt_algorithm: str = "HS256"

    class Config:
        env_file = ".env"


settings = Settings()

# ─────────────────── logging ─────────────────────
logger = logging.getLogger("lab3_service")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s — %(levelname)s — %(message)s"))
    logger.addHandler(_h)
logger.propagate = False                                           

# ─────────────────── security (JWT) ──────────────
bearer_scheme = HTTPBearer()


def verify_token(
    cred: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            cred.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        logger.debug("JWT decoded: %s", payload)                  
        return payload
    except JWTError:
        logger.warning("Invalid JWT received")                    
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


# ─────────────────── pydantic models ─────────────
class GroupHours(BaseModel):
    group_id: int
    group_name: str
    student_id: int
    student_name: str
    course_id: int
    course_title: str
    planned_hours: int
    attended_hours: int


# ─────────────────── FastAPI app ─────────────────
app = FastAPI(title="Lab-3 Service")

CACHE_TTL = 3600  # 1 час


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Starting Lab-3 service …")
    app.state.pg: asyncpg.Pool = await asyncpg.create_pool(settings.postgres_dsn)
    app.state.redis = aioredis.from_url(settings.redis_dsn, decode_responses=True)
    app.state.neo4j = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    logger.info("Connected to Postgres / Redis / Neo4j")          


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("Shutting down …")
    await app.state.pg.close()
    await app.state.neo4j.close()
    await app.state.redis.close()
    logger.info("Connections closed")                             


# ─────────────────── helpers ─────────────────────
def _cache_key(group_id: int) -> str:
    return f"group_hours:{group_id}"


async def _get_cached(redis, key: str):
    raw = await redis.get(key)
    if raw:
        logger.info("Cache hit: %s", key)
        return json.loads(raw)
    logger.info("Cache miss: %s", key)
    return None


async def _set_cached(redis, key: str, data):
    await redis.set(key, json.dumps(data), ex=CACHE_TTL)
    logger.info("Cached: %s (ttl=%ss)", key, CACHE_TTL)


# ─────────────────── SQL parts ───────────────────
async def _fetch_planned_hours(pool: asyncpg.pool.Pool, group_id: int):
    """Возвращает planned_hours для каждой (course, student) пары"""
    logger.info("Fetching *planned* hours for group_id=%s", group_id)   

    g, s, c, cl = (
        Table("groups"),
        Table("students"),
        Table("courses"),
        Table("classes"),
    )

    q = (
        Query.from_(g)
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
            (cl.duration * 2).as_("lecture_hours"),  # 1 лекция = 2 часа
        )
        .where(g.group_id == group_id)
        .where(cl.type == "lecture")
        .where(cl.requirements.ilike("%special%"))
    )

    sql = f"""
        SELECT group_id, group_name, student_id, student_name,
               course_id, course_title, SUM(lecture_hours) AS planned_hours
        FROM ({q.get_sql()}) sub
        GROUP BY group_id, group_name,
                 student_id, student_name,
                 course_id, course_title
    """
    logger.debug("Planned-hours SQL:\n%s", sql)                   

    rows = await pool.fetch(sql)
    logger.info("Planned hours rows: %d", len(rows))              
    return {(r["student_id"], r["course_id"]): dict(r) for r in rows}


# ─────────────────── Cypher parts ────────────────
ATTENDED_CYPHER = """
MATCH (g:Group {group_id: $group_id})<-[:BELONGS_TO]-(st:Student)
MATCH (st)-[:ATTENDED]->(sch:Schedule)-[:OF_CLASS]->(cl:Class {type:'lecture'})
MATCH (cl)-[:OF_COURSE]->(co:Course)
WHERE cl.requirements CONTAINS 'special'
RETURN st.student_id AS student_id,
       co.course_id  AS course_id,
       COUNT(DISTINCT sch) * 2 AS attended_hours   // 1 лекция = 2 часа
"""


async def _fetch_attended_hours(driver, group_id: int):
    logger.info("Fetching *attended* hours for group_id=%s", group_id)  
    async with driver.session() as sess:
        res = await sess.run(ATTENDED_CYPHER, group_id=group_id)
        records = await res.data()
    logger.info("Attended hours rows: %d", len(records))          
    return {(r["student_id"], r["course_id"]): r["attended_hours"] for r in records}


# ─────────────────── route ───────────────────────
@app.get(
    "/api/group-hours/{group_id}",
    response_model=List[GroupHours],
    dependencies=[Depends(verify_token)],
)
async def group_hours(group_id: int = Path(..., ge=1, description="ID группы")):
    """Отчёт по студентам группы: запланированные / фактические часы лекций"""
    logger.info("Generate report for group_id=%s", group_id)      

    # ── кэш ──
    redis = app.state.redis
    if cached := await _get_cached(redis, _cache_key(group_id)):
        logger.info("Report served from cache")                   
        return [GroupHours(**row) for row in cached]

    # ── данные из БД ──
    planned = await _fetch_planned_hours(app.state.pg, group_id)
    if not planned:
        logger.warning("Group %s not found or no classes", group_id)    
        raise HTTPException(status_code=404, detail="Group not found or no classes")

    attended = await _fetch_attended_hours(app.state.neo4j, group_id)

    # ── сшиваем ──
    report: List[GroupHours] = []
    for key, plan in planned.items():
        report.append(GroupHours(**plan, attended_hours=attended.get(key, 0)))

    # ── кэшируем и отдаём ──
    await _set_cached(redis, _cache_key(group_id), [r.model_dump() for r in report])

    logger.info("Report generated, rows=%d", len(report))         
    return report


# ─────────────────── main ────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "lab3_service.main:app",
        host="0.0.0.0",
        port=8003,
        reload=False,
    )
