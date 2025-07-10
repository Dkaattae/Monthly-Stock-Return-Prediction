FROM public.ecr.aws/lambda/python:3.12

RUN pip install -U pip
RUN pip install pipenv 

COPY [ "Pipfile", "Pipfile.lock", "./" ]

RUN pipenv install --system --deploy

COPY [ "predict_app.py", "predict.py", "./" ]

CMD [ "predict_app.handler" ]