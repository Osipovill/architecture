// 1) Полная очистка графа
MATCH (n) DETACH DELETE n;

// 2) Создаём группы
CREATE (g1:Group {code: 'БСБО-03-22'}),
       (g2:Group {code: 'БСБО-04-22'}),
       (g3:Group {code: 'БСБО-05-22'});

// 3) Создаём 30 студентов
UNWIND [
  {id:1,  name:'Мартынова Лия',      group:'БСБО-03-22'},
  {id:2,  name:'Осипов Илья',         group:'БСБО-03-22'},
  {id:3,  name:'Ершов Александр',    group:'БСБО-03-22'},
  {id:4,  name:'Студент 4',          group:'БСБО-03-22'},
  {id:5,  name:'Студент 5',          group:'БСБО-03-22'},
  {id:6,  name:'Студент 6',          group:'БСБО-03-22'},
  {id:7,  name:'Студент 7',          group:'БСБО-03-22'},
  {id:8,  name:'Студент 8',          group:'БСБО-03-22'},
  {id:9,  name:'Студент 9',          group:'БСБО-03-22'},
  {id:10, name:'Студент 10',         group:'БСБО-03-22'},
  {id:11, name:'Студент 11',         group:'БСБО-04-22'},
  {id:12, name:'Студент 12',         group:'БСБО-04-22'},
  {id:13, name:'Студент 13',         group:'БСБО-04-22'},
  {id:14, name:'Студент 14',         group:'БСБО-04-22'},
  {id:15, name:'Студент 15',         group:'БСБО-04-22'},
  {id:16, name:'Студент 16',         group:'БСБО-04-22'},
  {id:17, name:'Студент 17',         group:'БСБО-04-22'},
  {id:18, name:'Студент 18',         group:'БСБО-04-22'},
  {id:19, name:'Студент 19',         group:'БСБО-04-22'},
  {id:20, name:'Студент 20',         group:'БСБО-04-22'},
  {id:21, name:'Студент 21',         group:'БСБО-05-22'},
  {id:22, name:'Студент 22',         group:'БСБО-05-22'},
  {id:23, name:'Студент 23',         group:'БСБО-05-22'},
  {id:24, name:'Студент 24',         group:'БСБО-05-22'},
  {id:25, name:'Студент 25',         group:'БСБО-05-22'},
  {id:26, name:'Студент 26',         group:'БСБО-05-22'},
  {id:27, name:'Студент 27',         group:'БСБО-05-22'},
  {id:28, name:'Студент 28',         group:'БСБО-05-22'},
  {id:29, name:'Студент 29',         group:'БСБО-05-22'},
  {id:30, name:'Студент 30',         group:'БСБО-05-22'}
] AS student
CREATE (s:Student {id: student.id, name: student.name})
WITH s, student
MATCH (g:Group {code: student.group})
CREATE (s)-[:BELONGS_TO]->(g);

// 4) Создаём расписание (Schedule) и связываем с группами
// Для простоты: по 10 встреч на каждую группу, даты подряд
UNWIND [
  // для БСБО-03-22
  {group:'БСБО-03-22', title:'Математика',                date:'2023-09-01'},
  {group:'БСБО-03-22', title:'Физика',                    date:'2023-09-02'},
  {group:'БСБО-03-22', title:'Информатика',               date:'2023-09-03'},
  {group:'БСБО-03-22', title:'Алгебра',                    date:'2023-09-04'},
  {group:'БСБО-03-22', title:'Геометрия',                  date:'2023-09-05'},
  {group:'БСБО-03-22', title:'Дискретная математика',      date:'2023-09-06'},
  {group:'БСБО-03-22', title:'Линейная алгебра',           date:'2023-09-07'},
  {group:'БСБО-03-22', title:'Теория вероятностей',        date:'2023-09-08'},
  {group:'БСБО-03-22', title:'Статистика',                 date:'2023-09-09'},
  {group:'БСБО-03-22', title:'Математический анализ',      date:'2023-09-10'},

  // для БСБО-04-22
  {group:'БСБО-04-22', title:'История',                    date:'2023-09-11'},
  {group:'БСБО-04-22', title:'География',                  date:'2023-09-12'},
  {group:'БСБО-04-22', title:'Социология',                 date:'2023-09-13'},
  {group:'БСБО-04-22', title:'Политология',                date:'2023-09-14'},
  {group:'БСБО-04-22', title:'Экономика',                  date:'2023-09-15'},
  {group:'БСБО-04-22', title:'Менеджмент',                 date:'2023-09-16'},
  {group:'БСБО-04-22', title:'Юриспруденция',              date:'2023-09-17'},
  {group:'БСБО-04-22', title:'Правоведение',               date:'2023-09-18'},
  {group:'БСБО-04-22', title:'Этика',                      date:'2023-09-19'},
  {group:'БСБО-04-22', title:'Философия',                  date:'2023-09-20'},

  // для БСБО-05-22
  {group:'БСБО-05-22', title:'Химия',                      date:'2023-09-21'},
  {group:'БСБО-05-22', title:'Биология',                   date:'2023-09-22'},
  {group:'БСБО-05-22', title:'Геология',                   date:'2023-09-23'},
  {group:'БСБО-05-22', title:'Экология',                   date:'2023-09-24'},
  {group:'БСБО-05-22', title:'Астрономия',                 date:'2023-09-25'},
  {group:'БСБО-05-22', title:'Метеорология',               date:'2023-09-26'},
  {group:'БСБО-05-22', title:'Океанология',                date:'2023-09-27'},
  {group:'БСБО-05-22', title:'Ботаника',                   date:'2023-09-28'},
  {group:'БСБО-05-22', title:'Зоология',                   date:'2023-09-29'},
  {group:'БСБО-05-22', title:'Эволюция',                   date:'2023-09-30'}
] AS item
MATCH (g:Group {code: item.group})
CREATE (sch:Schedule {
  title: item.title,
  date: date(item.date),
  duration: 90
})
CREATE (g)-[:HAS_SCHEDULE]->(sch);

// 5) Записываем посещаемость только присутствующих студентов
UNWIND [
  {studentId: 1, title: 'Математика',               date: '2023-09-01', presence: true},
  {studentId: 2, title: 'Математика',               date: '2023-09-01', presence: true},
  {studentId: 3, title: 'Математика',               date: '2023-09-01', presence: false},
  {studentId: 1, title: 'Физика',                   date: '2023-09-02', presence: true},
  {studentId: 4, title: 'Физика',                   date: '2023-09-02', presence: false},
  {studentId: 5, title: 'Информатика',              date: '2023-09-03', presence: true},
  {studentId: 6, title: 'Информатика',              date: '2023-09-03', presence: true},
  {studentId: 7, title: 'Алгебра',                  date: '2023-09-04', presence: false},
  {studentId: 8, title: 'Геометрия',                date: '2023-09-05', presence: true},
  {studentId: 9, title: 'Дискретная математика',     date: '2023-09-06', presence: true}
] AS a
// Оставляем только записи с presence = true
WITH a
WHERE a.presence = true
MATCH (s:Student {id: a.studentId})
MATCH (sch:Schedule {title: a.title, date: date(a.date)})
CREATE (s)-[:ATTENDED]->(sch);
