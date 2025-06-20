-- Удаляем существующую схему (для чистоты) и создаем новую
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

-- Создаем таблицы

-- Университеты
CREATE TABLE universities (
  university_id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL
);

-- Институты
CREATE TABLE institutes (
  institute_id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  university_id INT REFERENCES universities(university_id)
);

-- Кафедры (departments) – добавляем внешний ключ institute_id
CREATE TABLE departments (
  dept_id SERIAL PRIMARY KEY,
  name TEXT,
  head TEXT,
  phone TEXT,
  institute_id INT REFERENCES institutes(institute_id)
);

-- Специальности
CREATE TABLE specialties (
  spec_id SERIAL PRIMARY KEY,
  name TEXT,
  code VARCHAR(10),
  dept_id INT REFERENCES departments(dept_id)
);

-- Курсы
CREATE TABLE courses (
  course_id SERIAL PRIMARY KEY,
  title TEXT,
  spec_id INT REFERENCES specialties(spec_id)
);

-- Группы
CREATE TABLE groups (
  group_id SERIAL PRIMARY KEY,
  name TEXT,
  year INT,
  spec_id INT REFERENCES specialties(spec_id)
);

-- Студенты
CREATE TABLE students (
  student_id SERIAL PRIMARY KEY,
  full_name TEXT,
  code VARCHAR(20),
  group_id INT REFERENCES groups(group_id)
);

-- Занятия
CREATE TABLE classes (
  class_id SERIAL PRIMARY KEY,
  type TEXT,
  title TEXT,
  requirements TEXT,
  date DATE,
  duration INT,
  tag TEXT,
  course_id INT REFERENCES courses(course_id)
);

-- Материалы (для последующей индексации в ElasticSearch)
CREATE TABLE materials (
  material_id SERIAL PRIMARY KEY,
  title TEXT,
  content TEXT,
  class_id INT REFERENCES classes(class_id)
);

CREATE TABLE shedule (
  shedule_id SERIAL PRIMARY KEY,
  title TEXT,
  start_time DATE,
  end_time DATE,
  class_id INT REFERENCES classes(class_id)
);

-- Посещаемость
CREATE TABLE attendances (
  student_id INT REFERENCES students(student_id),
  shedule_id INT REFERENCES shedule(shedule_id),
  presence BOOLEAN,
  date DATE,
  PRIMARY KEY (student_id, shedule_id)
);

CREATE OR REPLACE VIEW shedule_full AS
SELECT
  sh.shedule_id,
  sh.title,
  sh.start_time,
  cl.duration,
  g.group_id,
  c.course_id,
  c.title      AS course_title,
  cl.tag
FROM shedule AS sh
JOIN classes     AS cl  ON cl.class_id   = sh.class_id
JOIN courses     AS c   ON c.course_id   = cl.course_id
JOIN specialties AS sp  ON sp.spec_id    = c.spec_id
JOIN groups      AS g   ON g.spec_id     = sp.spec_id;


-- Заполнение данными

-- 10 университетов
INSERT INTO universities (name) VALUES
('Университет A'),
('Университет B'),
('Университет C'),
('Университет D'),
('Университет E'),
('Университет F'),
('Университет G'),
('Университет H'),
('Университет I'),
('Университет J');

-- 10 институтов
INSERT INTO institutes (name, university_id) VALUES
('Институт информационных технологий', 1),
('Институт экономики', 1),
('Институт права', 2),
('Институт управления', 2),
('Институт математики', 3),
('Институт физики', 3),
('Институт химии', 4),
('Институт биологии', 4),
('Институт лингвистики', 5),
('Институт социологии', 5);

-- 10 кафедр
INSERT INTO departments (name, head, phone, institute_id) VALUES
('Кафедра программирования', 'Иванов И.И.', '+7-111-111-1111', 1),
('Кафедра информационных систем', 'Петров П.П.', '+7-111-111-1112', 1),
('Кафедра менеджмента', 'Сидоров С.С.', '+7-111-111-1113', 2),
('Кафедра финансов', 'Кузнецов К.К.', '+7-111-111-1114', 2),
('Кафедра теоретической математики', 'Андреев А.А.', '+7-111-111-1115', 3),
('Кафедра прикладной математики', 'Борисов Б.Б.', '+7-111-111-1116', 3),
('Кафедра общей физики', 'Васильев В.В.', '+7-111-111-1117', 4),
('Кафедра экспериментальной физики', 'Григорьев Г.Г.', '+7-111-111-1118', 4),
('Кафедра химии', 'Дмитриев Д.Д.', '+7-111-111-1119', 5),
('Кафедра биологии', 'Егоров Е.Е.', '+7-111-111-1120', 5);

-- 10 специальностей
INSERT INTO specialties (name, code, dept_id) VALUES
('Компьютерные науки', '09.03.01', 1),
('Программная инженерия', '09.03.02', 2),
('Экономика', '38.05.01', 3),
('Менеджмент', '38.05.02', 4),
('Прикладная математика', '01.02.01', 5),
('Чистая математика', '01.02.02', 6),
('Фундаментальная физика', '04.05.01', 7),
('Прикладная физика', '04.05.02', 8),
('Химическая технология', '10.03.01', 9),
('Биоинженерия', '10.03.02', 10);

-- 10 курсов (привязка к spec_id той же порядковости)
INSERT INTO courses (title, spec_id) VALUES
('Введение в программирование', 1),
('ООП', 2),
('Базы данных', 3),
('Экономическая теория', 4),
('Менеджмент проектов', 5),
('Дискретная математика', 6),
('Физика для инженеров', 7),
('Органическая химия', 8),
('Биология клетки', 9),
('Статистика', 10);

-- 10 групп
INSERT INTO groups (name, year, spec_id) VALUES
('БСБО-03-22', 2022, 1),
('БСБО-04-22', 2022, 2),
('БСБО-05-22', 2022, 3),
('БСБО-06-22', 2022, 4),
('БСБО-07-22', 2022, 5),
('БСБО-08-22', 2022, 6),
('БСБО-09-22', 2022, 7),
('БСБО-10-22', 2022, 8),
('БСБО-11-22', 2022, 9),
('БСБО-12-22', 2022, 10);

-- 10 студентов
INSERT INTO students (full_name, code, group_id) VALUES
('Мартынова Лия', 'Ст-2022-001', 1),
('Осипов Илья', 'Ст-2022-002', 1),
('Ершов Александр', 'Ст-2022-003', 1),
('Иванов Сергей', 'Ст-2022-004', 2),
('Петрова Анна', 'Ст-2022-005', 2),
('Сидоров Максим', 'Ст-2022-006', 3),
('Кузнецова Ольга', 'Ст-2022-007', 3),
('Новиков Роман', 'Ст-2022-008', 4),
('Фролова Светлана', 'Ст-2022-009', 5),
('Смирнова Елена', 'Ст-2022-010', 6);

-- 10 занятий
-- 10 занятий с указанием требований по техническим средствам
INSERT INTO classes (type, title, requirements, date, duration, tag, course_id) VALUES
  ('Лекция',       'Введение в программирование',               'Установленный Python (3.8+)',              '2023-09-01',  120, 'специальная', 1),
  ('Семинар',      'ООП – практика',                           'Установленный Python (3.8+)',                 '2023-09-05', 120, 'специальная', 2),
  ('Лекция',       'Основы баз данных',                        'SQL-клиент (psql, DBeaver) и доступ к PostgreSQL',                      '2023-09-10',  120, 'специальная', 3),
  ('Лабораторная', 'Экономическая теория – задачи',            'Калькулятор (реальный или в приложении), ноутбук для выгрузки отчётов', '2023-09-15', 120, 'общая', 4),
  ('Лекция',       'Введение в менеджмент',                    'Проектор и презентация в PowerPoint, ноутбук для конспектирования',      '2023-09-20',  120, 'общая', 5),
  ('Семинар',      'Практика по дискретной математике',        'Тетрадь, ручка и калькулятор; для демонстрации – экран с интерактивной доской', '2023-09-25', 120, 'специальная', 6),
  ('Лекция',       'Основы физики',                             'Учебник по физике, калькулятор; доступ к виртуальному лабораторному стенду',      '2023-10-01',  120, 'общая', 7),
  ('Лекция',       'Органическая химия – введение',             'Лаборантский халат, защитные очки, перчатки; рабочая станция с ChemSketch',      '2023-10-05',  120, 'общая', 8),
  ('Семинар',      'Биология клетки – структура',               'Микроскоп или виртуальный эмулятор микроскопа, ноутбук',                '2023-10-10', 120, 'общая', 9),
  ('Лекция',       'Статистика: основы',                         'Ноутбук с установленным R и RStudio или Excel; доступ к набору тестовых данных', '2023-10-15',  120, 'специальная', 10);

-- 10 материалов
INSERT INTO materials (title, content, class_id) VALUES
('Слайды лекции 1', 'Материалы к введению в программирование', 1),
('Конспект семинара 2', 'Практические примеры по ООП', 2),
('Методические указания 3', 'Введение в БД и SQL', 3),
('Лабораторная работа 4', 'Задачи по экономической теории', 4),
('Презентация 5', 'Основы менеджмента проектов', 5),
('Конспект семинара 6', 'Решение задач по дискретной математике', 6),
('Слайды лекции 7', 'Физика для инженеров: основы', 7),
('Презентация 8', 'Органическая химия: вступление', 8),
('Методические указания 9', 'Ключевые понятия биологии клетки', 9),
('Лабораторная работа 10', 'Практическое задание по статистике', 10);

-- 10 расписаний (shedule)
INSERT INTO shedule (title, start_time, end_time, class_id) VALUES
('Введение в программирование', '2023-09-01', '2023-09-01', 1),
('ООП – практика',               '2023-09-05', '2023-09-05', 2),
('Основы баз данных',            '2023-09-10', '2023-09-10', 3),
('Экономическая теория – задачи','2023-09-15', '2023-09-15', 4),
('Введение в менеджмент',       '2023-09-20', '2023-09-20', 5),
('Практика по дискретной математике','2023-09-25','2023-09-25', 6),
('Основы физики',                '2023-10-01', '2023-10-01', 7),
('Органическая химия – введение','2023-10-05', '2023-10-05', 8),
('Биология клетки – структура',  '2023-10-10', '2023-10-10', 9),
('Статистика: основы',           '2023-10-15', '2023-10-15', 10);

-- 10 посещаемостей
INSERT INTO attendances (student_id, shedule_id, presence, date) VALUES
(1, 1, TRUE, '2023-09-01'),
(2, 1, TRUE, '2023-09-01'),
(3, 1, FALSE,'2023-09-01'),
(1, 2, TRUE, '2023-09-05'),
(4, 2, FALSE,'2023-09-05'),
(5, 3, TRUE, '2023-09-10'),
(6, 3, TRUE, '2023-09-10'),
(7, 4, FALSE,'2023-09-15'),
(8, 5, TRUE, '2023-09-20'),
(9, 6, TRUE, '2023-09-25');

DROP TABLE IF EXISTS students_full CASCADE;

CREATE TABLE students_full (
    student_id INT PRIMARY KEY,
    code VARCHAR(20),
    full_name TEXT,
    group_name TEXT,
    specialty TEXT,
    dept_id INT
);

INSERT INTO public.students_full (student_id, code, full_name, group_name, specialty, dept_id)
SELECT
    s.student_id,
    s.code,
    s.full_name,
    g.name,
    sp.name,
    sp.dept_id
FROM students s
JOIN groups g ON s.group_id = g.group_id
JOIN specialties sp ON g.spec_id = sp.spec_id;

-- INSERT/UPDATE
CREATE OR REPLACE FUNCTION sync_students_full_from_students()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT' OR TG_OP = 'UPDATE') THEN
        -- Сначала удаляем старое, если есть
        DELETE FROM students_full WHERE student_id = NEW.student_id;
        -- Вставляем новое
        INSERT INTO students_full (student_id, code, full_name, group_name, specialty, dept_id)
        SELECT
            NEW.student_id,
            NEW.code,
            NEW.full_name,
            g.name,
            sp.name,
            sp.dept_id
        FROM groups g
        JOIN specialties sp ON g.spec_id = sp.spec_id
        WHERE g.group_id = NEW.group_id;
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        DELETE FROM students_full WHERE student_id = OLD.student_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_students_full_from_students ON students;
CREATE TRIGGER trg_students_full_from_students
AFTER INSERT OR UPDATE OR DELETE ON students
FOR EACH ROW
EXECUTE FUNCTION sync_students_full_from_students();

CREATE OR REPLACE FUNCTION sync_students_full_from_groups()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'UPDATE') THEN
        -- Обновляем group_name, specialty и dept_id во всех students_full, связанных с этой группой
        UPDATE students_full sf
        SET
            group_name = NEW.name,
            specialty = sp.name,
            dept_id = sp.dept_id
        FROM students s
        JOIN specialties sp ON NEW.spec_id = sp.spec_id
        WHERE sf.student_id = s.student_id
          AND s.group_id = NEW.group_id;
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        -- Удаляем всех студентов этой группы из students_full
        DELETE FROM students_full sf
        USING students s
        WHERE sf.student_id = s.student_id
          AND s.group_id = OLD.group_id;
        RETURN OLD;
    ELSIF (TG_OP = 'INSERT') THEN
        -- Нет прямого действия — ведь нет студентов у новой группы
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_students_full_from_groups ON groups;
CREATE TRIGGER trg_students_full_from_groups
AFTER INSERT OR UPDATE OR DELETE ON groups
FOR EACH ROW
EXECUTE FUNCTION sync_students_full_from_groups();

CREATE OR REPLACE FUNCTION sync_students_full_from_specialties()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'UPDATE') THEN
        -- Обновляем specialty и dept_id у всех студентов этой специальности
        UPDATE students_full sf
        SET
            specialty = NEW.name,
            dept_id = NEW.dept_id
        FROM students s
        JOIN groups g ON s.group_id = g.group_id
        WHERE sf.student_id = s.student_id
          AND g.spec_id = NEW.spec_id;
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        -- Удаляем всех студентов, связанных с этой specialty
        DELETE FROM students_full sf
        USING students s
        JOIN groups g ON s.group_id = g.group_id
        WHERE sf.student_id = s.student_id
          AND g.spec_id = OLD.spec_id;
        RETURN OLD;
    ELSIF (TG_OP = 'INSERT') THEN
        -- Нет прямого действия
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_students_full_from_specialties ON specialties;
CREATE TRIGGER trg_students_full_from_specialties
AFTER INSERT OR UPDATE OR DELETE ON specialties
FOR EACH ROW
EXECUTE FUNCTION sync_students_full_from_specialties();

-- Создание materialized-аналога shedule_full
DROP TABLE IF EXISTS shedule_full_materialized;
CREATE TABLE shedule_full_materialized (
    shedule_id INT PRIMARY KEY,
    title TEXT,
    start_time DATE,
    duration INT,
    group_id INT,
    course_id INT,
    course_title TEXT,
    tag TEXT
);

-- Инициализация данными
INSERT INTO shedule_full_materialized
SELECT
    sh.shedule_id,
    sh.title,
    sh.start_time,
    cl.duration,
    g.group_id,
    c.course_id,
    c.title,
    cl.tag
FROM shedule AS sh
JOIN classes cl ON cl.class_id = sh.class_id
JOIN courses c ON c.course_id = cl.course_id
JOIN specialties sp ON sp.spec_id = c.spec_id
JOIN groups g ON g.spec_id = sp.spec_id;

-- Функция и триггер для shedule
CREATE OR REPLACE FUNCTION sync_shedule_full_from_shedule()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM shedule_full_materialized WHERE shedule_id = NEW.shedule_id;
    INSERT INTO shedule_full_materialized
    SELECT
        sh.shedule_id,
        sh.title,
        sh.start_time,
        cl.duration,
        g.group_id,
        c.course_id,
        c.title,
        cl.tag
    FROM shedule sh
    JOIN classes cl ON cl.class_id = sh.class_id
    JOIN courses c ON c.course_id = cl.course_id
    JOIN specialties sp ON sp.spec_id = c.spec_id
    JOIN groups g ON g.spec_id = sp.spec_id
    WHERE sh.shedule_id = NEW.shedule_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_shedule_full_from_shedule ON shedule;
CREATE TRIGGER trg_shedule_full_from_shedule
AFTER INSERT OR UPDATE ON shedule
FOR EACH ROW
EXECUTE FUNCTION sync_shedule_full_from_shedule();

-- Аналогичные функции для classes, courses, specialties, groups

CREATE OR REPLACE FUNCTION sync_shedule_full_on_class_change()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM shedule_full_materialized
    USING shedule sh
    WHERE sh.class_id = NEW.class_id AND shedule_full_materialized.shedule_id = sh.shedule_id;

    INSERT INTO shedule_full_materialized
    SELECT
        sh.shedule_id,
        sh.title,
        sh.start_time,
        cl.duration,
        g.group_id,
        c.course_id,
        c.title,
        cl.tag
    FROM shedule sh
    JOIN classes cl ON cl.class_id = sh.class_id
    JOIN courses c ON c.course_id = cl.course_id
    JOIN specialties sp ON sp.spec_id = c.spec_id
    JOIN groups g ON g.spec_id = sp.spec_id
    WHERE sh.class_id = NEW.class_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_shedule_full_on_class_change ON classes;
CREATE TRIGGER trg_shedule_full_on_class_change
AFTER UPDATE ON classes
FOR EACH ROW
EXECUTE FUNCTION sync_shedule_full_on_class_change();

CREATE OR REPLACE FUNCTION sync_shedule_full_on_course_change()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM shedule_full_materialized
    USING shedule sh, classes cl
    WHERE cl.course_id = NEW.course_id AND cl.class_id = sh.class_id AND shedule_full_materialized.shedule_id = sh.shedule_id;

    INSERT INTO shedule_full_materialized
    SELECT
        sh.shedule_id,
        sh.title,
        sh.start_time,
        cl.duration,
        g.group_id,
        c.course_id,
        c.title,
        cl.tag
    FROM shedule sh
    JOIN classes cl ON cl.class_id = sh.class_id
    JOIN courses c ON c.course_id = cl.course_id
    JOIN specialties sp ON sp.spec_id = c.spec_id
    JOIN groups g ON g.spec_id = sp.spec_id
    WHERE c.course_id = NEW.course_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_shedule_full_on_course_change ON courses;
CREATE TRIGGER trg_shedule_full_on_course_change
AFTER UPDATE ON courses
FOR EACH ROW
EXECUTE FUNCTION sync_shedule_full_on_course_change();

CREATE OR REPLACE FUNCTION sync_shedule_full_on_specialty_change()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM shedule_full_materialized
    USING shedule sh, classes cl, courses c
    WHERE c.spec_id = NEW.spec_id AND c.course_id = cl.course_id AND cl.class_id = sh.class_id AND shedule_full_materialized.shedule_id = sh.shedule_id;

    INSERT INTO shedule_full_materialized
    SELECT
        sh.shedule_id,
        sh.title,
        sh.start_time,
        cl.duration,
        g.group_id,
        c.course_id,
        c.title,
        cl.tag
    FROM shedule sh
    JOIN classes cl ON cl.class_id = sh.class_id
    JOIN courses c ON c.course_id = cl.course_id
    JOIN specialties sp ON sp.spec_id = c.spec_id
    JOIN groups g ON g.spec_id = sp.spec_id
    WHERE sp.spec_id = NEW.spec_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_shedule_full_on_specialty_change ON specialties;
CREATE TRIGGER trg_shedule_full_on_specialty_change
AFTER UPDATE ON specialties
FOR EACH ROW
EXECUTE FUNCTION sync_shedule_full_on_specialty_change();

CREATE OR REPLACE FUNCTION sync_shedule_full_on_group_change()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM shedule_full_materialized
    USING
        shedule sh,
        classes cl,
        courses c,
        specialties sp,
        groups g
    WHERE
        sh.class_id    = cl.class_id
        AND cl.course_id    = c.course_id
        AND c.spec_id       = sp.spec_id
        AND g.spec_id       = sp.spec_id
        AND shedule_full_materialized.shedule_id = sh.shedule_id
        AND g.group_id      = NEW.group_id;

    INSERT INTO shedule_full_materialized
    SELECT
        sh.shedule_id,
        sh.title,
        sh.start_time,
        cl.duration,
        g.group_id,
        c.course_id,
        c.title,
        cl.tag
    FROM shedule sh
    JOIN classes cl ON cl.class_id = sh.class_id
    JOIN courses c ON c.course_id = cl.course_id
    JOIN specialties sp ON sp.spec_id = c.spec_id
    JOIN groups g ON g.spec_id = sp.spec_id
    WHERE g.group_id = NEW.group_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_shedule_full_on_group_change ON groups;
CREATE TRIGGER trg_shedule_full_on_group_change
AFTER UPDATE ON groups
FOR EACH ROW
EXECUTE FUNCTION sync_shedule_full_on_group_change();


CREATE PUBLICATION pub FOR ALL TABLES;
