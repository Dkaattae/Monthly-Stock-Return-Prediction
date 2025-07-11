FROM python:3.12-slim

WORKDIR /app

RUN pip install -U pip

COPY [ "requirements.txt", "." ]

RUN pip install --no-cache-dir -r requirements.txt

COPY [ "metrics_calculation.py", "."]
COPY [ "backfill.parquet", "backfill.parquet"]

CMD [ "python", "metrics_calculation.py"]

