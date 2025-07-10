FROM python:3.12-slim

# Install any additional dependencies you want here, for example:
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && pip install pipenv

WORKDIR /workspace