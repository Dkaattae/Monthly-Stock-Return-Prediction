FROM public.ecr.aws/lambda/python:3.12

RUN pip install -U pip
RUN pip install pipenv 

COPY [ "Pipfile", "Pipfile.lock", "./" ]

RUN pipenv install --system --deploy

COPY [ "predict_app.py", "predict.py", "./" ]

CMD [ "gunicorn", "--workers", "4", "--bind", "0.0.0.0:8080", "predict_app:app" ]