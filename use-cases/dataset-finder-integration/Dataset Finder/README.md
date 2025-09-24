## Run via Docker

1. Run `docker build -t data-grabber .`
2. Run `docker run -p 5000:5000 -e RDMO_TOKEN=my_secret_token data-grabber`
3. Open [website](http://127.0.0.1:5000) shown in docker
