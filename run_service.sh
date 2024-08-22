# build docker image
docker build -t receiver-service .

# run docker container
docker run --env-file .env -p 3000:3000 receiver-service