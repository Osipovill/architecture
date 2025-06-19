FROM python:3.10-bullseye

WORKDIR /app

# установим все зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# копируем скрипт
COPY cdc.py .

# точка входа
CMD ["python", "cdc.py"]
