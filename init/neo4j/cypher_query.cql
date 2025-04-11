MATCH (n) DETACH DELETE n;

// Создаем узлы групп
CREATE (g1:Group {code: 'БСБО-03-22'}),
       (g2:Group {code: 'БСБО-04-22'}),
       (g3:Group {code: 'БСБО-05-22'});

//  Создаем 10 студентов для группы g1 (БСБО-03-22)
// Обратите внимание, что первые три – обязательные студенты
CREATE (s1:Student {id: 1, name: 'Мартынова Лия'})-[:BELONGS_TO]->(g1),
       (s2:Student {id: 2, name: 'Осипов Илья'})-[:BELONGS_TO]->(g1),
       (s3:Student {id: 3, name: 'Ершов Александр'})-[:BELONGS_TO]->(g1),
       (s4:Student {id: 4, name: 'Студент 4'})-[:BELONGS_TO]->(g1),
       (s5:Student {id: 5, name: 'Студент 5'})-[:BELONGS_TO]->(g1),
       (s6:Student {id: 6, name: 'Студент 6'})-[:BELONGS_TO]->(g1),
       (s7:Student {id: 7, name: 'Студент 7'})-[:BELONGS_TO]->(g1),
       (s8:Student {id: 8, name: 'Студент 8'})-[:BELONGS_TO]->(g1),
       (s9:Student {id: 9, name: 'Студент 9'})-[:BELONGS_TO]->(g1),
       (s10:Student {id: 10, name: 'Студент 10'})-[:BELONGS_TO]->(g1);

// Создаем 10 студентов для группы g2 (БСБО-04-22)
CREATE (s11:Student {id: 11, name: 'Студент 11'})-[:BELONGS_TO]->(g2),
       (s12:Student {id: 12, name: 'Студент 12'})-[:BELONGS_TO]->(g2),
       (s13:Student {id: 13, name: 'Студент 13'})-[:BELONGS_TO]->(g2),
       (s14:Student {id: 14, name: 'Студент 14'})-[:BELONGS_TO]->(g2),
       (s15:Student {id: 15, name: 'Студент 15'})-[:BELONGS_TO]->(g2),
       (s16:Student {id: 16, name: 'Студент 16'})-[:BELONGS_TO]->(g2),
       (s17:Student {id: 17, name: 'Студент 17'})-[:BELONGS_TO]->(g2),
       (s18:Student {id: 18, name: 'Студент 18'})-[:BELONGS_TO]->(g2),
       (s19:Student {id: 19, name: 'Студент 19'})-[:BELONGS_TO]->(g2),
       (s20:Student {id: 20, name: 'Студент 20'})-[:BELONGS_TO]->(g2);

// Создаем 10 студентов для группы g3 (БСБО-05-22)
CREATE (s21:Student {id: 21, name: 'Студент 21'})-[:BELONGS_TO]->(g3),
       (s22:Student {id: 22, name: 'Студент 22'})-[:BELONGS_TO]->(g3),
       (s23:Student {id: 23, name: 'Студент 23'})-[:BELONGS_TO]->(g3),
       (s24:Student {id: 24, name: 'Студент 24'})-[:BELONGS_TO]->(g3),
       (s25:Student {id: 25, name: 'Студент 25'})-[:BELONGS_TO]->(g3),
       (s26:Student {id: 26, name: 'Студент 26'})-[:BELONGS_TO]->(g3),
       (s27:Student {id: 27, name: 'Студент 27'})-[:BELONGS_TO]->(g3),
       (s28:Student {id: 28, name: 'Студент 28'})-[:BELONGS_TO]->(g3),
       (s29:Student {id: 29, name: 'Студент 29'})-[:BELONGS_TO]->(g3),
       (s30:Student {id: 30, name: 'Студент 30'})-[:BELONGS_TO]->(g3);

--------------------------------------------------
 // Создаем 10 занятий для группы g1
CREATE (c1:Class {id: 1, topic: 'Математика', date: date('2023-09-01'), duration: 90})<-[:HAS_CLASS]-(g1),
       (c2:Class {id: 2, topic: 'Физика', date: date('2023-09-02'), duration: 90})<-[:HAS_CLASS]-(g1),
       (c3:Class {id: 3, topic: 'Информатика', date: date('2023-09-03'), duration: 90})<-[:HAS_CLASS]-(g1),
       (c4:Class {id: 4, topic: 'Алгебра', date: date('2023-09-04'), duration: 90})<-[:HAS_CLASS]-(g1),
       (c5:Class {id: 5, topic: 'Геометрия', date: date('2023-09-05'), duration: 90})<-[:HAS_CLASS]-(g1),
       (c6:Class {id: 6, topic: 'Дискретная математика', date: date('2023-09-06'), duration: 90})<-[:HAS_CLASS]-(g1),
       (c7:Class {id: 7, topic: 'Линейная алгебра', date: date('2023-09-07'), duration: 90})<-[:HAS_CLASS]-(g1),
       (c8:Class {id: 8, topic: 'Теория вероятностей', date: date('2023-09-08'), duration: 90})<-[:HAS_CLASS]-(g1),
       (c9:Class {id: 9, topic: 'Статистика', date: date('2023-09-09'), duration: 90})<-[:HAS_CLASS]-(g1),
       (c10:Class {id: 10, topic: 'Математический анализ', date: date('2023-09-10'), duration: 90})<-[:HAS_CLASS]-(g1);

 // Создаем 10 занятий для группы g2
CREATE (c11:Class {id: 11, topic: 'История', date: date('2023-09-11'), duration: 90})<-[:HAS_CLASS]-(g2),
       (c12:Class {id: 12, topic: 'География', date: date('2023-09-12'), duration: 90})<-[:HAS_CLASS]-(g2),
       (c13:Class {id: 13, topic: 'Социология', date: date('2023-09-13'), duration: 90})<-[:HAS_CLASS]-(g2),
       (c14:Class {id: 14, topic: 'Политология', date: date('2023-09-14'), duration: 90})<-[:HAS_CLASS]-(g2),
       (c15:Class {id: 15, topic: 'Экономика', date: date('2023-09-15'), duration: 90})<-[:HAS_CLASS]-(g2),
       (c16:Class {id: 16, topic: 'Менеджмент', date: date('2023-09-16'), duration: 90})<-[:HAS_CLASS]-(g2),
       (c17:Class {id: 17, topic: 'Юриспруденция', date: date('2023-09-17'), duration: 90})<-[:HAS_CLASS]-(g2),
       (c18:Class {id: 18, topic: 'Правоведение', date: date('2023-09-18'), duration: 90})<-[:HAS_CLASS]-(g2),
       (c19:Class {id: 19, topic: 'Этика', date: date('2023-09-19'), duration: 90})<-[:HAS_CLASS]-(g2),
       (c20:Class {id: 20, topic: 'Философия', date: date('2023-09-20'), duration: 90})<-[:HAS_CLASS]-(g2);

 // Создаем 10 занятий для группы g3
CREATE (c21:Class {id: 21, topic: 'Химия', date: date('2023-09-21'), duration: 90})<-[:HAS_CLASS]-(g3),
       (c22:Class {id: 22, topic: 'Биология', date: date('2023-09-22'), duration: 90})<-[:HAS_CLASS]-(g3),
       (c23:Class {id: 23, topic: 'Геология', date: date('2023-09-23'), duration: 90})<-[:HAS_CLASS]-(g3),
       (c24:Class {id: 24, topic: 'Экология', date: date('2023-09-24'), duration: 90})<-[:HAS_CLASS]-(g3),
       (c25:Class {id: 25, topic: 'Астрономия', date: date('2023-09-25'), duration: 90})<-[:HAS_CLASS]-(g3),
       (c26:Class {id: 26, topic: 'Метеорология', date: date('2023-09-26'), duration: 90})<-[:HAS_CLASS]-(g3),
       (c27:Class {id: 27, topic: 'Океанология', date: date('2023-09-27'), duration: 90})<-[:HAS_CLASS]-(g3),
       (c28:Class {id: 28, topic: 'Ботаника', date: date('2023-09-28'), duration: 90})<-[:HAS_CLASS]-(g3),
       (c29:Class {id: 29, topic: 'Зоология', date: date('2023-09-29'), duration: 90})<-[:HAS_CLASS]-(g3),
       (c30:Class {id: 30, topic: 'Эволюция', date: date('2023-09-30'), duration: 90})<-[:HAS_CLASS]-(g3);

