// Очистка базы данных от всех узлов и связей
MATCH (n) DETACH DELETE n;

// Создаем узлы групп
CREATE (g1:Group {code: 'БСБО-03-22'}),
       (g2:Group {code: 'БСБО-04-22'}),
       (g3:Group {code: 'БСБО-05-22'});

// Создаем студентов для группы g1 (БСБО-03-22)
CREATE (s1:Student {id: 1, name: 'Мартынова Лия'}),
       (s2:Student {id: 2, name: 'Осипов Илья'}),
       (s3:Student {id: 3, name: 'Ершов Александр'}),
       (s4:Student {id: 4, name: 'Студент 4'}),
       (s5:Student {id: 5, name: 'Студент 5'}),
       (s6:Student {id: 6, name: 'Студент 6'}),
       (s7:Student {id: 7, name: 'Студент 7'}),
       (s8:Student {id: 8, name: 'Студент 8'}),
       (s9:Student {id: 9, name: 'Студент 9'}),
       (s10:Student {id: 10, name: 'Студент 10'});

// Связываем студентов с группой g1
MATCH (g1:Group {code:'БСБО-03-22'})
MATCH (s:Student)
WHERE s.id IN [1,2,3,4,5,6,7,8,9,10]
CREATE (s)-[:BELONGS_TO]->(g1);

// Создаем студентов для группы g2 (БСБО-04-22)
CREATE (s11:Student {id: 11, name: 'Студент 11'}),
       (s12:Student {id: 12, name: 'Студент 12'}),
       (s13:Student {id: 13, name: 'Студент 13'}),
       (s14:Student {id: 14, name: 'Студент 14'}),
       (s15:Student {id: 15, name: 'Студент 15'}),
       (s16:Student {id: 16, name: 'Студент 16'}),
       (s17:Student {id: 17, name: 'Студент 17'}),
       (s18:Student {id: 18, name: 'Студент 18'}),
       (s19:Student {id: 19, name: 'Студент 19'}),
       (s20:Student {id: 20, name: 'Студент 20'});

// Связываем студентов с группой g2
MATCH (g2:Group {code:'БСБО-04-22'})
MATCH (s:Student)
WHERE s.id IN [11,12,13,14,15,16,17,18,19,20]
CREATE (s)-[:BELONGS_TO]->(g2);

// Создаем студентов для группы g3 (БСБО-05-22)
CREATE (s21:Student {id: 21, name: 'Студент 21'}),
       (s22:Student {id: 22, name: 'Студент 22'}),
       (s23:Student {id: 23, name: 'Студент 23'}),
       (s24:Student {id: 24, name: 'Студент 24'}),
       (s25:Student {id: 25, name: 'Студент 25'}),
       (s26:Student {id: 26, name: 'Студент 26'}),
       (s27:Student {id: 27, name: 'Студент 27'}),
       (s28:Student {id: 28, name: 'Студент 28'}),
       (s29:Student {id: 29, name: 'Студент 29'}),
       (s30:Student {id: 30, name: 'Студент 30'});

// Связываем студентов с группой g3
MATCH (g3:Group {code:'БСБО-05-22'})
MATCH (s:Student)
WHERE s.id IN [21,22,23,24,25,26,27,28,29,30]
CREATE (s)-[:BELONGS_TO]->(g3);

// Создаем занятия для группы g1 (БСБО-03-22)
CREATE (c1:Class {id: 1, topic: 'Математика', date: date('2023-09-01'), duration: 90}),
       (c2:Class {id: 2, topic: 'Физика', date: date('2023-09-02'), duration: 90}),
       (c3:Class {id: 3, topic: 'Информатика', date: date('2023-09-03'), duration: 90}),
       (c4:Class {id: 4, topic: 'Алгебра', date: date('2023-09-04'), duration: 90}),
       (c5:Class {id: 5, topic: 'Геометрия', date: date('2023-09-05'), duration: 90}),
       (c6:Class {id: 6, topic: 'Дискретная математика', date: date('2023-09-06'), duration: 90}),
       (c7:Class {id: 7, topic: 'Линейная алгебра', date: date('2023-09-07'), duration: 90}),
       (c8:Class {id: 8, topic: 'Теория вероятностей', date: date('2023-09-08'), duration: 90}),
       (c9:Class {id: 9, topic: 'Статистика', date: date('2023-09-09'), duration: 90}),
       (c10:Class {id: 10, topic: 'Математический анализ', date: date('2023-09-10'), duration: 90});

// Связываем занятия с группой g1
MATCH (g1:Group {code:'БСБО-03-22'})
MATCH (c:Class)
WHERE c.id IN [1,2,3,4,5,6,7,8,9,10]
CREATE (g1)-[:HAS_CLASS]->(c);

// Создаем занятия для группы g2 (БСБО-04-22)
CREATE (c11:Class {id: 11, topic: 'История', date: date('2023-09-11'), duration: 90}),
       (c12:Class {id: 12, topic: 'География', date: date('2023-09-12'), duration: 90}),
       (c13:Class {id: 13, topic: 'Социология', date: date('2023-09-13'), duration: 90}),
       (c14:Class {id: 14, topic: 'Политология', date: date('2023-09-14'), duration: 90}),
       (c15:Class {id: 15, topic: 'Экономика', date: date('2023-09-15'), duration: 90}),
       (c16:Class {id: 16, topic: 'Менеджмент', date: date('2023-09-16'), duration: 90}),
       (c17:Class {id: 17, topic: 'Юриспруденция', date: date('2023-09-17'), duration: 90}),
       (c18:Class {id: 18, topic: 'Правоведение', date: date('2023-09-18'), duration: 90}),
       (c19:Class {id: 19, topic: 'Этика', date: date('2023-09-19'), duration: 90}),
       (c20:Class {id: 20, topic: 'Философия', date: date('2023-09-20'), duration: 90});

// Связываем занятия с группой g2
MATCH (g2:Group {code:'БСБО-04-22'})
MATCH (c:Class)
WHERE c.id IN [11,12,13,14,15,16,17,18,19,20]
CREATE (g2)-[:HAS_CLASS]->(c);

// Создаем занятия для группы g3 (БСБО-05-22)
CREATE (c21:Class {id: 21, topic: 'Химия', date: date('2023-09-21'), duration: 90}),
       (c22:Class {id: 22, topic: 'Биология', date: date('2023-09-22'), duration: 90}),
       (c23:Class {id: 23, topic: 'Геология', date: date('2023-09-23'), duration: 90}),
       (c24:Class {id: 24, topic: 'Экология', date: date('2023-09-24'), duration: 90}),
       (c25:Class {id: 25, topic: 'Астрономия', date: date('2023-09-25'), duration: 90}),
       (c26:Class {id: 26, topic: 'Метеорология', date: date('2023-09-26'), duration: 90}),
       (c27:Class {id: 27, topic: 'Океанология', date: date('2023-09-27'), duration: 90}),
       (c28:Class {id: 28, topic: 'Ботаника', date: date('2023-09-28'), duration: 90}),
       (c29:Class {id: 29, topic: 'Зоология', date: date('2023-09-29'), duration: 90}),
       (c30:Class {id: 30, topic: 'Эволюция', date: date('2023-09-30'), duration: 90});

// Связываем занятия с группой g3
MATCH (g3:Group {code:'БСБО-05-22'})
MATCH (c:Class)
WHERE c.id IN [21,22,23,24,25,26,27,28,29,30]
CREATE (g3)-[:HAS_CLASS]->(c);
