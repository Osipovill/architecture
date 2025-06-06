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
    await app.state.redis.close()

class StudentReport(BaseModel):
    student_id: int
    code: str
    full_name: str
    group: str
    specialty: str
    department: str
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
        all_ids = [int(hit["_source"]["class_id"]) for hit in resp["hits"]["hits"]]
        if not all_ids:
            return None
            
        # Кэшируем результаты поиска
        await set_cached_data(app.state.redis, es_cache_key, all_ids)
    else:
        all_ids = cached_ids
        
    # 2) фильтрация по дате в Postgres
    sch = Table('shedule')
    q = (
        PypikaQuery
        .from_(sch)
        .select(sch.class_id).distinct()
        .where(sch.class_id.isin(all_ids))
        .where(sch.start_time.between(start, end))
    )
    sql = q.get_sql()
    rows = await pool.fetch(sql)
    return {r['class_id'] for r in rows}

async def fetch_attendance(pool, lecture_ids: list[int]) -> dict[int, tuple[int, int]]:
    """Подсчет статистики посещаемости по списку лекций"""
    a = Table('attendances')
    s = Table('shedule')

    q = (
        PypikaQuery
        .from_(a)
        .join(s).on(a.shedule_id == s.shedule_id)
        .select(
            a.student_id,
            Sum(
                Case()
                .when(a.presence == True, 1)
                .else_(0)
            ).as_('attended'),
            Count(a.student_id).as_('total')
        )
        .where(s.class_id.isin(lecture_ids))
        .groupby(a.student_id)
    )
    sql = q.get_sql()
    rows = await pool.fetch(sql)
    result = {r["student_id"]: (r["attended"], r["total"]) for r in rows}
    return result


async def fetch_student_details(pool, mongo, student_ids: list[int]) -> dict[int, dict]:
    """Получение информации о студентах из базы данных"""
    s = Table('students')
    g = Table('groups')
    sp = Table('specialties')

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
        .where(s.student_id.isin(student_ids))
    )
    sql = q.get_sql()
    rows = await pool.fetch(sql)
    details = {}
    dept_ids = set()
    for r in rows:
        sid = r['student_id']
        did = r['dept_id']
        details[sid] = {
            "code":       r["code"],
            "full_name":  r["full_name"],
            "group":      r["group_name"],
            "specialty":  r["specialty"],
            "dept_id":    did  
        }
        dept_ids.add(did)

    if not dept_ids:
        return {sid: {**v, "department": ""} for sid, v in details.items()}

    # 2) Из MongoDB получаем названия кафедр по dept_id
    pipeline = [
        { "$unwind": "$institutes" },
        { "$unwind": "$institutes.departments" },
        { "$match": { "institutes.departments.department_id": { "$in": list(dept_ids) } } },
        { "$project": {
            "_id": 0,
            "department_id": "$institutes.departments.department_id",
            "department_name": "$institutes.departments.name"
        } }
    ]
    cursor = mongo.universities.aggregate(pipeline)
    docs = await cursor.to_list(length=None)

    dept_map = { doc["department_id"]: doc["department_name"] for doc in docs }

    # 3) Вкладываем department_name в детали и убираем dept_id
    for sid, info in details.items():
        info["department"] = dept_map.get(info["dept_id"], "")
        del info["dept_id"]

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
    attendance = await fetch_attendance(app.state.db, lecture_ids)
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
    details = await fetch_student_details(app.state.db, app.state.mongo, student_ids)

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
