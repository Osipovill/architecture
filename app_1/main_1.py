import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import asyncpg
from elasticsearch import AsyncElasticsearch
import aioredis

# ----------------- CONFIGURATION -----------------
# Используем имена сервисов из docker-compose
DB_DSN = os.getenv(
    "POSTGRES_DSN",
    "postgresql://admin:P@ssw0rd@postgres:5432/university"
)
ES_HOST = os.getenv("ES_HOST", "http://elasticsearch:9200")
REDIS_DSN = os.getenv("REDIS_DSN", "redis://redis:6379/0")

# ----------------- Pydantic Models -----------------
class StudentReport(BaseModel):
    student_id: int
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

# ----------------- INITIALIZE SERVICES -----------------
app = FastAPI(title="Lab1 Service")

@app.on_event("startup")
async def startup():
    # Подключение к PostgreSQL
    app.state.db = await asyncpg.create_pool(dsn=DB_DSN)
    # Подключение к Elasticsearch
    app.state.es = AsyncElasticsearch([ES_HOST])
    # Подключение к Redis
    app.state.redis = await aioredis.create_redis_pool(REDIS_DSN)

@app.on_event("shutdown")
async def shutdown():
    await app.state.db.close()
    await app.state.es.close()
    app.state.redis.close()
    await app.state.redis.wait_closed()

# ----------------- BUSINESS LOGIC -----------------
async def fetch_lecture_ids(es, term: str, start: str, end: str) -> list[int]:
    query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"content": term}},
                    {"range": {"date": {"gte": start, "lte": end}}}
                ]
            }
        }
    }
    resp = await es.search(index="materials", body=query, size=1000)
    return [int(hit["_source"]["class_id"]) for hit in resp["hits"]["hits"]]

async def fetch_attendance(pool, lecture_ids: list[int]) -> dict[int, tuple[int, int]]:
    sql = """
        SELECT student_id,
               SUM(CASE WHEN presence THEN 1 ELSE 0 END) AS attended,
               COUNT(*) AS total
        FROM attendances
        WHERE class_id = ANY($1)
        GROUP BY student_id;
    """
    rows = await pool.fetch(sql, lecture_ids)
    return {r["student_id"]: (r["attended"], r["total"]) for r in rows}

async def fetch_student_details(pool, student_ids: list[int]) -> dict[int, dict]:
    sql = """
        SELECT s.student_id, s.full_name, g.name AS group_name,
               sp.name AS specialty, d.name AS department
        FROM students s
        JOIN groups g ON s.group_id = g.group_id
        JOIN specialties sp ON g.spec_id = sp.spec_id
        JOIN departments d ON sp.dept_id = d.dept_id
        WHERE s.student_id = ANY($1);
    """
    rows = await pool.fetch(sql, student_ids)
    result = {}
    for r in rows:
        result[r["student_id"]] = {
            "full_name": r["full_name"],
            "group": r["group_name"],
            "specialty": r["specialty"],
            "department": r["department"],
        }
    return result

# ----------------- ROUTE -----------------
@app.get("/report", response_model=ReportResponse)
async def generate_report(
    term: str = Query(..., description="Search term for lectures"),
    start: str = Query(..., description="Start date YYYY-MM-DD"),
    end: str = Query(..., description="End date YYYY-MM-DD")
):
    # 1. Поиск лекций по ключевому слову
    lecture_ids = await fetch_lecture_ids(app.state.es, term, start, end)
    if not lecture_ids:
        raise HTTPException(status_code=404, detail="No lectures found for given term and period")

    # 2. Получение данных о посещаемости
    attendance = await fetch_attendance(app.state.db, lecture_ids)

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

    # 5. Детали студентов
    details = await fetch_student_details(app.state.db, student_ids)

    # 6. Формирование отчёта
    report_students = []
    for sid, pct in top10:
        det = details.get(sid, {})
        report_students.append(
            StudentReport(
                student_id=sid,
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
    return response