// 1) Полная очистка графа
MATCH (n) DETACH DELETE n;

// 2) Создаём группы
CREATE (g1:Group {code: 'БСБО-03-22'}),
       (g2:Group {code: 'БСБО-04-22'}),
       (g3:Group {code: 'БСБО-05-22'}),
       (g4:Group {code: 'БСБО-06-22'}),
       (g5:Group {code: 'БСБО-07-22'}),
       (g6:Group {code: 'БСБО-08-22'}),
       (g7:Group {code: 'БСБО-09-22'}),
       (g8:Group {code: 'БСБО-10-22'}),
       (g9:Group {code: 'БСБО-11-22'}),
       (g10:Group {code: 'БСБО-12-22'});

// 3) Создаём студентов и связываем с группами точно как в PostgreSQL
MATCH (g:Group {code: 'БСБО-03-22'})
CREATE (s1:Student {id: 1, name: 'Мартынова Лия'})-[:BELONGS_TO]->(g),
       (s2:Student {id: 2, name: 'Осипов Илья'})-[:BELONGS_TO]->(g),
       (s3:Student {id: 3, name: 'Ершов Александр'})-[:BELONGS_TO]->(g);

MATCH (g:Group {code: 'БСБО-04-22'})
CREATE (s4:Student {id: 4, name: 'Иванов Сергей'})-[:BELONGS_TO]->(g),
       (s5:Student {id: 5, name: 'Петрова Анна'})-[:BELONGS_TO]->(g);

MATCH (g:Group {code: 'БСБО-05-22'})
CREATE (s6:Student {id: 6, name: 'Сидоров Максим'})-[:BELONGS_TO]->(g),
       (s7:Student {id: 7, name: 'Кузнецова Ольга'})-[:BELONGS_TO]->(g);

MATCH (g:Group {code: 'БСБО-06-22'})
CREATE (s8:Student {id: 8, name: 'Новиков Роман'})-[:BELONGS_TO]->(g);

MATCH (g:Group {code: 'БСБО-07-22'})
CREATE (s9:Student {id: 9, name: 'Фролова Светлана'})-[:BELONGS_TO]->(g);

MATCH (g:Group {code: 'БСБО-08-22'})
CREATE (s10:Student {id: 10, name: 'Смирнова Елена'})-[:BELONGS_TO]->(g);

// 4) Создаём расписание точно как в PostgreSQL
MATCH (g:Group {code: 'БСБО-03-22'})
CREATE (sch1:Schedule {
    title: 'Введение в программирование',
    date: date('2023-09-01'),
    duration: 90
}),
(g)-[:HAS_SCHEDULE]->(sch1);

MATCH (g:Group {code: 'БСБО-04-22'})
CREATE (sch2:Schedule {
    title: 'ООП – практика',
    date: date('2023-09-05'),
    duration: 120
}),
(g)-[:HAS_SCHEDULE]->(sch2);

MATCH (g:Group {code: 'БСБО-05-22'})
CREATE (sch3:Schedule {
    title: 'Основы баз данных',
    date: date('2023-09-10'),
    duration: 90
}),
(g)-[:HAS_SCHEDULE]->(sch3);

MATCH (g:Group {code: 'БСБО-06-22'})
CREATE (sch4:Schedule {
    title: 'Экономическая теория – задачи',
    date: date('2023-09-15'),
    duration: 120
}),
(g)-[:HAS_SCHEDULE]->(sch4);

MATCH (g:Group {code: 'БСБО-07-22'})
CREATE (sch5:Schedule {
    title: 'Введение в менеджмент',
    date: date('2023-09-20'),
    duration: 90
}),
(g)-[:HAS_SCHEDULE]->(sch5);

MATCH (g:Group {code: 'БСБО-08-22'})
CREATE (sch6:Schedule {
    title: 'Практика по дискретной математике',
    date: date('2023-09-25'),
    duration: 120
}),
(g)-[:HAS_SCHEDULE]->(sch6);

MATCH (g:Group {code: 'БСБО-09-22'})
CREATE (sch7:Schedule {
    title: 'Основы физики',
    date: date('2023-10-01'),
    duration: 90
}),
(g)-[:HAS_SCHEDULE]->(sch7);

MATCH (g:Group {code: 'БСБО-10-22'})
CREATE (sch8:Schedule {
    title: 'Органическая химия – введение',
    date: date('2023-10-05'),
    duration: 90
}),
(g)-[:HAS_SCHEDULE]->(sch8);

MATCH (g:Group {code: 'БСБО-11-22'})
CREATE (sch9:Schedule {
    title: 'Биология клетки – структура',
    date: date('2023-10-10'),
    duration: 120
}),
(g)-[:HAS_SCHEDULE]->(sch9);

MATCH (g:Group {code: 'БСБО-12-22'})
CREATE (sch10:Schedule {
    title: 'Статистика: основы',
    date: date('2023-10-15'),
    duration: 90
}),
(g)-[:HAS_SCHEDULE]->(sch10);

// 5) Создаём связи посещаемости точно как в PostgreSQL
// Добавляем только записи где presence = TRUE
MATCH (s:Student {id: 1}), (sch:Schedule {title: 'Введение в программирование', date: date('2023-09-01')})
CREATE (s)-[:ATTENDED]->(sch);

MATCH (s:Student {id: 2}), (sch:Schedule {title: 'Введение в программирование', date: date('2023-09-01')})
CREATE (s)-[:ATTENDED]->(sch);

MATCH (s:Student {id: 1}), (sch:Schedule {title: 'ООП – практика', date: date('2023-09-05')})
CREATE (s)-[:ATTENDED]->(sch);

MATCH (s:Student {id: 5}), (sch:Schedule {title: 'Основы баз данных', date: date('2023-09-10')})
CREATE (s)-[:ATTENDED]->(sch);

MATCH (s:Student {id: 6}), (sch:Schedule {title: 'Основы баз данных', date: date('2023-09-10')})
CREATE (s)-[:ATTENDED]->(sch);

MATCH (s:Student {id: 8}), (sch:Schedule {title: 'Введение в менеджмент', date: date('2023-09-20')})
CREATE (s)-[:ATTENDED]->(sch);

MATCH (s:Student {id: 9}), (sch:Schedule {title: 'Практика по дискретной математике', date: date('2023-09-25')})
CREATE (s)-[:ATTENDED]->(sch);
