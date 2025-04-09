-- Создание схемы для PostgreSQL базы данных "university"

-- 1. Таблица Departments
CREATE TABLE Departments (
    department_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

-- 2. Таблица Specialties
CREATE TABLE Specialties (
    specialty_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    department_id INT REFERENCES Departments(department_id)
);

-- 3. Таблица Groups
CREATE TABLE Groups (
    group_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    specialty_id INT REFERENCES Specialties(specialty_id)
);

-- 4. Таблица Students
CREATE TABLE Students (
    student_id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    group_id INT REFERENCES Groups(group_id)
);

-- 5. Таблица Courses
CREATE TABLE Courses (
    course_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT
);

-- 6. Таблица Lectures
CREATE TABLE Lectures (
    lecture_id SERIAL PRIMARY KEY,
    course_id INT REFERENCES Courses(course_id),
    topic VARCHAR(255) NOT NULL,
    lecture_date DATE,
    duration_hours INT
);

-- 7. Таблица Attendance
CREATE TABLE Attendance (
    attendance_id SERIAL PRIMARY KEY,
    student_id INT REFERENCES Students(student_id),
    lecture_id INT REFERENCES Lectures(lecture_id),
    attended BOOLEAN DEFAULT FALSE
);

-- 8. Таблица Curriculum
CREATE TABLE Curriculum (
    curriculum_id SERIAL PRIMARY KEY,
    group_id INT REFERENCES Groups(group_id),
    course_id INT REFERENCES Courses(course_id),
    year INT,
    semester INT,
    planned_hours INT
);

-- Вставка данных

-- Вставляем кафедру
INSERT INTO Departments (name) VALUES ('Кафедра Информатики');

-- Вставляем специальность
INSERT INTO Specialties (name, department_id) VALUES ('Прикладная информатика', 1);

-- Вставляем группу БСБО-03-22
INSERT INTO Groups (name, specialty_id) VALUES ('БСБО-03-22', 1);

-- Вставляем обязательных студентов для группы БСБО-03-22
INSERT INTO Students (full_name, group_id) VALUES
  ('Мартынова Лия', 1),
  ('Осипов Илья', 1),
  ('Ершов Александр', 1),
  ('Рамазанов Максим', 1);

-- Вставляем курсы
INSERT INTO Courses (title, description) VALUES
  ('Основы программирования', 'Введение в основы программирования и логики.'),
  ('Высшая математика', 'Курс включает анализ, алгебру, геометрию и прочее.');

-- Вставляем учебный план для группы БСБО-03-22 на 2025 год, 1 семестр
INSERT INTO Curriculum (group_id, course_id, year, semester, planned_hours) VALUES
  (1, 1, 2025, 1, 40),
  (1, 2, 2025, 1, 30);

-- Вставляем лекции
INSERT INTO Lectures (course_id, topic, lecture_date, duration_hours) VALUES
  (1, 'Введение. Обзор курса', '2025-02-10', 2),
  (1, 'Основы синтаксиса и семантики', '2025-02-17', 2),
  (2, 'Лекция по теме: Производные', '2025-03-05', 2),
  (2, 'Лекция по теме: Интегралы', '2025-03-12', 2);

-- Вставляем записи посещаемости
INSERT INTO Attendance (student_id, lecture_id, attended) VALUES
  (1, 1, TRUE),
  (2, 1, FALSE),
  (3, 1, TRUE),
  (4, 1, FALSE),
  (1, 2, TRUE),
  (2, 2, TRUE),
  (3, 2, FALSE),
  (4, 2, TRUE),
  (1, 3, FALSE),
  (2, 3, TRUE),
  (3, 3, TRUE),
  (4, 3, FALSE),
  (1, 4, TRUE),
  (2, 4, TRUE),
  (3, 4, TRUE),
  (4, 4, TRUE);
