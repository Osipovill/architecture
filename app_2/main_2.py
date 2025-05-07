from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import asyncpg
from neo4j import AsyncGraphDatabase
from pypika import Query as PypikaQuery, Table

# ----------------- CONFIGURATION -----------------
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

# ----------------- LOGGING -----------------
logger = logging.getLogger("app2_service")
if not logger.handlers:
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    logger.propagate = False

# ----------------- LIFESPAN -----------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = await asyncpg.create_pool(dsn=settings.postgres_dsn)
    app.state.neo4j = AsyncGraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )
    yield
    await app.state.db.close()
    await app.state.neo4j.close()

app = FastAPI(title="App2 Service", lifespan=lifespan)

# ----------------- Pydantic Models -----------------
class CourseReport(BaseModel):
    course_title: str
    class_title: str
    type: str
    date: str
    duration: int
    requirements: str
    student_count: int

# ----------------- BUSINESS LOGIC -----------------

async def fetch_classes(pool, course_title, year, semester, requirements=None):
    c  = Table('courses')
    cl = Table('classes')

    q = (
        PypikaQuery
        .from_(c)
        .join(cl).on(cl.course_id == c.course_id)
        .select(
            c.title.as_('course_title'),
            cl.title.as_('class_title'),
            cl.type,
            cl.date,
            cl.duration,
            cl.requirements,
            cl.class_id
        )
        .where(c.title.ilike(f'%{course_title}%'))
    )
    if requirements:
        q = q.where(cl.requirements.ilike(f'%{requirements}%'))

    sql = q.get_sql()

    filters: list[str] = []
    if year is not None:
        filters.append(f"EXTRACT(YEAR FROM classes.date) = {year}")
    if semester is not None:
        if semester == 1:
            filters.append("EXTRACT(MONTH FROM classes.date) BETWEEN 1 AND 6")
        else:
            filters.append("EXTRACT(MONTH FROM classes.date) BETWEEN 7 AND 12")

    if filters:
        sql += " AND " + " AND ".join(filters)

    return await pool.fetch(sql)

async def fetch_student_count(neo4j_driver, class_info) -> int:
    cypher = """
        MATCH (s:Student)-[:ATTENDED]->(sch:Schedule {title: $title, date: date($date)})
        RETURN COUNT(DISTINCT s) as student_count
    """
    async with neo4j_driver.session() as session:
        result = await session.run(cypher, title=class_info["class_title"], date=class_info["date"].strftime('%Y-%m-%d'))
        record = await result.single()
        return record["student_count"] if record else 0

# ----------------- ROUTES -----------------
@app.get("/api/course-attendance/{course_title}", response_model=List[CourseReport])
async def get_course_attendance(
    course_title: str, 
    year: Optional[int] = None, 
    semester: Optional[int] = None,
    requirements: Optional[str] = None
):
    logger.info(f"Generating course attendance report for course_title={course_title}, year={year}, semester={semester}, requirements={requirements}")
    pool = app.state.db
    neo4j_driver = app.state.neo4j
    classes = await fetch_classes(pool, course_title, year, semester, requirements)
    if not classes:
        logger.warning("Course or classes not found")
        raise HTTPException(status_code=404, detail="Course or classes not found")
    results = []
    for class_info in classes:
        student_count = await fetch_student_count(neo4j_driver, class_info)
        results.append(CourseReport(
            course_title=class_info["course_title"],
            class_title=class_info["class_title"],
            type=class_info["type"],
            date=class_info["date"].strftime('%Y-%m-%d'),
            duration=class_info["duration"],
            requirements=class_info["requirements"],
            student_count=student_count
        ))
    logger.info(f"Report generated: {len(results)} classes")
    return results

if __name__ == "__main__":
    uvicorn.run(
        "app_2.main_2:app",
        host="127.0.0.1",
        port=8002,
        workers=1
    )