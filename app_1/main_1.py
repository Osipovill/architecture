from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime
import json
from json import JSONEncoder
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
from fastapi import FastAPI, HTTPException, Query
import asyncpg
from elasticsearch import AsyncElasticsearch
import aioredis
from neo4j import AsyncGraphDatabase
from pypika import Query as PypikaQuery, Table, Field, Case, Parameter
from pypika.functions import Count, Sum
from pydantic import BaseModel, AnyHttpUrl, Field
from pydantic_settings import BaseSettings
import logging

class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

logger = logging.getLogger("lab1_service")
if not logger.handlers:
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    logger.propagate = False


CACHE_TTL = 60

def generate_cache_key(prefix: str, *args) -> str:
    """Генерация уникального ключа кэша из префикса и аргументов"""
    key_parts = [prefix] + [str(arg) for arg in args]
    key_string = ":".join(key_parts)
    return key_string

async def get_cached_data(redis, key: str):
    """Получение данных из Redis кэша"""
    data = await redis.get(key)
    if data:
        logger.info(f"Cache hit: {key}")
        return json.loads(data)
    logger.info(f"Cache miss: {key}")
    return None

async def set_cached_data(redis, key: str, data, ttl: int = CACHE_TTL):
    """Сохранение данных в Redis кэш с указанным TTL"""
    await redis.set(key, json.dumps(data, cls=CustomJSONEncoder), ex=ttl)
    logger.info(f"Cached: {key}, TTL: {ttl}")

class Settings(BaseSettings):
    postgres_dsn: str = Field(..., env="POSTGRES_DSN")
    es_host: AnyHttpUrl = Field(..., env="ES_HOST")
    redis_dsn: str     = Field(..., env="REDIS_DSN")
    mongo_dsn: str     = Field(..., env="MONGO_DSN")
    neo4j_uri: str = Field(..., env="NEO4J_URI")
    neo4j_user: str = Field(..., env="NEO4J_USER")
    neo4j_password: str = Field(..., env="NEO4J_PASSWORD")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db  = await asyncpg.create_pool(dsn=settings.postgres_dsn)
    app.state.es    = AsyncElasticsearch([str(settings.es_host)])
    app.state.redis = aioredis.from_url(settings.redis_dsn, decode_responses=True)
    app.state.neo4j = AsyncGraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )
    mongo_client = AsyncIOMotorClient(settings.mongo_dsn, serverSelectionTimeoutMS=5000)
    try:
        await mongo_client.admin.command("ping")
        logger.info("MongoDB connected")
    except Exception as e:
        logger.error("MongoDB connection error: %s", e)
        raise
    app.state.mongo = mongo_client[mongo_client.get_default_database().name]

    yield
    await app.state.db.close()
    await app.state.es.close()
    await app.state.neo4j.close()
    await app.state.redis.close()

class StudentReport(BaseModel):
    student_id: int
    code: str
    full_name: str
    group: str
    specialty: str
    department: str
    institute: str
    attendance_percent: float

class ReportResponse(BaseModel):
    term: str
    period: dict
    students: list[StudentReport]
    total_lectures: int
    timestamp: datetime

app = FastAPI(title="Lab1 Service", lifespan=lifespan)

async def fetch_lecture_ids(es, pool, term: str, start: str, end: str) -> set[int] | None:
    """Поиск лекций по термину в ES и фильтрация по датам в PostgreSQL"""
    # Проверяем кэш для результатов поиска ES
    es_cache_key = generate_cache_key("es_search", term)
    cached_ids = await get_cached_data(app.state.redis, es_cache_key)

    if cached_ids is None:
        # 1) полнотекстовый поиск в ES если нет в кэше
        query = {"query": {"match": {"content": term}}}
        resp = await es.search(index="materials", body=query, size=1000)
        class_ids = [int(hit["_source"]["class_id"]) for hit in resp["hits"]["hits"]]
        logger.info(f"class ids: {class_ids}")
        if not class_ids:
            return None
        await set_cached_data(app.state.redis, es_cache_key, class_ids)
    else:
        class_ids = cached_ids
        
    # 2) фильтрация по дате в Postgres
    sch = Table('shedule')
    q = (
        PypikaQuery
        .from_(sch)
        .select(sch.shedule_id).distinct()
        .where(sch.class_id.isin(class_ids))
        .where(sch.start_time.between(start, end))
    )
    rows = await pool.fetch(q.get_sql())
    return {r["shedule_id"] for r in rows}


async def fetch_attendance(
    neo4j: AsyncGraphDatabase,
    lecture_ids: set[int]
) -> dict[int, tuple[int, int]]:
    """
    """
    cypher = """
            MATCH (s:Student)-[:BELONGS_TO]->(:Group)-[:HAS_SCHEDULE]->(sch:Schedule)
            WHERE sch.id IN $schedule_ids
            OPTIONAL MATCH (s)-[a:ATTENDED]->(sch)
            WITH s.id AS student_id,
                 count(sch) AS total_cnt,      
                 count(a)   AS attended_cnt    
            RETURN student_id, attended_cnt, total_cnt
        """

    async with neo4j.session(database="neo4j") as sess:
        result = await sess.run(cypher, schedule_ids=list(lecture_ids))
        rows   = await result.data()
    return {r["student_id"]: (r["attended_cnt"], r["total_cnt"]) for r in rows}


async def fetch_student_details(pool, mongo, redis, student_ids: list[int]) -> dict[int, dict]:
    """Получение информации о студентах"""
    details: dict[int, dict] = {}
    missed_ids: list[int] = []

    # 1) Разом забираем из Redis всё
    raw_values = await redis.mget(*[str(sid) for sid in student_ids])
    for sid, raw in zip(student_ids, raw_values):
        if raw:
            logger.info(f"Cache hit: sid {sid} of {student_ids}")
            msg = json.loads(raw)
            after = msg.get("after", {})
            details[sid] = {
                "code":      after.get("code", ""),
                "full_name": after.get("full_name", ""),
                "group":     after.get("group_name", ""),
                "specialty": after.get("specialty", ""),
                "dept_id":   after.get("dept_id", None)
            }
        else:
            logger.info(f"Cache miss: sid {sid} of {student_ids}")
            missed_ids.append(sid)

    # 2) Для тех, кого нет в Redis, подгружаем из Postgres
    if missed_ids:
        s, g, sp = Table('students'), Table('groups'), Table('specialties')
        q = (
            PypikaQuery
            .from_(s)
            .join(g).on(s.group_id == g.group_id)
            .join(sp).on(g.spec_id == sp.spec_id)
            .select(
                s.student_id,
                s.code,
                s.full_name,
                g.name.as_('group_name'),
                sp.name.as_('specialty'),
                sp.dept_id.as_('dept_id')
            )
            .where(s.student_id.isin(missed_ids))
        )
        rows = await pool.fetch(q.get_sql())
        for r in rows:
            sid = r['student_id']
            details[sid] = {
                "code":      r["code"],
                "full_name": r["full_name"],
                "group":     r["group_name"],
                "specialty": r["specialty"],
                "dept_id":   r["dept_id"]
            }

    # 3) Собираем все dept_id, чтобы получить имена кафедр из Mongo
    dept_ids = {info["dept_id"] for info in details.values() if info.get("dept_id") is not None}
    if not dept_ids:
        return {sid: {**v, "department": ""} for sid, v in details.items()}

    # 2) Из MongoDB получаем названия кафедр по dept_id
    pipeline = [
        {"$unwind": "$institutes"},
        {"$unwind": "$institutes.departments"},
        {"$match": {
            "institutes.departments.department_id": {"$in": list(dept_ids)}
        }},
        {"$project": {
            "_id": 0,
            "department_id": "$institutes.departments.department_id",
            "department_name": "$institutes.departments.name",
            "institute_id": "$institutes.institute_id",
            "institute_name": "$institutes.name"
        }}
    ]
    cursor = mongo.universities.aggregate(pipeline)
    docs = await cursor.to_list(length=None)

    dept_map = {d["department_id"]: d["department_name"] for d in docs}
    inst_map = {d["department_id"]: d["institute_name"] for d in docs}


    for sid, rec in details.items():
        did = rec.pop("dept_id", None)
        rec["department"] = dept_map.get(did, "")
        rec["institute"] = inst_map.get(did, "")

    return details

@app.get("/report", response_model=ReportResponse)
async def generate_report(
    term: str = Query("введение", description="Search term for lectures"),
    start: str = Query("2023-09-01", description="Start date YYYY-MM-DD"),
    end: str = Query("2023-10-16", description="End date YYYY-MM-DD")
):
    """Генерация отчета о посещаемости лекций с заданными параметрами"""
    logger.info("Generating report for term='%s', period=%s to %s", term, start, end)
    
    # Проверяем кэш
    cache_key = generate_cache_key("report", term, start, end)
    cached_data = await get_cached_data(app.state.redis, cache_key)
    if cached_data:
        logger.info("Returning cached report data")
        return ReportResponse(**cached_data)

    # 1. Поиск и фильтрация lecture_ids
    lecture_ids = await fetch_lecture_ids(app.state.es, app.state.db, term, start, end)
    if not lecture_ids:
        logger.warning("No lectures found for term '%s' and period %s-%s", term, start, end)
        raise HTTPException(status_code=404, detail="No lectures found for given term and period")
    logger.info(" Found lecture_ids: %s", lecture_ids)

    # 2. Получение данных о посещаемости
    attendance = await fetch_attendance(app.state.neo4j, lecture_ids)
    logger.info(" Found attendance: %s", attendance)

    # 3. Расчёт процента посещаемости
    students_pct = []
    for sid, (att, total) in attendance.items():
        pct = (att / total) * 100 if total > 0 else 0
        students_pct.append((sid, pct))
    # сортировка по возрастанию процента
    students_pct.sort(key=lambda x: x[1])

    # 4. Выбор 10 студентов с минимальной посещаемостью
    top10 = students_pct[:10]
    student_ids = [sid for sid, _ in top10]
    logger.info(" Top 10 student_ids: %s", student_ids)

    # 5. Детали студентов
    details = await fetch_student_details(app.state.db, app.state.mongo, app.state.redis, student_ids)

    # 6. Формирование отчёта
    report_students = []
    for sid, pct in top10:
        det = details.get(sid, {})
        report_students.append(
            StudentReport(
                student_id=sid,
                code=det.get("code", ""),
                full_name=det.get("full_name", ""),
                group=det.get("group", ""),
                specialty=det.get("specialty", ""),
                department=det.get("department", ""),
                institute=det.get("institute", ""),
                attendance_percent=round(pct, 2)
            )
        )

    response = ReportResponse(
        term=term,
        period={"start": start, "end": end},
        students=report_students,
        total_lectures=len(lecture_ids),
        timestamp=datetime.utcnow()
    )
    
    # Сохраняем результат в кэш
    await set_cached_data(app.state.redis, cache_key, response.model_dump())
    
    logger.info("Report generated and cached: %d students, %d lectures", len(report_students), len(lecture_ids))
    return response

if __name__ == "__main__":
    uvicorn.run(
        "app_1.main_1:app",
        host="127.0.0.1",
        port=8001,
        workers=1
    )
