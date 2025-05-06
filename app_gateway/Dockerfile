# Используем легковесный образ Python
FROM python:3.10-bullseye

# Рабочая директория внутри контейнера
WORKDIR /app

# Копируем файл с зависимостями и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё приложение в контейнер
COPY . .

# Открываем порт
EXPOSE 80

# По умолчанию запускаем Uvicorn с вашим приложением
CMD ["uvicorn", "main_gateway:app", "--host", "0.0.0.0", "--port", "80"]
