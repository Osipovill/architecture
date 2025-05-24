#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import random
from datetime import date, timedelta

import psycopg2
from neo4j import GraphDatabase

# === Настройки из окружения ===
POSTGRES_DSN   = os.getenv(
    "POSTGRES_DSN",
    "postgresql://admin:P%40ssw0rd@localhost:5433/university"
)
NEO4J_URI      = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "P@ssw0rd")


def generate_pg_data():
    conn = psycopg2.connect(dsn=POSTGRES_DSN)
    cur  = conn.cursor()

    print("=== Генерация случайных занятий в PostgreSQL ===")
    class_types = ['Лекция', 'Семинар', 'Лабораторная']
    tags        = ['специальная', 'общая']

    # Определяем, с какого class_id начинать
    cur.execute("SELECT COALESCE(MAX(class_id), 0) FROM classes")
    max_class_before = cur.fetchone()[0]

    # Берём все курсы и всех студентов
    cur.execute("SELECT course_id FROM courses")
    courses = [row[0] for row in cur.fetchall()]
    cur.execute("SELECT student_id FROM students")
    students = [row[0] for row in cur.fetchall()]

    # Для каждого курса создаём случайное число занятий
    new_classes = []
    for course_id in courses:
        n = random.randint(8, 15)  # 8–15 занятий на курс
        for i in range(1, n + 1):
            ctype     = random.choice(class_types)
            title     = f"{ctype} по курсу #{course_id}, тема {i}"
            req       = random.choice([
                "Ноутбук, проектор",
                "Тетрадь, ручка",
                "Калькулятор, ноутбук",
                "Учебник, микроскоп"
            ])
            cls_date  = date(2023, 9, 1) + timedelta(days=random.randint(0, 120))
            duration  = random.choice([120])
            tag       = random.choice(tags)

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

    # Получаем ID всех новых classes
    cur.execute(
        "SELECT class_id, title, date FROM classes WHERE class_id > %s",
        (max_class_before,)
    )
    new_classes = cur.fetchall()
    print(f"Сгенерировано {len(new_classes)} занятий (всех типов, всех тегов).")

    # === Расписание (shedule) ===
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

    # === Посещаемость ===
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
    print("=== Данные PostgreSQL: классы, расписание и посещения сгенерированы. ===")


def generate_more_attendance():
    """
    Генерирует дополнительные посещения для уже существующих расписаний,
    чтобы получить неполные показатели посещаемости (не только 0% или 100%).
    """
    conn = psycopg2.connect(dsn=POSTGRES_DSN)
    cur  = conn.cursor()

    print("=== Генерация дополнительных посещений для существующих shedule ===")
    # Берём все shedule и всех студентов
    cur.execute("SELECT shedule_id FROM shedule")
    schedule_ids = [row[0] for row in cur.fetchall()]
    cur.execute("SELECT student_id FROM students")
    student_ids  = [row[0] for row in cur.fetchall()]

    # Для каждого сочетания выбираем с вероятностью 50% запись посещения
    for sid in student_ids:
        for sch_id in schedule_ids:
            # Пропускаем уже существующие записи
            cur.execute(
                "SELECT 1 FROM attendances WHERE student_id=%s AND shedule_id=%s",
                (sid, sch_id)
            )
            if cur.fetchone():
                continue
            # Рандомим посещение: True 70%, False 30%
            presence = random.random() < 0.7
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


def populate_neo4j_from_pg() -> None:
    """
    Полностью пересоздаёт граф Neo4j на основании текущих данных PostgreSQL
    (схема 2025-05), включая все поля и связи:

        Group(id, name)
        └─ Student(id, name) ─[:BELONGS_TO]→ Group
        Schedule(id, title, date, duration)
        Group ─[:HAS_SCHEDULE]→ Schedule
        Student ─[:ATTENDED]→   Schedule
    """
    import psycopg2
    from neo4j import GraphDatabase

    print("=== Загрузка данных в Neo4j ===")

    # ---------- PostgreSQL ----------
    conn = psycopg2.connect(dsn=POSTGRES_DSN)
    cur  = conn.cursor()

    # 1. Группы
    cur.execute("SELECT group_id, name FROM groups")
    groups = cur.fetchall()                         # [(gid, name), ...]

    # 2. Студенты
    cur.execute("""
        SELECT student_id, full_name, group_id
        FROM students
    """)
    students = cur.fetchall()                       # [(sid, full_name, gid), ...]

    # 3. Расписания с привязкой к группам и длительностью
    cur.execute("""
        SELECT sh.shedule_id,
               sh.title,
               sh.start_time,
               cl.duration,
               g.group_id
        FROM   shedule  AS sh
        JOIN   classes  AS cl ON cl.class_id  = sh.class_id
        JOIN   courses  AS c  ON c.course_id  = cl.course_id
        JOIN   specialties AS sp ON sp.spec_id = c.spec_id
        JOIN   groups    AS g  ON g.spec_id   = sp.spec_id
    """)
    # одна строка = конкретное расписание + одна из групп, для которой оно актуально
    schedules = cur.fetchall()                      # [(sch_id, title, date, dur, gid), ...]

    # 4. Посещаемость (только presence = TRUE)
    cur.execute("""
        SELECT student_id, shedule_id
        FROM   attendances
        WHERE  presence = TRUE
    """)
    attends = cur.fetchall()                        # [(sid, sch_id), ...]

    cur.close()
    conn.close()

    # ---------- Neo4j ----------
    driver = GraphDatabase.driver(
        NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
    )

    with driver.session() as session:
        # Полная очистка графа
        session.run("MATCH (n) DETACH DELETE n")

        # --- 1. Группы ---
        for gid, name in groups:
            session.run("""
                MERGE (g:Group {id:$id})
                SET   g.code = $code    // оставляем поле `code`, как в прежних запросах
                """,
                id=gid, code=name
            )

        # --- 2. Студенты и связь BELONGS_TO ---
        for sid, full_name, gid in students:
            session.run("""
                MATCH (g:Group {id:$gid})
                MERGE (s:Student {id:$sid})
                SET   s.name = $name
                MERGE (s)-[:BELONGS_TO]->(g)
                """,
                sid=sid, name=full_name, gid=gid
            )

        # --- 3. Расписания + связь HAS_SCHEDULE ---
        for sch_id, title, dt, dur, gid in schedules:
            session.run("""
                // создаём/обновляем расписание
                MERGE (sch:Schedule {id:$sch_id})
                ON CREATE SET sch.title = $title,
                              sch.date  = date($date),
                              sch.duration = $dur
                ON MATCH  SET sch.title = $title,
                              sch.date  = date($date),
                              sch.duration = $dur

                // привязываем к группе
                WITH sch
                MATCH (g:Group {id:$gid})
                MERGE (g)-[:HAS_SCHEDULE]->(sch)
                """,
                sch_id=sch_id,
                title=title,
                date=dt.isoformat(),
                dur=dur,
                gid=gid
            )

        # --- 4. Посещаемость ---
        for sid, sch_id in attends:
            session.run("""
                MATCH (s:Student  {id:$sid}),
                      (sch:Schedule {id:$sch_id})
                MERGE (s)-[:ATTENDED]->(sch)
                """,
                sid=sid, sch_id=sch_id
            )

    driver.close()
    print("=== Neo4j: данные загружены и соответствует PostgreSQL ===")

def generate_for_first_group():
    """
    Генерирует новые курсы, лекции, shedule и attendances
    только для первой группы (group_id = 1).
    """
    print("=== Генерация данных только для первой группы (group_id=1) ===")
    conn = psycopg2.connect(dsn=POSTGRES_DSN)
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
    generate_for_first_group()
    populate_neo4j_from_pg()
