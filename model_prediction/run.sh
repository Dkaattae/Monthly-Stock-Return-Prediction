#!/usr/bin/env bash

set -e 

export RUN_ID=f085545033ee42e48ab356df6f8ef03e
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test

if [ "${LOCAL_IMAGE_NAME}" == "" ]; then 
    LOCAL_TAG=`date +"%Y-%m-%d-%H-%M"`
    export LOCAL_IMAGE_NAME="return-prediction:${LOCAL_TAG}"
    echo "LOCAL_IMAGE_NAME is not set, building a new image with tag ${LOCAL_IMAGE_NAME}"
    docker build -t ${LOCAL_IMAGE_NAME} .
else
    echo "no need to build image ${LOCAL_IMAGE_NAME}"
fi

docker-compose up -d
sleep 1

docker build -f "Dockerfile.test" -t return-prediction:test .

aws --endpoint-url=http://localhost:4566 s3  mb s3://return-prediction --region us-east-1

docker network inspect predict-network >/dev/null 2>&1 || docker network create predict-network

docker run --rm -e PYTHONPATH=/app return-prediction:test pytest tests/unit

docker run -d \
    --name my-prediction-app \
    --network predict-network \
    --add-host=host.docker.internal:host-gateway \
    -e RUN_ID=f085545033ee42e48ab356df6f8ef03e \
    -e AWS_ACCESS_KEY_ID=test \
    -e AWS_SECRET_ACCESS_KEY=test \
    -p 9696:8080 \
    ${LOCAL_IMAGE_NAME} 

until docker exec my-prediction-app curl -s http://localhost:8080/health | grep ok; do
    echo "Still waiting..."
    sleep 1
done

docker run --rm \
  --add-host=host.docker.internal:host-gateway \
  --network predict-network \
  return-prediction:test \
  pytest tests/integration

docker-compose down
docker stop my-prediction-app
docker remove my-prediction-app