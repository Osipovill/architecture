#!/bin/bash
# Создаем индекс "materials" с заданным mapping для полей
curl -X PUT "http://elasticsearch:9200/materials" \
  -H 'Content-Type: application/json' -d '{
    "mappings": {
      "properties": {
        "material_id": { "type": "integer" },
        "class_id":    { "type": "integer" },
        "title":       { "type": "text" },
        "content":     { "type": "text" }
      }
    }
}' && echo ""

# Материал 1: Введение в программирование (Лекция)
curl -X POST "http:/elasticsearch:9200/materials/_doc/1" \
  -H 'Content-Type: application/json' -d '{
    "material_id": 1,
    "class_id": 1,
    "title": "Введение в программирование",
    "content": "Лекция \"Введение в программирование\" охватывает основы алгоритмического мышления и принципы построения программ. В данном занятии рассматриваются понятия языка программирования, синтаксиса, переменных, типов данных, операторов, условных конструкций и циклов. Студенты изучают, как простые алгоритмы могут комбинироваться для решения сложных задач, а также анализируются примеры на популярных языках, таких как Python и C. Практические упражнения направлены на формирование навыков написания корректного кода и понимания логики программирования."
}' && echo ""

# Материал 2: ООП – практика (Семинар)
curl -X POST "http://elasticsearch:9200/materials/_doc/2" \
  -H 'Content-Type: application/json' -d '{
    "material_id": 2,
    "class_id": 2,
    "title": "ООП – практика",
    "content": "Лекция \"ООП – практика\" посвящена ключевым концепциям объектно-ориентированного программирования. В ходе занятия подробно разбираются понятия классов, объектов, наследования, инкапсуляции и полиморфизма. Студенты знакомятся с практическими примерами на языках, таких как Java и C++, где показывается как создавать свои классы, реализовывать наследование и работать с методами. Теоретическая часть дополняется практическими заданиями, позволяющими закрепить полученные знания и освоить структурирование кода в объектно-ориентированном стиле."
}' && echo ""

# Материал 3: Основы баз данных (Лекция)
curl -X POST "http://elasticsearch:9200/materials/_doc/3" \
  -H 'Content-Type: application/json' -d '{
    "material_id": 3,
    "class_id": 3,
    "title": "Основы баз данных",
    "content": "Лекция \"Основы баз данных\" представляет подробное введение в мир реляционных систем хранения данных. В занятии объясняется, что такое база данных, как осуществляется организация информации в виде таблиц и какие преимущества дает нормализация данных. Одним из ключевых моментов лекции является определение языка SQL (Structured Query Language) как стандартизированного средства для управления базами данных. Рассматриваются основные команды SQL: SELECT, INSERT, UPDATE, DELETE, а также принципы построения запросов, создание таблиц и определение связей между ними с помощью первичных и внешних ключей. Дополнительно обсуждаются вопросы оптимизации запросов и роль индексов для повышения производительности систем."
}' && echo ""

# Материал 4: Экономическая теория – задачи (Лабораторное занятие)
curl -X POST "http://elasticsearch:9200/materials/_doc/4" \
  -H 'Content-Type: application/json' -d '{
    "material_id": 4,
    "class_id": 4,
    "title": "Экономическая теория – задачи",
    "content": "Лабораторное занятие \"Экономическая теория – задачи\" направлено на применение теоретических моделей в практических расчетах. В лекции обсуждаются основные экономические модели, такие как модели спроса и предложения, рыночного равновесия и ценовых механизмов. Студенты учатся анализировать влияние различных факторов на рыночные процессы, а также решать задачи, связанные с оценкой экономической эффективности и прогнозированием изменений на рынке. Теоретическая часть подкрепляется конкретными примерами, расчетами и использованием математических методов для моделирования экономических процессов."
}' && echo ""

# Материал 5: Введение в менеджмент (Лекция)
curl -X POST "http://elasticsearch:9200/materials/_doc/5" \
  -H 'Content-Type: application/json' -d '{
    "material_id": 5,
    "class_id": 5,
    "title": "Введение в менеджмент",
    "content": "Лекция \"Введение в менеджмент\" знакомит слушателей с основными принципами управления организацией. В занятии рассматриваются понятия планирования, организации, мотивации и контроля, а также современные подходы к управлению в условиях динамичной бизнес-среды. Студенты изучают различные модели менеджмента, примеры успешных управленческих стратегий и методы оптимизации бизнес-процессов. Особое внимание уделяется разработке стратегических планов и внедрению инновационных методов в управлении компанией."
}' && echo ""

# Материал 6: Практика по дискретной математике (Семинар)
curl -X POST "http://elasticsearch:9200/materials/_doc/6" \
  -H 'Content-Type: application/json' -d '{
    "material_id": 6,
    "class_id": 6,
    "title": "Практика по дискретной математике",
    "content": "Семинар \"Практика по дискретной математике\" направлен на решение типичных задач из области дискретной математики. В рамках занятия изучаются понятия множеств, отношений, функций, графов и комбинаторики. Студенты знакомятся с методами доказательства теорем, решают примеры по построению графов, вычислению комбинаторных коэффициентов и анализу алгоритмов. Теоретическая часть сопровождается практическими заданиями, что позволяет закрепить представленные методы и понять, как абстрактные математические концепции применяются в решении реальных проблем."
}' && echo ""

# Материал 7: Основы физики (Лекция)
curl -X POST "http://elasticsearch:9200/materials/_doc/7" \
  -H 'Content-Type: application/json' -d '{
    "material_id": 7,
    "class_id": 7,
    "title": "Основы физики",
    "content": "Лекция \"Основы физики\" представляет введение в фундаментальные законы природы. В материале обсуждаются базовые понятия, такие как масса, сила, энергия и импульс, а также законы движения, сформулированные Ньютоном. Кроме того, затрагиваются основы термодинамики, электромагнетизма и волновой теории. Студенты изучают экспериментальные подтверждения теоретических положений и узнают, как физические законы применяются для описания явлений в окружающем мире."
}' && echo ""

# Материал 8: Органическая химия – введение (Лекция)
curl -X POST "http://elasticsearch:9200/materials/_doc/8" \
  -H 'Content-Type: application/json' -d '{
    "material_id": 8,
    "class_id": 8,
    "title": "Органическая химия – введение",
    "content": "Лекция \"Органическая химия – введение\" посвящена изучению строения и свойств органических соединений. В материале дается определение органической химии, описываются основные типы химических связей, функциональные группы и механизмы реакций, таких как замещение, присоединение и отщепление. Приводятся схемы молекулярных структур, рассматривается явление изомерии и обсуждаются примеры синтеза органических веществ. Занятие направлено на закладывание фундаментальных знаний, необходимых для дальнейшего углубленного изучения химии."
}' && echo ""

# Материал 9: Биология клетки – структура (Семинар)
curl -X POST "http://elasticsearch:9200/materials/_doc/9" \
  -H 'Content-Type: application/json' -d '{
    "material_id": 9,
    "class_id": 9,
    "title": "Биология клетки – структура",
    "content": "Семинар \"Биология клетки – структура\" фокусируется на организационных и функциональных особенностях клетки. В занятии рассматриваются структура и функции клеточной мембраны, ядра, митохондрий, рибосом и других органелл. Обсуждаются процессы клеточного деления, обмен веществ и межклеточные взаимодействия. Теоретическая часть подкрепляется примерами современных исследований в области молекулярной биологии, что помогает студентам осознать сложность клеточной организации и важность каждого компонента для жизнедеятельности организма."
}' && echo ""

# Материал 10: Статистика: основы (Лекция)
curl -X POST "http://elasticsearch:9200/materials/_doc/10" \
  -H 'Content-Type: application/json' -d '{
    "material_id": 10,
    "class_id": 10,
    "title": "Статистика: основы",
    "content": "Лекция \"Статистика: основы\" представляет собой подробное введение в теоретические аспекты статистики и методы анализа данных. В материале подробно рассматриваются понятия выборки и генеральной совокупности, рассчитываются среднее значение, дисперсия и стандартное отклонение. Также обсуждаются методы построения распределений, регрессионного анализа и проверка статистических гипотез. Студенты знакомятся с практическими примерами применения статистических методов для анализа данных в исследованиях и бизнес-аналитике, что является важным навыком в современной науке."
}' && echo ""

echo "ElasticSearch индекс 'materials' создан, и все материалы успешно загружены."
