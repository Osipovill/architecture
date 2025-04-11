db = db.getSiblingDB('university');
// Очищаем коллекцию, если она существует.
db.universities.drop();

// Вставляем 10 документов, где для университетов A–E заданы институты согласно данным из PostgreSQL.
db.universities.insertMany([
  {
    university_id: 1,
    name: "Университет A",
    institutes: [
      { institute_id: 1, name: "Институт информационных технологий" },
      { institute_id: 2, name: "Институт экономики" }
    ]
  },
  {
    university_id: 2,
    name: "Университет B",
    institutes: [
      { institute_id: 3, name: "Институт права" },
      { institute_id: 4, name: "Институт управления" }
    ]
  },
  {
    university_id: 3,
    name: "Университет C",
    institutes: [
      { institute_id: 5, name: "Институт математики" },
      { institute_id: 6, name: "Институт физики" }
    ]
  },
  {
    university_id: 4,
    name: "Университет D",
    institutes: [
      { institute_id: 7, name: "Институт химии" },
      { institute_id: 8, name: "Институт биологии" }
    ]
  },
  {
    university_id: 5,
    name: "Университет E",
    institutes: [
      { institute_id: 9, name: "Институт лингвистики" },
      { institute_id: 10, name: "Институт социологии" }
    ]
  },
  {
    university_id: 6,
    name: "Университет F",
    institutes: []
  },
  {
    university_id: 7,
    name: "Университет G",
    institutes: []
  },
  {
    university_id: 8,
    name: "Университет H",
    institutes: []
  },
  {
    university_id: 9,
    name: "Университет I",
    institutes: []
  },
  {
    university_id: 10,
    name: "Университет J",
    institutes: []
  }
]);

print("Инициализация MongoDB завершена. Количество университетов: " + db.universities.countDocuments());
