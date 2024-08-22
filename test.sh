#!/bin/bash

echo "build automating image"
docker build -t cy-test -f Dockerfile.test .

echo "deploying app...."
docker-compose up -d --build

echo "wait the app ready http://localhost:5085"
docker run -u node  --network=host --entrypoint npx cy-test wait-on http://localhost:5085

echo "backup db.sqlite3 before make changes"
cp db.sqlite3 db.sqlite3.backup

echo "run the test"
docker run -u node --rm -v $(pwd)/test_reports:/workspace/results -v $(pwd)/db.sqlite3:/tmp/db.sqlite3 --network=host cy-test

echo "remove all the container"
docker-compose down

echo "reset db.sqlite3 to original one"
cp db.sqlite3.backup db.sqlite3
rm db.sqlite3.backup

echo "done"
