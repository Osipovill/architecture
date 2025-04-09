/* 
  init-mongodb.js
  Инициализация базы данных "university" для MongoDB с коллекцией courses
*/

db = db.getSiblingDB('university');

db.courses.insertMany([
  {
    course_id: 1,
    title: "Основы программирования",
    department: "Кафедра Информатики",
    tech_requirements: "Компьютерный класс с 20 рабочими станциями",
    program: [
      { module: "Введение", topics: ["История вычислительной техники", "Обзор языков программирования"] },
      { module: "Базовые конструкции", topics: ["Переменные", "Условные операторы", "Циклы"] }
    ],
    semester_plan: [
      { week: 1, topic: "Введение. Обзор курса", hours: 2 },
      { week: 2, topic: "Основы синтаксиса", hours: 2 }
    ],
    tags: ["базовый курс", "программирование"]
  },
  {
    course_id: 2,
    title: "Высшая математика",
    department: "Кафедра Информатики",
    tech_requirements: "Аудитория с проекторами, доской и компьютерными средствами",
    program: [
      { module: "Анализ", topics: ["Пределы", "Предел функции"] },
      { module: "Алгебра", topics: ["Матрицы", "Векторы"] }
    ],
    semester_plan: [
      { week: 1, topic: "Лекция по теме: Производные", hours: 2 },
      { week: 2, topic: "Лекция по теме: Интегралы", hours: 2 }
    ],
    tags: ["математика", "университетский курс"]
  }
]);
