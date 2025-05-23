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
from pypika import Query as PypikaQuery, Table

class CustomJSONEncoder(JSONEncoder):
    """Кастомный JSON энкодер для сериализации datetime объектов"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# ----------------- CONFIGURATION -----------------
class Settings(BaseSettings):
    """Настройки приложения из .env"""
    postgres_dsn: str = Field(..., env="POSTGRES_DSN")
    redis_dsn: str = Field(..., env="REDIS_DSN")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

# ----------------- LOGGING -----------------
logger = logging.getLogger("lab3_service")
if not logger.handlers:
    fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    h = logging.StreamHandler()
    h.setFormatter(fmt)
    logger.setLevel(logging.INFO)
    logger.addHandler(h)
    logger.propagate = False

# ----------------- CACHE -----------------
CACHE_TTL = 3600  # секунды

def generate_cache_key(prefix: str, *args) -> str:
    parts = [prefix, *map(str, args)]
    return ":".join(parts)

async def get_cached_data(redis, key: str):
    raw = await redis.get(key)
    if raw:
        logger.info(f"Cache hit: {key}")
        return json.loads(raw)
    logger.info(f"Cache miss: {key}")
    return None

async def set_cached_data(redis, key: str, data, ttl: int = CACHE_TTL):
    await redis.set(key, json.dumps(data, cls=CustomJSONEncoder), ex=ttl)
    logger.info(f"Cached: {key}, TTL={ttl}s")

# ----------------- LIFESPAN -----------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Запуск сервиса Lab-3…")
    app.state.db = await asyncpg.create_pool(dsn=settings.postgres_dsn)
    app.state.redis = aioredis.from_url(settings.redis_dsn, decode_responses=True)
    logger.info("Подключены Postgres и Redis")
    yield
    logger.info("Завершение работы сервиса Lab-3…")
    await app.state.db.close()
    await app.state.redis.close()
    logger.info("Все соединения закрыты")

app = FastAPI(title="Lab-3 Service", lifespan=lifespan)

# ----------------- Pydantic Models -----------------
class GroupHours(BaseModel):
    group_id: int
    group_name: str
    student_id: int
    student_name: str
    course_id: int
    course_title: str
    planned_hours: int
    attended_hours: int

# ----------------- BUSINESS LOGIC -----------------
async def fetch_planned_hours(pool, group_id: int) -> dict[tuple[int,int], dict]:
    """
    Получение запланированных часов (только лекции с tag='специальная')
    для каждой пары (student_id, course_id)
    """
    logger.info(f"Fetching planned hours for group_id={group_id}")
    g, s, c, cl = (
        Table("groups"),
        Table("students"),
        Table("courses"),
        Table("classes"),
    )

    q = (
        PypikaQuery
        .from_(g)
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
            cl.duration,
        )
        .where(g.group_id == group_id)
        .where(cl.type == "Лекция")
        .where(cl.tag == "специальная")
    )

    sql = f"""
        SELECT group_id, group_name, student_id, student_name,
               course_id, course_title,
               SUM(duration / 60) AS planned_hours
        FROM ({q.get_sql()}) sub
        GROUP BY group_id, group_name, student_id,
                 student_name, course_id, course_title
    """
    logger.debug("Planned-hours SQL:\n%s", sql)
    rows = await pool.fetch(sql)
    logger.info(f"Planned rows: {len(rows)}")
    return {(r["student_id"], r["course_id"]): dict(r) for r in rows}

async def fetch_attended_hours(pool, group_id: int) -> dict[tuple[int,int], int]:
    """
    Получение фактических часов посещения (только лекции с tag='специальная')
    из таблицы attendances
    """
    logger.info(f"Fetching attended hours for group_id={group_id}")
    sql = """
        SELECT s.student_id, c.course_id, SUM(cl.duration / 60) AS attended_hours
        FROM students s
        JOIN attendances a ON a.student_id = s.student_id
        JOIN shedule sch ON a.shedule_id = sch.shedule_id
        JOIN classes cl ON sch.class_id = cl.class_id
        JOIN courses c ON cl.course_id = c.course_id
        WHERE s.group_id = $1
          AND cl.type = 'Лекция'
          AND cl.tag = 'специальная'
          AND a.presence = TRUE
        GROUP BY s.student_id, c.course_id
    """
    rows = await pool.fetch(sql, group_id)
    logger.info(f"Attended rows: {len(rows)}")
    return {(r["student_id"], r["course_id"]): r["attended_hours"] for r in rows}

# ----------------- ROUTES -----------------
@app.get(
    "/api/group-hours/{group_id}",
    response_model=List[GroupHours]
)
async def get_group_hours(
    group_id: int = Path(..., ge=1, description="ID группы")
):
    """
    Отчёт по студентам группы: запланированные и фактические часы лекций
    """
    logger.info(f"Generate report for group_id={group_id}")

    # проверка кэша
    cache_key = generate_cache_key("group_hours", group_id)
    if cached := await get_cached_data(app.state.redis, cache_key):
        logger.info("Report served from cache")
        return [GroupHours(**row) for row in cached]

    # данные
    planned = await fetch_planned_hours(app.state.db, group_id)
    if not planned:
        logger.warning(f"Group {group_id} not found or no classes")
        raise HTTPException(status_code=404, detail="Group not found or no classes")

    attended = await fetch_attended_hours(app.state.db, group_id)

    # объединение
    report: List[GroupHours] = []
    for (stu_id, course_id), data in planned.items():
        hours = attended.get((stu_id, course_id), 0)
        report.append(GroupHours(**data, attended_hours=hours))

    # кэшируем и возвращаем
    await set_cached_data(app.state.redis, cache_key, [r.model_dump() for r in report])
    logger.info(f"Report generated, rows={len(report)}")
    return report

# ----------------- MAIN -----------------
if __name__ == "__main__":
    uvicorn.run(
        "lab3_service.main:app",
        host="127.0.0.1",
        port=8003,
        workers=1
    )
