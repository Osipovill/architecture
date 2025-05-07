#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import random
from datetime import date, timedelta

import psycopg2
from neo4j import GraphDatabase

# === Настройки из окружения ===
POSTGRES_DSN   = os.getenv("POSTGRES_DSN", "postgresql://admin:P%40ssw0rd@localhost:5433/university")
ES_HOST        = os.getenv("ES_HOST", "http://localhost:9200")           # Для Elasticsearch
REDIS_DSN      = os.getenv("REDIS_DSN", "redis://localhost:6379/0")     # Для Redis
NEO4J_URI      = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "P@ssw0rd")


def generate_pg_data():
    # Подключаемся по DSN
    conn = psycopg2.connect(dsn=POSTGRES_DSN)
    cur  = conn.cursor()

    print("Генерируем новые занятия в PostgreSQL...")
    class_types = ['Лекция', 'Семинар', 'Лабораторная']
    tags        = ['специальная', 'общая']

    # Получаем существующие course_id
    cur.execute("SELECT course_id FROM courses")
    courses = [row[0] for row in cur.fetchall()]

    for i in range(11, 21):
        ctype     = random.choice(class_types)
        title     = f"{ctype} по теме #{i}"
        req       = "Ноутбук, проектор"
        cls_date  = date(2023, 9, 1) + timedelta(days=random.randint(0, 90))
        duration  = random.choice([60, 90, 120])
        tag       = random.choice(tags)
        course_id = random.choice(courses)

        cur.execute(
            """
            INSERT INTO classes (type, title, requirements, date, duration, tag, course_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (ctype, title, req, cls_date, duration, tag, course_id)
        )

    print("Генерируем расписания (shedule)...")
    cur.execute("SELECT class_id, title, date FROM classes")
    all_classes = cur.fetchall()

    for class_id, title, cls_date in all_classes:
        cur.execute(
            """
            INSERT INTO shedule (title, start_time, end_time, class_id)
            VALUES (%s, %s, %s, %s)
            """,
            (title, cls_date, cls_date, class_id)
        )

    print("Генерируем записи о посещении...")
    cur.execute("SELECT student_id FROM students")
    students = [row[0] for row in cur.fetchall()]
    cur.execute("SELECT shedule_id FROM shedule")
    schedules = [row[0] for row in cur.fetchall()]

    for student_id in students:
        for sch_id in random.sample(schedules, k=random.randint(3, 7)):
            presence   = random.choice([True, False])
            visit_date = date.today() - timedelta(days=random.randint(0, 30))
            cur.execute(
                """
                INSERT INTO attendances (student_id, shedule_id, presence, date)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (student_id, shedule_id) DO NOTHING
                """,
                (student_id, sch_id, presence, visit_date)
            )

    conn.commit()
    cur.close()
    conn.close()
    print("Данные в PostgreSQL сгенерированы и сохранены.")


def populate_neo4j_from_pg():
    print("Заливаем данные в Neo4j...")
    conn = psycopg2.connect(dsn=POSTGRES_DSN)
    cur  = conn.cursor()

    # Извлекаем данные
    cur.execute("SELECT group_id, name FROM groups")
    groups    = cur.fetchall()
    cur.execute("SELECT student_id, full_name, group_id FROM students")
    students  = cur.fetchall()
    cur.execute("SELECT shedule_id, title, start_time FROM shedule")
    schedules = cur.fetchall()
    cur.execute("SELECT student_id, shedule_id FROM attendances WHERE presence = TRUE")
    attends   = cur.fetchall()

    cur.close()
    conn.close()

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

        for group_id, code in groups:
            session.run(
                "CREATE (:Group {id: $id, code: $code})",
                id=group_id, code=code
            )

        for student_id, full_name, group_id in students:
            session.run(
                """
                MATCH (g:Group {id: $gid})
                CREATE (:Student {id: $sid, name: $name})-[:MEMBER_OF]->(g)
                """,
                sid=student_id, name=full_name, gid=group_id
            )

        for sch_id, title, dt in schedules:
            session.run(
                "CREATE (:Schedule {id: $id, title: $title, date: date($date)})",
                id=sch_id, title=title, date=dt.isoformat()
            )

        for student_id, sch_id in attends:
            session.run(
                """
                MATCH (s:Student {id: $sid}), (sch:Schedule {id: $schid})
                CREATE (s)-[:ATTENDED]->(sch)
                """,
                sid=student_id, schid=sch_id
            )

    driver.close()
    print("Neo4j: данные загружены.")


if __name__ == "__main__":
    generate_pg_data()
    populate_neo4j_from_pg()
