db = db.getSiblingDB('university');

db.universities.drop();


db.universities.insertMany([
  {
    university_id: 1,
    name: "Университет A",
    institutes: [
      {
        institute_id: 1,
        name: "Институт информационных технологий",
        departments: [
          { department_id: 1, 
            name: "Кафедра программирования",               
            head: "Иванов И.И.",   
            phone: "+7-111-111-1111" },
          { department_id: 2, 
            name: "Кафедра информационных систем",          
            head: "Петров П.П.",    
            phone: "+7-111-111-1112" }
        ]
      },
      {
        institute_id: 2,
        name: "Институт экономики",
        departments: [
          { department_id: 3, 
            name: "Кафедра менеджмента",                   
            head: "Сидоров С.С.",   
            phone: "+7-111-111-1113" },
          { department_id: 4, 
            name: "Кафедра финансов",                      
            head: "Кузнецов К.К.",  
            phone: "+7-111-111-1114" }
        ]
      }
    ]
  },
  {
    university_id: 2,
    name: "Университет B",
    institutes: [
      {
        institute_id: 3,
        name: "Институт права",
        departments: [
          { department_id: 5, 
            name: "Кафедра теоретической математики",     
            head: "Андреев А.А.",   
            phone: "+7-111-111-1115" }
        ]
      },
      {
        institute_id: 4,
        name: "Институт управления",
        departments: [
          { department_id: 6, 
            name: "Кафедра прикладной математики",        
            head: "Борисов Б.Б.",   
            phone: "+7-111-111-1116" }
        ]
      }
    ]
  },
  {
    university_id: 3,
    name: "Университет C",
    institutes: [
      {
        institute_id: 5,
        name: "Институт математики",
        departments: [
          { department_id: 7, 
            name: "Кафедра общей физики",                  
            head: "Васильев В.В.",  
            phone: "+7-111-111-1117" }
        ]
      },
      {
        institute_id: 6,
        name: "Институт физики",
        departments: [
          { department_id: 8, 
            name: "Кафедра экспериментальной физики",      
            head: "Григорьев Г.Г.", 
            phone: "+7-111-111-1118" }
        ]
      }
    ]
  },
  {
    university_id: 4,
    name: "Университет D",
    institutes: [
      {
        institute_id: 7,
        name: "Институт химии",
        departments: [
          { department_id: 9, 
            name: "Кафедра химии",                         
            head: "Дмитриев Д.Д.",  
            phone: "+7-111-111-1119" }
        ]
      },
      {
        institute_id: 8,
        name: "Институт биологии",
        departments: [
          { department_id: 10, 
            name: "Кафедра биологии",                     
            head: "Егоров Е.Е.",    
            phone: "+7-111-111-1120" }
        ]
      }
    ]
  },
  {
    university_id: 5,
    name: "Университет E",
    institutes: [
      { institute_id: 9,  name: "Институт лингвистики",   departments: [] },
      { institute_id: 10, name: "Институт социологии",    departments: [] }
    ]
  },
  { university_id: 6,  name: "Университет F", institutes: [] },
  { university_id: 7,  name: "Университет G", institutes: [] },
  { university_id: 8,  name: "Университет H", institutes: [] },
  { university_id: 9,  name: "Университет I", institutes: [] },
  { university_id: 10, name: "Университет J", institutes: [] }
]);

print("Инициализация MongoDB завершена. Всего университетов: " + db.universities.countDocuments());
