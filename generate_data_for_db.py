#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import random
from datetime import date, timedelta

import psycopg2
from neo4j import GraphDatabase
from elasticsearch import Elasticsearch, helpers

# ───── параметры окружения ───────────────────────────────────────────────────
POSTGRES_DSN   = os.getenv(
    "POSTGRES_DSN",
    "postgresql://admin:P%40ssw0rd@localhost:5433/university"
)
NEO4J_URI      = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "P@ssw0rd")

ES_HOST        = os.getenv("ES_HOST", "http://localhost:9200")
es             = Elasticsearch(ES_HOST)

random.seed(42)


def generate_materials(conn, new_classes) -> None:
    if not new_classes:
        return
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(material_id), 0) FROM materials")
    next_id = cur.fetchone()[0] + 1

    bulk = []
    keywords = ["введение", "основы", "практика", "теория", "пример", "лабораторная"]

    for class_id, title, _ in new_classes:
        material_id = next_id
        next_id += 1
        content = (
            f"{title}. Это автоматически сгенерированный материал — "
            f"{random.choice(keywords)} {random.choice(keywords)} по теме "
            f"«{title.split(',')[0]}». Содержит примеры, задачи и пояснения."
        )
        cur.execute(
            "INSERT INTO materials (material_id, title, content, class_id) "
            "VALUES (%s, %s, %s, %s)",
            (material_id, title, content, class_id)
        )
        # bulk.append({
        #     "_index": "materials",
        #     "_id":    material_id,
        #     "_source": {
        #         "material_id": material_id,
        #         "class_id":    class_id,
        #         "title":       title,
        #         "content":     content
        #     }
        # })

    # helpers.bulk(es, bulk)
    # es.indices.refresh(index="materials")
    conn.commit()
    print(f"=== ES/PG: добавлено {len(bulk)} материалов ===")


FIRST_NAMES  = ["Алексей", "Иван", "Мария", "Елена", "Дмитрий", "Ольга", "Сергей",
                "Наталья", "Алина", "Глеб", "Кирилл", "Анна"]
LAST_NAMES   = ["Иванов", "Петров", "Сидоров", "Кузнецов", "Смирнов", "Ковалёв",
                "Попов", "Орлов", "Сухоруков", "Селиванов"]
PATRONYMICS  = ["Иванович", "Петрович", "Сергеевич", "Дмитриевич", "Алексеевна",
                "Игоревна", "Сергеевна", "Даниловна"]

def generate_students() -> None:                                 # ← NEW
    """Добавляет к каждой группе 10–15 новых студентов."""
    print("=== Генерация новых студентов для всех групп ===")
    conn = psycopg2.connect(dsn=POSTGRES_DSN)
    cur  = conn.cursor()

    cur.execute("SELECT group_id FROM groups")
    group_ids = [r[0] for r in cur.fetchall()]

    # для проверки уникальности «code»
    cur.execute("SELECT code FROM students")
    existing_codes = {r[0] for r in cur.fetchall()}

    created = 0
    for gid in group_ids:
        for _ in range(random.randint(3, 5)):
            full_name = f"{random.choice(LAST_NAMES)} {random.choice(FIRST_NAMES)} {random.choice(PATRONYMICS)}"
            # гарантируем уникальный code
            while True:
                code = f"S{random.randint(100000, 999999)}"
                if code not in existing_codes:
                    existing_codes.add(code)
                    break
            cur.execute(
                "INSERT INTO students (code, full_name, group_id) VALUES (%s, %s, %s)",
                (code, full_name, gid)
            )
            created += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"=== Добавлено {created} студентов ===")


def generate_pg_data():
    conn = psycopg2.connect(dsn=POSTGRES_DSN)
    cur  = conn.cursor()

    print("=== Генерация занятий в PostgreSQL ===")
    class_types = ['Лекция', 'Семинар', 'Лабораторная']
    tags        = ['специальная', 'общая']

    cur.execute("SELECT COALESCE(MAX(class_id), 0) FROM classes")
    max_class_before = cur.fetchone()[0]

    cur.execute("SELECT course_id FROM courses")
    courses = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT student_id FROM students")
    students = [r[0] for r in cur.fetchall()]

    for course_id in courses:
        for i in range(1, random.randint(20, 30) + 1):
            ctype     = random.choice(class_types)
            title     = f"{ctype} по курсу #{course_id}, тема {i}"
            req       = random.choice([
                "Ноутбук, проектор", "Тетрадь, ручка",
                "Калькулятор, ноутбук", "Учебник, микроскоп"
            ])
            cls_date  = date(2023, 9, 1) + timedelta(days=random.randint(0, 120))
            duration  = 120
            tag       = "специальная" if ctype == "Лабораторная" else random.choice(tags)
            cur.execute(
                """
                INSERT INTO classes
                       (type, title, requirements, date, duration, tag, course_id)
                VALUES (%s,   %s,    %s,           %s,  %s,       %s,  %s)
                """,
                (ctype, title, req, cls_date, duration, tag, course_id)
            )
    conn.commit()

    cur.execute(
        "SELECT class_id, title, date FROM classes WHERE class_id > %s",
        (max_class_before,)
    )
    new_classes = cur.fetchall()
    print(f"Сгенерировано {len(new_classes)} занятий.")

    generate_materials(conn, new_classes)

    print("=== Генерация shedule ===")
    for class_id, title, cls_date in new_classes:
        cur.execute(
            """
            INSERT INTO shedule (title, start_time, end_time, class_id)
            VALUES (%s, %s, %s, %s)
            """,
            (title, cls_date, cls_date, class_id)
        )
    conn.commit()

    print("=== Генерация initial attendances ===")
    cur.execute("SELECT shedule_id FROM shedule")
    all_schedules = [r[0] for r in cur.fetchall()]

    for sid in students:
        base_p = 0.55 + (sid % 5) * 0.07
        picked = random.sample(all_schedules, k=random.randint(5, 20))
        for sch_id in picked:
            presence   = random.random() < base_p
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
    print("=== PostgreSQL: занятия, расписание и базовая посещаемость готовы ===")

def generate_more_attendance():
    conn = psycopg2.connect(dsn=POSTGRES_DSN)
    cur  = conn.cursor()

    print("=== Генерация дополнительных посещений ===")
    cur.execute("SELECT shedule_id FROM shedule")
    schedule_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT student_id FROM students")
    student_ids  = [r[0] for r in cur.fetchall()]

    for sid in student_ids:
        base_p = 0.55 + (sid % 5) * 0.07
        for sch_id in schedule_ids:
            if random.random() >= 0.35:
                continue
            cur.execute(
                "SELECT 1 FROM attendances WHERE student_id=%s AND shedule_id=%s",
                (sid, sch_id)
            )
            if cur.fetchone():
                continue
            presence = random.random() < base_p
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
    print("=== Дополнительные посещения сгенерированы ===")

def boost_attendance_for_keyword(keyword: str, min_pct=0.3, max_pct=0.6):
    """
    Гарантирует, что у лекций, материалы которых содержат <keyword>,
    будет хоть какая-то посещаемость.
    """
    import psycopg2, random
    from elasticsearch import Elasticsearch

    conn = psycopg2.connect(dsn=POSTGRES_DSN)
    cur  = conn.cursor()
    es   = Elasticsearch(ES_HOST)

    # 1. Находим class_id всех материалов с ключевым словом
    resp = es.search(
        index="materials",
        body={"query": {"match": {"content": keyword}}},
        size=10_000,
        _source=["class_id"]
    )
    class_ids = list({int(hit['_source']['class_id']) for hit in resp['hits']['hits']})
    if not class_ids:
        print(f"keyword='{keyword}': материалов нет – пропуск")
        return

    # 2. Берём shedule этих лекций
    cur.execute(
        "SELECT shedule_id, class_id FROM shedule WHERE class_id = ANY(%s)",
        (class_ids,)
    )
    schedules = cur.fetchall()   # [(shedule_id, class_id), ...]

    # 3. Для каждого shedule берём «хозяев»-группы и отмечаем посещение N % студентов
    for shedule_id, class_id in schedules:
        cur.execute("""
            SELECT DISTINCT g.group_id
            FROM classes      c
            JOIN courses      cr  ON cr.course_id = c.course_id
            JOIN specialties  sp  ON sp.spec_id   = cr.spec_id
            JOIN groups       g   ON g.spec_id    = sp.spec_id
            WHERE c.class_id = %s
        """, (class_id,))
        group_ids = [r[0] for r in cur.fetchall()]
        for gid in group_ids:
            # все студенты группы
            cur.execute("SELECT student_id FROM students WHERE group_id = %s", (gid,))
            studs = [r[0] for r in cur.fetchall()]
            k = max(1, int(len(studs) * random.uniform(min_pct, max_pct)))
            add = random.sample(studs, k)
            for sid in add:
                cur.execute("""
                    INSERT INTO attendances (student_id, shedule_id, presence, date)
                    VALUES (%s, %s, TRUE, %s)
                    ON CONFLICT (student_id, shedule_id) DO NOTHING
                """, (sid, shedule_id, date.today()))
    conn.commit()
    cur.close()
    conn.close()
    print(f"=== Boosted attendance for keyword '{keyword}' ({len(schedules)} расписаний) ===")

def populate_neo4j_from_pg():
    print("=== Загрузка данных в Neo4j ===")
    conn = psycopg2.connect(dsn=POSTGRES_DSN)
    cur  = conn.cursor()

    cur.execute("SELECT group_id, name FROM groups")
    groups = cur.fetchall()

    cur.execute("SELECT student_id, full_name, group_id FROM students")
    students = cur.fetchall()

    # ⬇️  добавили course_id, course_title, tag
    cur.execute("""
        SELECT sh.shedule_id,
               sh.title,
               sh.start_time,
               cl.duration,
               g.group_id,
               c.course_id,
               c.title         AS course_title,
               cl.tag
        FROM   shedule      AS sh
        JOIN   classes      AS cl ON cl.class_id = sh.class_id
        JOIN   courses      AS c  ON c.course_id = cl.course_id
        JOIN   specialties  AS sp ON sp.spec_id  = c.spec_id
        JOIN   groups       AS g  ON g.spec_id   = sp.spec_id
    """)
    schedules = cur.fetchall()

    cur.execute("SELECT student_id, shedule_id FROM attendances WHERE presence = TRUE")
    attends = cur.fetchall()
    cur.close()
    conn.close()

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as sess:
        sess.run("MATCH (n) DETACH DELETE n")        # чистим граф

        # ----- группы -----
        for gid, name in groups:
            sess.run("MERGE (g:Group {id:$id}) SET g.code=$code", id=gid, code=name)

        # ----- студенты -----
        for sid, full_name, gid in students:
            sess.run("""
                MATCH (g:Group {id:$gid})
                MERGE (s:Student {id:$sid}) SET s.name=$name
                MERGE (s)-[:BELONGS_TO]->(g)
            """, sid=sid, name=full_name, gid=gid)

        # ----- расписание -----
        for (sid_, title, dt, dur, gid,
             course_id, course_title, tag) in schedules:
            sess.run("""
                MERGE (sch:Schedule {id:$sid})
                ON CREATE SET sch.title=$title,
                              sch.date=date($date),
                              sch.duration=$dur,
                              sch.course_id=$course_id,
                              sch.course_title=$course_title,
                              sch.tag=$tag
                ON MATCH  SET sch.title=$title,
                              sch.date=date($date),
                              sch.duration=$dur,
                              sch.course_id=$course_id,
                              sch.course_title=$course_title,
                              sch.tag=$tag
                WITH sch
                MATCH (g:Group {id:$gid})
                MERGE (g)-[:HAS_SCHEDULE]->(sch)
            """, sid=sid_, title=title, date=dt.isoformat(),
                 dur=dur, gid=gid,
                 course_id=course_id, course_title=course_title, tag=tag)

        # ----- посещаемости -----
        for sid, sch_id in attends:
            sess.run("""
                MATCH (s:Student {id:$sid}),
                      (sch:Schedule {id:$sch_id})
                MERGE (s)-[:ATTENDED]->(sch)
            """, sid=sid, sch_id=sch_id)

    driver.close()
    print("=== Neo4j: граф синхронизирован ===")



def generate_for_first_group():
    print("=== Дополнительные данные для группы 1 ===")
    conn = psycopg2.connect(dsn=POSTGRES_DSN)
    cur  = conn.cursor()

    cur.execute("SELECT spec_id FROM groups WHERE group_id = 1")
    row = cur.fetchone()
    if not row:
        print("Группа 1 не найдена")
        return
    spec_id = row[0]

    new_courses = []
    for i in range(1, random.randint(3, 5) + 1):
        cur.execute(
            "INSERT INTO courses (title, spec_id) VALUES (%s, %s) RETURNING course_id",
            (f"Курс grp1 #{i}", spec_id)
        )
        new_courses.append(cur.fetchone()[0])
    conn.commit()

    new_classes = []
    for course_id in new_courses:
        for j in range(1, random.randint(3, 5) + 1):
            title    = f"Лекция grp1, курс {course_id}, тема {j}"
            cls_date = date(2023, 9, 1) + timedelta(days=random.randint(0, 90))
            cur.execute(
                """
                INSERT INTO classes (type, title, requirements, date, duration, tag, course_id)
                VALUES ('Лекция', %s, 'Проектор, ноутбук', %s, 120, 'специальная', %s)
                RETURNING class_id
                """,
                (title, cls_date, course_id)
            )
            new_classes.append((cur.fetchone()[0], title, cls_date))
    conn.commit()

    generate_materials(conn, new_classes)

    for cid, title, cls_date in new_classes:
        cur.execute(
            "INSERT INTO shedule (title, start_time, end_time, class_id) VALUES (%s, %s, %s, %s)",
            (title, cls_date, cls_date, cid)
        )
    conn.commit()

    class_ids = tuple(c[0] for c in new_classes)

    if not class_ids:
        new_schedules = []
    else:
        cur.execute(
            "SELECT shedule_id FROM shedule WHERE class_id IN %s",
            (class_ids,)  #
        )
        new_schedules = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT student_id FROM students WHERE group_id = 1")
    students = [r[0] for r in cur.fetchall()]

    for sid in students:
        base_p = 0.55 + (sid % 5) * 0.07
        picks = random.sample(new_schedules, k=random.randint(3, min(7, len(new_schedules))))
        for sch_id in picks:
            presence   = random.random() < base_p
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
    print("=== Группа 1: лекции и посещаемость добавлены ===")

# ───── точка входа ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    generate_students()
    generate_pg_data()
    generate_more_attendance()
    generate_for_first_group()
    boost_attendance_for_keyword("введение")

    # populate_neo4j_from_pg()
    print("=== ВСЁ ГОТОВО: данные «показательные», студентов больше ===")