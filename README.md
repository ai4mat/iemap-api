# IEMAP RESTful/GraphQL API

This API allow you to do some CRUD operation with RESTful methods over the Mission Innovation mongoDB.

# Quickstart

First, set environment variables and create database. For example using `docker`: ::

    export MONGO_DB=rwdb MONGO_PORT=5432 MONGO_USER=MONGO MONGO_PASSWORD=MONGO
    docker run --name mongodb --rm -e MONGO_USER="$MONGO_USER" -e MONGO_PASSWORD="$MONGO_PASSWORD" -e MONGO_DB="$MONGO_DB" MONGO
    export MONGO_HOST=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' pgdb)
    mongo --host=$MONGO_HOST --port=$MONGO_PORT --username=$MONGO_USER $MONGO_DB

Then run the following commands to bootstrap your environment with `poetry`: ::

    git clone https://github.com/markqiu/fastapi-realworld-example-app
    cd fastapi-realworld-example-app
    poetry install
    poetry shell

Then create `.env` file (or rename and modify `.env.example`) in project root and set environment variables for application: ::

    touch .env
    echo "PROJECT_NAME=FastAPI RealWorld Application Example" >> .env
    echo DATABASE_URL=mongo://$MONGO_USER:$MONGO_PASSWORD@$MONGO_HOST:$MONGO_PORT/$MONGO_DB >> .env
    echo SECRET_KEY=$(openssl rand -hex 32) >> .env
    echo ALLOWED_HOSTS='"127.0.0.1", "localhost"' >> .env

To run the web application in debug use::

    uvicorn app.main:app --reload

# Deployment with Docker

---

You must have `docker` and `docker-compose` tools installed to work with material in this section.
First, create `.env` file like in `Quickstart` section or modify `.env.example`. `MONGO_HOST` must be specified as `db` or modified in `docker-compose.yml` also. Then just run::

    docker-compose up -d

Application will be available on `localhost` or `127.0.0.1` in your browser.

# Web routes

---

All routes are available on `/docs` or `/redoc` paths with Swagger or ReDoc.

# Project structure

---

Files related to application are in the `app` directory. `  
Application parts are:

::

    models  - pydantic models that used in crud or handlers
    crud    - CRUD for types from models (create new user/article/comment, check if user is followed by another, etc)
    db      - db specific utils
    core    - some general components (jwt, security, configuration)
    api     - handlers for routes
    main.py - FastAPI application instance, CORS configuration and api router including

## Configure

Use the `env.sample` to setup your mongoDB URI and save it as `.env`.

## Run for development (locally)

1.  Get the environment varibales:
    ```bash
    export $(xargs < .env)
    ```
2.  Install `poetry`:

    ```
    curl -sSL https://install.python-poetry.org | python3 -
    ```

3.  Then run the following commands to bootstrap your environment with `poetry`:

    ```
    git clone https://github.com/markqiu/fastapi-realworld-example-app
    cd fastapi-realworld-example-app
    poetry install
    poetry shell

    ```

4.  To run the web application in debug use:

    ```
    uvicorn app.main:app --reload
    ```

    Or alternatively use:

    ```
      python start_server.py
    ```

## Run for production (containerized)

1. Build container:
   ```bash
   make build
   ```
2. Run container
   `bash make run `
   Or, if you want to build and run in one command:

```bash
make all
```

## Check API

```bash
curl http://0.0.0.0:8000/api
```

If all is working properly, you'll get this output:

```json
{ "message": "Welcome to the IEMAP API" }
```

## Check documentation

Go to [http://0.0.0.0/api/docs](http://0.0.0.0/api/docs) to get a complete and interactive documentation on APIs, where you can test routes.

## ToDo

- [x] Add CORS policies
- [ ] Add GET routes
- [ ] Add POST routes
- [ ] Add PUT routes
- [ ] Add DELETE routes
- [x] Add GraphQL support
- [ ] Add Authentication

## Useful resources

### FASTAPI

[3 Ways to Handle Errors in FastAPI That You Need to Know](https://python.plainenglish.io/3-ways-to-handle-errors-in-fastapi-that-you-need-to-know-e1199e833039)  
[Python Asyncio, Requests, Aiohttp | Make faster API Calls](https://www.youtube.com/watch?v=nFn4_nA_yk8)  
[Implementing FastAPI Services – Abstraction and Separation of Concerns](https://camillovisini.com/article/abstracting-fastapi-services/)  
[Python API Tutorials](https://realpython.com/tutorials/api/)  
[FastAPI Tutorial - Building RESTful APIs with Python](https://www.youtube.com/watch?v=GN6ICac3OXY9)
[FASTAPI Project structure and versioning](https://christophergs.com/tutorials/ultimate-fastapi-tutorial-pt-8-project-structure-api-versioning/)  
[FAST API versioning using fastapi-versioning](https://medium.com/geoblinktech/fastapi-with-api-versioning-for-data-applications-2b178b0f843f)  
[How to save UploadFile in FastAPI(stackoverflow)](https://stackoverflow.com/questions/63580229/how-to-save-uploadfile-in-fastapi)
[Real world MongoDb Example APP (TO USE AS BASE)](https://github.com/markqiu/fastapi-mongodb-realworld-example-app)

## Logging

[Logging & Tracing in Python, FastApi, OpenCensus and Azure](https://dev.to/tomas223/logging-tracing-in-python-fastapi-with-opencensus-a-azure-2jcm)  
[Integrate Sentry to FastAPI](https://philstories.medium.com/integrate-sentry-to-fastapi-7250603c070f)  
[Color logs](https://pypi.org/project/colorlog/)
[How to color python logging](https://betterstack.com/community/questions/how-to-color-python-logging-output/)
[Logging and tracing](https://dev.to/tomas223/logging-tracing-in-python-fastapi-with-opencensus-a-azure-2jcm)

### GraphQL

[Integrate GraphQL into Python using Ariadne](https://blog.logrocket.com/integrate-graphql-python-using-ariadne/)  
[Getting started with GraphQL in Python with FastAPI and Ariadne](https://www.obytes.com/blog/getting-started-with-graphql-in-python-with-fastapi-and-ariadne)  
[Developing an API with FastAPI and GraphQL](https://testdriven.io/blog/fastapi-graphql/)  
[Build a GraphQL API with Subscriptions using Python, Asyncio and Ariadne](https://www.twilio.com/blog/graphql-api-subscriptions-python-asyncio-ariadne)  
[FASTAPI + GraphQL Ariadne Example](https://github.com/obytes/FastQL)
[GraphQL in the Python World](https://www.youtube.com/watch?v=p7VujaALaGQ)  
[Building An Instagram Clone With GraphQL and Auth0](https://auth0.com/blog/building-an-instagram-clone-with-graphql-and-auth0/)  
[GraphQL file uploads - evaluating the 5 most common approaches](https://wundergraph.com/blog/graphql_file_uploads_evaluating_the_5_most_common_approaches)  
[Fetching data](https://hasura.io/learn/graphql/vue/intro-to-graphql/2-fetching-data-queries/)  
[Hasura GrapQL tutorials](https://hasura.io/learn/)

### ML FASTAPI

[Deploying PyTorch Model to Production with FastAPI in CUDA-supported Docker](https://medium.com/@mingc.me/deploying-pytorch-model-to-production-with-fastapi-in-cuda-supported-docker-c161cca68bb8)

### MongoDB

[Getting Started with MongoDB and FastAPI](https://www.mongodb.com/developer/quickstart/python-quickstart-fastapi/)

### Deployment

[direnv – unclutter your .profile](https://direnv.net/)  
[UVICORN deployment](https://www.uvicorn.org/deployment/)  
[FASTAPI + NGINX + SUPERVISOR](https://medium.com/@travisluong/how-to-deploy-fastapi-with-nginx-and-supervisor-41f70f7fd943)  
[FASTAPI on NGINX UNIT](https://levelup.gitconnected.com/deploying-an-asynchronous-fastapi-on-nginx-unit-b038288bec5)
[FASTAPI + NGINX + PM2](https://www.travisluong.com/how-to-deploy-fastapi-with-nginx-and-pm2/)  
[Deploy FastAPI with Hypercorn HTTP/2 ASGI](https://levelup.gitconnected.com/deploy-fastapi-with-hypercorn-http-2-asgi-8cfc304e9e7a)
[Poetry]

#### Pydantic

> to generate a Pydantic model from a JSON schema use
> `datamodel-codegen --input schema_db.json --input-file-type jsonschema --output model_iemap.py`
> a schema can be generated online from a JSON file using:
> [Free Online JSON to JSON Schema Converte](https://www.liquid-technologies.com/online-json-to-schema-converter)  
> [JSON SCHEMA TOOL](https://www.jsonschema.net/home)  
> [Tools to generate json schema](https://stackoverflow.com/questions/7341537/tool-to-generate-json-schema-from-json-data)  
>  [PyDantic datamodel code generator](https://pydantic-docs.helpmanual.io/datamodel_code_generator/)

#### POETRY

[Dependency Management With Python Poetry](https://realpython.com/dependency-management-python-poetry/#add-poetry-to-an-existing-project)  
[PyBites Python Poetry Training](https://www.youtube.com/watch?v=G-OAVLBFxbw)
[Python projects with Poetry and VSCode. Part 2](https://www.pythoncheatsheet.org/blog/python-projects-with-poetry-and-vscode-part-2/)
