FROM python:3.10-bullseye
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY cdc_hierarchy.py .
CMD ["python", "cdc_hierarchy.py"]