# predict
if mlflow server is alive, load model from mlflow model registry.   
if not, load model from S3.   
if S3 is not accessible, load from local folder.   
prepare features using artifact.   
predict using model and features.   

# predict app   
wrap predict with flask api.   
in dockerfile, deploy with gunicorn.
```
docker build -t predict_app .
docker run \
  --env-file .env \
  -p 9696:8080 \
  predict_app
```
note: get rid of .env line

open another terminal,   
```
curl -X POST http://localhost:9696/predict \
  -H "Content-Type: application/json" \
  --data @json_records.json
```

# predict backfill
```
docker build -f Dockerfile.backfill -t backfill .

docker run \
  --env-file .env \
  -v $(pwd)/output:/app/output \
  backfill 
```

note: get rid of line including .env file

# unit tests and integration test
test prepare feature function  
test predict function
test outside docker
`pipenv run pytest tests`

# mock s3
test outside of docker
using localstack to mock S3

# formatting
`pipenv run black .`

# sorting
`pipenv run isort .`

# linting
`pipenv run pylint predict.py`

# CI
```
chmod +x run.sh
./run.sh
```
(not done)