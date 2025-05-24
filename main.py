#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import random
from datetime import date, timedelta

import psycopg2
from neo4j import GraphDatabase

import os

# —————— Важно! ——————
# Чтобы libpq (библиотека, на которой основан psycopg2) сразу шла с UTF-8,
# нужно задать переменную окружения PGCLIENTENCODING до импорта psycopg2.
os.environ.setdefault('PGCLIENTENCODING', 'UTF8')


# === Настройки из окружения ===
PG_HOST       = os.getenv("PG_HOST",       "localhost")
PG_PORT       = os.getenv("PG_PORT",       "5433")
PG_DB         = os.getenv("PG_DB",         "university")
PG_USER       = os.getenv("PG_USER",       "admin")
PG_PASSWORD   = os.getenv("PG_PASSWORD",   "P@ssw0rd")

NEO4J_URI      = os.getenv("NEO4J_URI",      "neo4j://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "P@ssw0rd")


def get_pg_connection():
    """
    Создаёт соединение с PostgreSQL,
    без использования URL-DSN, и сразу
    гарантирует UTF-8 для всeх сообщений.
    """
    conn = psycopg2.connect(f"host={PG_HOST} port={PG_PORT} dbname={PG_DB} user={PG_USER} password={PG_PASSWORD}")
    # на всякий случай ещё раз ставим кодировку клиента
    conn.set_client_encoding("UTF8")
    return conn


def generate_pg_data():
    conn = get_pg_connection()
    cur  = conn.cursor()

    print("=== Генерация случайных занятий в PostgreSQL ===")
    class_types = ['Лекция', 'Семинар', 'Лабораторная']
    tags        = ['специальная', 'общая']

    cur.execute("SELECT COALESCE(MAX(class_id), 0) FROM classes")
    max_class_before = cur.fetchone()[0]

    cur.execute("SELECT course_id FROM courses")
    courses = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT student_id FROM students")
    students = [r[0] for r in cur.fetchall()]

    new_classes = []
    for course_id in courses:
        for i in range(random.randint(8, 15)):
            ctype    = random.choice(class_types)
            title    = f"{ctype} по курсу #{course_id}, тема {i+1}"
            req      = random.choice([
                "Ноутбук, проектор",
                "Тетрадь, ручка",
                "Калькулятор, ноутбук",
                "Учебник, микроскоп"
            ])
            cls_date = date(2023, 9, 1) + timedelta(days=random.randint(0, 120))
            duration = 120
            tag      = random.choice(tags)

            cur.execute(
                """
                INSERT INTO classes
                  (type, title, requirements, date, duration, tag, course_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING class_id
                """,
                (ctype, title, req, cls_date, duration, tag, course_id)
            )
            new_classes.append(cur.fetchone()[0])

    conn.commit()

    cur.execute(
        "SELECT class_id, title, date FROM classes WHERE class_id > %s",
        (max_class_before,)
    )
    new_classes = cur.fetchall()
    print(f"Сгенерировано {len(new_classes)} занятий.")

    print("=== Генерация расписаний для новых занятий ===")
    cur.execute("SELECT COALESCE(MAX(shedule_id), 0) FROM shedule")
    max_sch_before = cur.fetchone()[0]

    new_schedules = []
    for class_id, title, cls_date in new_classes:
        cur.execute(
            """
            INSERT INTO shedule (title, start_time, end_time, class_id)
            VALUES (%s, %s, %s, %s)
            RETURNING shedule_id
            """,
            (title, cls_date, cls_date, class_id)
        )
        new_schedules.append(cur.fetchone()[0])

    conn.commit()

    print("=== Генерация записей о посещении ===")
    for sid in students:
        picked = random.sample(new_schedules, k=random.randint(5, min(len(new_schedules), 10)))
        for sch_id in picked:
            presence   = random.choice([True, False])
            visit_date = date.today() - timedelta(days=random.randint(0, 30))
            cur.execute(
                """
                INSERT INTO attendances
                  (student_id, shedule_id, presence, date)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (student_id, shedule_id) DO NOTHING
                """,
                (sid, sch_id, presence, visit_date)
            )

    conn.commit()
    cur.close()
    conn.close()
    print("=== Данные PostgreSQL сгенерированы. ===")


def generate_more_attendance():
    conn = get_pg_connection()
    cur  = conn.cursor()

    print("=== Генерация дополнительных посещений ===")
    cur.execute("SELECT shedule_id FROM shedule")
    schedule_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT student_id FROM students")
    student_ids  = [r[0] for r in cur.fetchall()]

    for sid in student_ids:
        for sch_id in schedule_ids:
            cur.execute(
                "SELECT 1 FROM attendances WHERE student_id=%s AND shedule_id=%s",
                (sid, sch_id)
            )
            if cur.fetchone():
                continue
            presence   = random.random() < 0.7
            visit_date = date.today() - timedelta(days=random.randint(0, 30))
            cur.execute(
                """
                INSERT INTO attendances (student_id, shedule_id, presence, date)
                VALUES (%s, %s, %s, %s)
                """,
                (sid, sch_id, presence, visit_date)
            )

    conn.commit()
    cur.close()
    conn.close()
    print("=== Дополнительные посещения сгенерированы. ===")


def populate_neo4j_from_pg():
    print("=== Загрузка данных в Neo4j ===")
    conn = psycopg2.connect(host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD)
    cur  = conn.cursor()

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

        for gid, code in groups:
            session.run("CREATE (:Group {id:$id, code:$code})", id=gid, code=code)

        for sid, name, gid in students:
            session.run(
                """
                MATCH (g:Group {id:$gid})
                CREATE (:Student {id:$sid, name:$name})-[:MEMBER_OF]->(g)
                """,
                sid=sid, name=name, gid=gid
            )

        for sch_id, title, dt in schedules:
            session.run(
                "CREATE (:Schedule {id:$id, title:$title, date:date($date)})",
                id=sch_id, title=title, date=dt.isoformat()
            )

        for sid, sch_id in attends:
            session.run(
                """
                MATCH (s:Student {id:$sid}), (sch:Schedule {id:$schid})
                CREATE (s)-[:ATTENDED]->(sch)
                """,
                sid=sid, schid=sch_id
            )

    driver.close()
    print("=== Neo4j: данные загружены. ===")


def generate_for_first_group():
    """
    Генерирует новые курсы, лекции, shedule и attendances
    только для первой группы (group_id = 1).
    """
    print("=== Генерация данных только для первой группы (group_id=1) ===")
    conn = psycopg2.connect(host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD)
    cur  = conn.cursor()

    # 1) Узнаём spec_id у группы 1
    cur.execute("SELECT spec_id FROM groups WHERE group_id = %s", (1,))
    row = cur.fetchone()
    if not row:
        print("Группа 1 не найдена, отмена.")
        cur.close()
        conn.close()
        return
    spec_id = row[0]

    # 2) Создаём новые курсы для этой специальности
    new_courses = []
    n_courses = random.randint(3, 5)
    print(f"Создаём {n_courses} новых курсов для spec_id={spec_id}")
    for i in range(1, n_courses + 1):
        course_title = f"Курс grp1 #{i}"
        cur.execute(
            "INSERT INTO courses (title, spec_id) VALUES (%s, %s) RETURNING course_id",
            (course_title, spec_id)
        )
        new_course_id = cur.fetchone()[0]
        new_courses.append((new_course_id, course_title))
    conn.commit()
    print(f"Новые courses: {[c[0] for c in new_courses]}")

    # 3) Создаём лекции (специальные) для новых курсов
    new_classes = []
    print("Создаём специальные лекции для новых курсов…")
    for course_id, course_title in new_courses:
        count = random.randint(3, 5)
        for j in range(1, count + 1):
            title    = f"Лекция grp1, курс {course_id}, тема {j}"
            req      = "Проектор, ноутбук"
            cls_date = date(2023, 9, 1) + timedelta(days=random.randint(0, 90))
            duration = random.choice([120])
            tag      = 'специальная'
            cur.execute(
                """
                INSERT INTO classes (type, title, requirements, date, duration, tag, course_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING class_id
                """,
                ('Лекция', title, req, cls_date, duration, tag, course_id)
            )
            new_class_id = cur.fetchone()[0]
            new_classes.append((new_class_id, title, cls_date))
    conn.commit()
    print(f"Сгенерировано {len(new_classes)} новых лекций для группы 1.")

    # 4) Вставляем shedule для новых лекций
    new_schedules = []
    print("Генерируем shedule для новых лекций…")
    for class_id, title, cls_date in new_classes:
        cur.execute(
            """
            INSERT INTO shedule (title, start_time, end_time, class_id)
            VALUES (%s, %s, %s, %s)
            RETURNING shedule_id
            """,
            (title, cls_date, cls_date, class_id)
        )
        new_sch = cur.fetchone()[0]
        new_schedules.append(new_sch)
    conn.commit()
    print(f"Сгенерировано {len(new_schedules)} записей в shedule для группы 1.")

    # 5) Генерируем посещения только для студентов группы 1
    print("Генерируем attendances для студентов группы 1…")
    cur.execute("SELECT student_id FROM students WHERE group_id = %s", (1,))
    students = [r[0] for r in cur.fetchall()]

    for sid in students:
        picks = random.sample(new_schedules, k=random.randint(3, min(7, len(new_schedules))))
        for sch_id in picks:
            presence   = random.choice([True, False])
            visit_date = date.today() - timedelta(days=random.randint(0, 30))
            cur.execute(
                """
                INSERT INTO attendances (student_id, shedule_id, presence, date)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (student_id, shedule_id) DO NOTHING
                """,
                (sid, sch_id, presence, visit_date)
            )

    conn.commit()
    cur.close()
    conn.close()
    print("=== Данные для первой группы успешно сгенерированы. ===")


if __name__ == "__main__":
    generate_pg_data()
    generate_more_attendance()
    populate_neo4j_from_pg()
    generate_for_first_group()