// init-neo4j.cypher
MATCH (n) DETACH DELETE n;

// Инициализация графовой базы данных Neo4j с данными университета

// Создаём кафедру
CREATE (d:Department {name: 'Кафедра Информатики'});

// Создаём специальность и связываем с кафедрой
CREATE (s:Specialty {name: 'Прикладная информатика'})
  -[:BELONGS_TO]->(d);

// Создаём группу БСБО-03-22 и связываем со специальностью
CREATE (g:Group {name: 'БСБО-03-22'})
  -[:PART_OF]->(s);

// Создаём студентов
CREATE (stu1:Student {name: 'Мартынова Лия'});
CREATE (stu2:Student {name: 'Осипов Илья'});
CREATE (stu3:Student {name: 'Ершов Александр'});
CREATE (stu4:Student {name: 'Рамазанов Максим'});

// Связываем студентов с группой
CREATE (stu1)-[:MEMBER_OF]->(g);
CREATE (stu2)-[:MEMBER_OF]->(g);
CREATE (stu3)-[:MEMBER_OF]->(g);
CREATE (stu4)-[:MEMBER_OF]->(g);

// Создаём курсы
CREATE (c1:Course {course_id: 1, title: 'Основы программирования'});
CREATE (c2:Course {course_id: 2, title: 'Высшая математика'});

// Назначаем преподавателя и связываем с курсами
CREATE (inst:Instructor {name: 'Иванов И.И.'});
CREATE (inst)-[:TEACHES]->(c1);
CREATE (inst)-[:TEACHES]->(c2);

// Связываем группу с курсами (учебный план)
CREATE (g)-[:STUDIES {year: 2025, semester:1, planned_hours:40}]->(c1);
CREATE (g)-[:STUDIES {year: 2025, semester:1, planned_hours:30}]->(c2);

// Создаём теги для курсов
CREATE (t1:Tag {name:'программирование'});
CREATE (t2:Tag {name:'математика'});
CREATE (t3:Tag {name:'базовый курс'});
CREATE (t4:Tag {name:'университетский курс'});

CREATE (c1)-[:REQUIRES]->(t1);
CREATE (c1)-[:REQUIRES]->(t3);
CREATE (c2)-[:REQUIRES]->(t2);
CREATE (c2)-[:REQUIRES]->(t4);

// Создаём узлы тем лекций для курсов (семестровой план)
CREATE (lt1:LectureTopic {topic: 'Введение. Обзор курса', hours:2});
CREATE (lt2:LectureTopic {topic: 'Основы синтаксиса', hours:2});
CREATE (lt3:LectureTopic {topic: 'Лекция по теме: Производные', hours:2});
CREATE (lt4:LectureTopic {topic: 'Лекция по теме: Интегралы', hours:2});

CREATE (c1)-[:HAS_TOPIC]->(lt1);
CREATE (c1)-[:HAS_TOPIC]->(lt2);
CREATE (c2)-[:HAS_TOPIC]->(lt3);
CREATE (c2)-[:HAS_TOPIC]->(lt4);
