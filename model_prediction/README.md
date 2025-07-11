

# predict backfill

docker build -f Dockerfile.backfill -t backfill .

docker run \
  --env-file .env \
  -v $(pwd)/output:/app/output \
  backfill 