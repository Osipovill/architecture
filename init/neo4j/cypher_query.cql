// 1) Полная очистка графа
MATCH (n) DETACH DELETE n;

// 2) Группы
CREATE (g1:Group {id: 1, code: 'БСБО-03-22'}),
       (g2:Group {id: 2, code: 'БСБО-04-22'}),
       (g3:Group {id: 3, code: 'БСБО-05-22'}),
       (g4:Group {id: 4, code: 'БСБО-06-22'}),
       (g5:Group {id: 5, code: 'БСБО-07-22'}),
       (g6:Group {id: 6, code: 'БСБО-08-22'}),
       (g7:Group {id: 7, code: 'БСБО-09-22'}),
       (g8:Group {id: 8, code: 'БСБО-10-22'}),
       (g9:Group {id: 9, code: 'БСБО-11-22'}),
       (g10:Group {id: 10, code: 'БСБО-12-22'});

// 3) Студенты
MATCH (g:Group {id: 1})
CREATE (s1:Student {id: 1, name: 'Мартынова Лия'})-[:BELONGS_TO]->(g),
       (s2:Student {id: 2, name: 'Осипов Илья'})-[:BELONGS_TO]->(g),
       (s3:Student {id: 3, name: 'Ершов Александр'})-[:BELONGS_TO]->(g);

MATCH (g:Group {id: 2})
CREATE (s4:Student {id: 4, name: 'Иванов Сергей'})-[:BELONGS_TO]->(g),
       (s5:Student {id: 5, name: 'Петрова Анна'})-[:BELONGS_TO]->(g);

MATCH (g:Group {id: 3})
CREATE (s6:Student {id: 6, name: 'Сидоров Максим'})-[:BELONGS_TO]->(g),
       (s7:Student {id: 7, name: 'Кузнецова Ольга'})-[:BELONGS_TO]->(g);

MATCH (g:Group {id: 4})
CREATE (s8:Student {id: 8, name: 'Новиков Роман'})-[:BELONGS_TO]->(g);

MATCH (g:Group {id: 5})
CREATE (s9:Student {id: 9, name: 'Фролова Светлана'})-[:BELONGS_TO]->(g);

MATCH (g:Group {id: 6})
CREATE (s10:Student {id: 10, name: 'Смирнова Елена'})-[:BELONGS_TO]->(g);

// 4) Расписание с course_id, course_title, tag
WITH [
  {sch_id: 1, title: 'Введение в программирование', date: '2023-09-01', dur: 90, group_id: 1, course_id: 101, course_title: 'Введение в программирование'},
  {sch_id: 2, title: 'ООП – практика', date: '2023-09-05', dur: 120, group_id: 2, course_id: 102, course_title: 'ООП – практика'},
  {sch_id: 3, title: 'Основы баз данных', date: '2023-09-10', dur: 90, group_id: 3, course_id: 103, course_title: 'Основы баз данных'},
  {sch_id: 4, title: 'Экономическая теория – задачи', date: '2023-09-15', dur: 120, group_id: 4, course_id: 104, course_title: 'Экономическая теория – задачи'},
  {sch_id: 5, title: 'Введение в менеджмент', date: '2023-09-20', dur: 90, group_id: 5, course_id: 105, course_title: 'Введение в менеджмент'},
  {sch_id: 6, title: 'Практика по дискретной математике', date: '2023-09-25', dur: 120, group_id: 6, course_id: 106, course_title: 'Практика по дискретной математике'},
  {sch_id: 7, title: 'Основы физики', date: '2023-10-01', dur: 90, group_id: 7, course_id: 107, course_title: 'Основы физики'},
  {sch_id: 8, title: 'Органическая химия – введение', date: '2023-10-05', dur: 90, group_id: 8, course_id: 108, course_title: 'Органическая химия – введение'},
  {sch_id: 9, title: 'Биология клетки – структура', date: '2023-10-10', dur: 120, group_id: 9, course_id: 109, course_title: 'Биология клетки – структура'},
  {sch_id: 10, title: 'Статистика: основы', date: '2023-10-15', dur: 90, group_id: 10, course_id: 110, course_title: 'Статистика: основы'}
] AS lectures
UNWIND lectures AS l
MATCH (g:Group {id: l.group_id})
CREATE (sch:Schedule {
  id: l.sch_id,
  title: l.title,
  date: date(l.date),
  duration: l.dur,
  course_id: l.course_id,
  course_title: l.course_title,
  tag: 'специальная'
}),
(g)-[:HAS_SCHEDULE]->(sch);

// 5) Посещения
MATCH (s:Student {id: 1}), (sch:Schedule {id: 1}) CREATE (s)-[:ATTENDED]->(sch);
MATCH (s:Student {id: 2}), (sch:Schedule {id: 1}) CREATE (s)-[:ATTENDED]->(sch);
MATCH (s:Student {id: 1}), (sch:Schedule {id: 2}) CREATE (s)-[:ATTENDED]->(sch);
MATCH (s:Student {id: 5}), (sch:Schedule {id: 3}) CREATE (s)-[:ATTENDED]->(sch);
MATCH (s:Student {id: 6}), (sch:Schedule {id: 3}) CREATE (s)-[:ATTENDED]->(sch);
MATCH (s:Student {id: 8}), (sch:Schedule {id: 5}) CREATE (s)-[:ATTENDED]->(sch);
MATCH (s:Student {id: 9}), (sch:Schedule {id: 6}) CREATE (s)-[:ATTENDED]->(sch);
