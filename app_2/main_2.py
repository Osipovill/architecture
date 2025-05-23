from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from typing import List, Optional
from datetime import datetime
import json
from json import JSONEncoder

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import asyncpg
from neo4j import AsyncGraphDatabase
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
    """Настройки приложения, загружаемые из переменных окружения"""
    postgres_dsn: str = Field(..., env="POSTGRES_DSN")
    redis_dsn: str = Field(..., env="REDIS_DSN")
    neo4j_uri: str = Field(..., env="NEO4J_URI")
    neo4j_user: str = Field(..., env="NEO4J_USER")
    neo4j_password: str = Field(..., env="NEO4J_PASSWORD")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # разрешить игнорировать любые доп. ключи из .env

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

# ----------------- CACHE -----------------
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

# ----------------- LIFESPAN -----------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация при запуске
    logger.info("Запуск сервиса App2...")
    app.state.db = await asyncpg.create_pool(dsn=settings.postgres_dsn)
    app.state.neo4j = AsyncGraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )
    app.state.redis = aioredis.from_url(settings.redis_dsn, decode_responses=True)
    logger.info("Успешное подключение ко всем базам данных")
    yield
    # Очистка при завершении
    logger.info("Завершение работы сервиса App2...")
    await app.state.db.close()
    await app.state.neo4j.close()
    await app.state.redis.close()
    logger.info("Все соединения закрыты")

app = FastAPI(title="App2 Service", lifespan=lifespan)

# ----------------- Pydantic Models -----------------
class CourseReport(BaseModel):
    course_title: str
    class_title: str
    tag: str
    type: str
    date: str
    duration: int
    requirements: str
    student_count: int

# ----------------- BUSINESS LOGIC -----------------

async def fetch_classes(pool, course_title, year, semester, requirements=None):
    """Получение списка занятий из PostgreSQL с опциональной фильтрацией"""
    logger.info(f"Поиск занятий с параметрами: course_title={course_title}, year={year}, semester={semester}, requirements={requirements}")
    
    c = Table('courses')
    cl = Table('classes')

    q = (
        PypikaQuery
        .from_(c)
        .join(cl).on(cl.course_id == c.course_id)
        .select(
            c.title.as_('course_title'),
            cl.title.as_('class_title'),
            cl.tag,
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

    classes = await pool.fetch(sql)
    logger.info(f"Найдено {len(classes)} подходящих занятий")
    return classes

async def fetch_student_count(neo4j_driver, class_info) -> int:
    """Получение количества студентов, посетивших занятие, из Neo4j"""
    logger.info(f"Подсчет студентов для занятия: {class_info['class_title']} ({class_info['date']})")
    
    cypher = """
        MATCH (s:Student)-[:ATTENDED]->(sch:Schedule {title: $title, date: date($date)})
        RETURN COUNT(DISTINCT s) as student_count
    """
    async with neo4j_driver.session() as session:
        result = await session.run(cypher, title=class_info["class_title"], date=class_info["date"].strftime('%Y-%m-%d'))
        record = await result.single()
        count = record["student_count"] if record else 0
        logger.info(f"Найдено {count} студентов для занятия {class_info['class_title']}")
        return count

# ----------------- ROUTES -----------------
@app.get("/api/course-attendance/{course_title}", response_model=List[CourseReport])
async def get_course_attendance(
    course_title: str, 
    year: Optional[int] = None, 
    semester: Optional[int] = None,
    requirements: Optional[str] = None
):
    """
    Генерация отчета о посещаемости курса с опциональной фильтрацией
    
    Args:
        course_title: название курса
        year: год для фильтрации
        semester: семестр (1 или 2)
        requirements: требования для фильтрации
    """
    logger.info(f"Генерация отчета о посещаемости для: course_title={course_title}, year={year}, semester={semester}, requirements={requirements}")

    # Проверка кэша
    cache_key = generate_cache_key("course_attendance", course_title, year, semester, requirements)
    cached_data = await get_cached_data(app.state.redis, cache_key)
    if cached_data:
        logger.info("Возврат данных из кэша")
        return [CourseReport(**item) for item in cached_data]

    pool = app.state.db
    neo4j_driver = app.state.neo4j
    
    # Получение списка занятий
    classes = await fetch_classes(pool, course_title, year, semester, requirements)
    if not classes:
        logger.warning("Курс или занятия не найдены")
        raise HTTPException(status_code=404, detail="Course or classes not found")

    # Формирование отчета
    results = []
    for class_info in classes:
        student_count = await fetch_student_count(neo4j_driver, class_info)
        results.append(CourseReport(
            course_title=class_info["course_title"],
            class_title=class_info["class_title"],
            tag=class_info["tag"],
            type=class_info["type"],
            date=class_info["date"].strftime('%Y-%m-%d'),
            duration=class_info["duration"],
            requirements=class_info["requirements"],
            student_count=student_count
        ))

    # Кэширование результатов
    await set_cached_data(app.state.redis, cache_key, [r.model_dump() for r in results])
    
    logger.info(f"Отчет успешно сгенерирован: {len(results)} занятий")
    return results

if __name__ == "__main__":
    uvicorn.run(
        "app_2.main_2:app",
        host="127.0.0.1",
        port=8002,
        workers=1
    )