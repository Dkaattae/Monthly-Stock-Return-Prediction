FROM python:3.12-slim

WORKDIR /app

RUN pip install -U pip
RUN pip install pipenv 
RUN apt-get update && apt-get install -y curl

COPY [ "Pipfile", "Pipfile.lock", "./" ]

RUN pipenv install --system --deploy

COPY [ "predict_app.py", "predict.py", "./" ]
COPY [ "artifacts/", "artifacts/"]

CMD [ "gunicorn", "--workers", "4", "--bind", "0.0.0.0:8080", "predict_app:app" ]
