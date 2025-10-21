# Pet Store API

## How to access OpenAPI generated documentation?

To access it you will have to start the server (check "How to build and run?" section). Then openapi.json must be accessible at the http://localhost:8000/openapi.json

## How to build and run?

1. First you will need to create an environment:

```bash
python -m venv env
source env/bin/activate
```

2. After that install all dependencies:

```bash
python -m pip install -r svc/server/requirements.txt
```

3. In the [.env-example](svc/server/.env-example) reside all environment variables that application requires to run. Create an .env file with all variables filled and put in svc/server/.env

### Run server with docker compose (recommended).

To do so you will need an installed Docker. And input the following command:

```bash
docker compose up --build -d
```

This will run services in the background. Default address for OpenAPI docs: http://localhost:8081/docs.

### Run server with pure docker.

To do so you will need to build an image first with the following command:

```bash
cd svc/server
docker image build . -t pet-server
```

And then run the image with the following command:

```bash
cd -
mkdir data/ logs/
docker run --rm -p 8081:8081 --mount type=bind,src=./data,dst=/app/data --mount type=bind,src=./logs,dst=/app/logs -d pet-server
```

This will run the container in the detached mode.

### Run server in dev mode.

To run a server in dev mode all you need to do is:

```bash
cd svc/server
fastapi dev main.py
```

By default, server will start on http://locahost:8000/docs.

## How to authorize DML for products?

If you are seller, you will have to prove it! Quite simple authorization consists of env variable "SECRET_KEY" which is "password" by default. This key must be passed as a header "X-API-Key" to authorize the following endpoints:

- POST /api/product
- PUT /api/product/{id}
- DELETE /api/product/{id}
- POST /api/product/{id}/sell

Everything else does not have to be authorized.

## TODO
- ✅ Add logging.
- ✅ Add Dockerfile & Docker Compose file.
- ✅ Rewrite docstrings in server API, so it will look more readable in the OpenAPI docs.
- ✅ Add basic authorization for seller.

## What can be Improved?
- Add ChatGPT to the available recommenders & Implement Chain-of-Responsibility Pattern. This way we can proof service from sudden connections issues.
- Instead of user-defined token generate a new one upon each start of the application. This way we can guarantee that generated token is long and complex enough + it will not depend on a seller at all.
- Add more informative examples of exceptions. Right now we have 500 Error, that hase an example: "product_id=... is not present", but this error will 100% never be thrown with such detail.
- Add end-to-end tests + integrational tests for Recommenders. This will help streamline development process.
- Add "seles" table with columns: "sell_id", "product_id", "quantity", "cancelled". We can keep track of all sales and get an insights from this, like the amount of "cancells" for each product, or how much money we get from sales of each product.
