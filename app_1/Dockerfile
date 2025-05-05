# app_1/Dockerfile
FROM python:3.12-slim
WORKDIR /usr/src/app

# Копируем корень проекта (содержимое папки app_1 будет доступно в ./app_1)
COPY . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Переключаемся в папку app_1, чтобы запускать main_1.py как "main_1:app"
WORKDIR /usr/src/app/app_1

# Команда по умолчанию
CMD ["uvicorn", "main_1:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
