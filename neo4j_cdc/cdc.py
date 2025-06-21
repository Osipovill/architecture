import os
import asyncio
import json
import logging
from aiokafka import AIOKafkaConsumer
from neo4j import AsyncGraphDatabase
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("neo4j_cdc")

# Буферы для отложенных операций
pending_students: dict[int, dict] = {}
pending_schedules: dict[int, dict] = {}
pending_att: dict[int, list[dict]] = {}


KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:29092")
KAFKA_GROUP_ID  = "neo4j_hierarchy_group"
KAFKA_TOPICS    = [
    "university_db.public.groups",
    "university_db.public.students",
    "university_db.public.shedule_full_materialized",
    "university_db.public.attendances",
]

NEO4J_URI      = os.getenv("NEO4J_URI", "neo4j://neo4j:7687")
NEO4J_USER     = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "P@ssw0rd")

driver: AsyncGraphDatabase

async def flush_att_for_student(session, sid):
    """Если для студента есть buffered attendances — обработать их."""
    if sid not in pending_att:
        return
    for after in pending_att.pop(sid):
        await _do_attendance(session, after)
    logger.info(f"Flushed buffered attendances for student={sid}")

async def _do_attendance(session, after):
    sid = after["student_id"]
    sch = after["shedule_id"]
    await session.run(
        """
        MERGE (s:Student {id:$sid})
        MERGE (sch:Schedule {id:$sch})
        MERGE (s)-[:ATTENDED]->(sch)
        """,
        sid=sid,
        sch=sch
    )
    logger.info(f"Attendance upserted: student={sid} → schedule={sch}")

async def handle_group(session, after):
    await session.run(
        """
        MERGE (g:Group {id:$id})
        ON CREATE SET g.code = $name
        ON MATCH  SET g.code = $name
        """,
        id=after["group_id"],
        name=after["name"]
    )
    logger.info(f"Group upserted: {after['group_id']}")

async def handle_group_delete(session, before):
    await session.run(
        "MATCH (g:Group {id:$id}) DETACH DELETE g",
        id=before["group_id"]
    )
    logger.info(f"Group deleted: {before['group_id']}")

async def handle_student(session, after):
    sid = after["student_id"]
    gid = after["group_id"]
    # создаём группу-заглушку, если вдруг её нет
    await session.run(
        """
        MERGE (g:Group {id:$gid})
        MERGE (s:Student {id:$sid})
        SET s.name = $full_name
        MERGE (s)-[:BELONGS_TO]->(g)
        """,
        sid=sid,
        full_name=after["full_name"],
        gid=gid
    )
    logger.info(f"Student upserted: {sid}")

    # после появления студента — можно сбросить buffered attendances
    await flush_att_for_student(session, sid)

async def handle_student_delete(session, before):
    await session.run(
        "MATCH (s:Student {id:$sid}) DETACH DELETE s",
        sid=before["student_id"]
    )
    logger.info(f"Student deleted: {before['student_id']}")

async def handle_schedule(session, after):
    sid = after["shedule_id"]
    await session.run(
        """
        MERGE (sch:Schedule {id: $sid})
        ON CREATE SET
          sch.title        = $title,
          sch.date         = date("1970-01-01") + duration({ days: $start_time }),
          sch.duration     = $duration,
          sch.course_id    = $course_id,
          sch.course_title = $course_title,
          sch.tag          = $tag
        ON MATCH SET
          sch.title        = $title,
          sch.date         = date("1970-01-01") + duration({ days: $start_time }),
          sch.duration     = $duration,
          sch.course_id    = $course_id,
          sch.course_title = $course_title,
          sch.tag          = $tag
        WITH sch
        MATCH (g:Group {id: $gid})
        MERGE (g)-[:HAS_SCHEDULE]->(sch)
        """,
        sid=sid,
        title=after["title"],
        start_time=after["start_time"],
        duration=after["duration"],
        course_id=after["course_id"],
        course_title=after["course_title"],
        tag=after["tag"],
        gid=after["group_id"],
    )
    logger.info(f"Schedule upserted: {sid}")


async def handle_schedule_delete(session, before):
    await session.run(
        "MATCH (sch:Schedule {id:$sid}) DETACH DELETE sch",
        sid=before["shedule_id"]
    )
    logger.info(f"Schedule deleted: {before['shedule_id']}")

async def handle_attendance(session, after):
    sid = after["student_id"]
    sch = after["shedule_id"]

    # По умолчанию считаем presence == True (если поле отсутствует)
    presence = after.get("presence", True)

    if not presence:
        # Если presence == False — удалить связь
        await session.run(
            """
            MATCH (s:Student {id:$sid})-[r:ATTENDED]->(sch:Schedule {id:$sch})
            DELETE r
            """,
            sid=sid,
            sch=sch
        )
        logger.info(f"Attendance REMOVED (presence=False): student={sid} → schedule={sch}")
        return

    # если студента нет — буферизовать
    result = await session.run(
        "MATCH (s:Student {id:$sid}) RETURN s", sid=sid
    )
    if await result.single() is None:
        pending_att.setdefault(sid, []).append(after)
        logger.info(f"Buffered attendance for student={sid} → schedule={sch}")
        return

    await _do_attendance(session, after)

async def handle_attendance_delete(session, before):
    await session.run(
        """
        MATCH (s:Student {id:$sid})-[r:ATTENDED]->(sch:Schedule {id:$sch})
        DELETE r
        """,
        sid=before["student_id"],
        sch=before["shedule_id"]
    )
    logger.info(f"Attendance deleted: student={before['student_id']} → schedule={before['shedule_id']}")

async def consume():
    global driver
    driver = AsyncGraphDatabase.driver(
        NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
    )

    consumer = AIOKafkaConsumer(
        *KAFKA_TOPICS,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=KAFKA_GROUP_ID,
        auto_offset_reset='earliest',
        enable_auto_commit=False,
        value_deserializer=lambda v: json.loads(v.decode()) if v is not None else None
    )
    await consumer.start()
    try:
        async for msg in consumer:
            payload = msg.value

            if payload is None:
                continue

            op = payload.get("op")
            if op not in ('c', 'u', 'd', 'r'):
                continue

            before = payload.get("before") or {}
            after = payload.get("after") or {}
            table = msg.topic.split('.')[-1]

            async with driver.session() as session:
                if table == "groups":
                    if op == 'd':
                        await handle_group_delete(session, before)
                    else:
                        await handle_group(session, after)

                elif table == "students":
                    if op == 'd':
                        await handle_student_delete(session, before)
                    else:
                        await handle_student(session, after)

                elif table == "shedule_full_materialized":
                    if op == 'd':
                        await handle_schedule_delete(session, before)
                    else:
                        await handle_schedule(session, after)

                elif table == "attendances":
                    if op == 'd':
                        await handle_attendance_delete(session, before)
                    else:
                        await handle_attendance(session, after)

            await consumer.commit()
    finally:
        await consumer.stop()
        await driver.close()

if __name__ == "__main__":
    asyncio.run(consume())
