# IEMAP RESTful/GraphQL API

## General Informations

This API allow you to do some CRUD operation with RESTful methods over the Mission Innovation mongoDB.

This API can run in _development mode_ in you local machine or deployed as containerized _production-ready_ service on your server and/or on common public cloud providers.

### Official site

You can find the last working API version on the official site: [ai4mat.enea.it](https://ai4mat.enea.it)

### Official documentation

All routes are available on [`/docs`](https://ai4mat.enea.it/docs) or [`/redoc`](https://ai4mat.enea.it/redoc) paths with Swagger or ReDoc.

## Project structure

Files related to application are in the `app` directory. Application parts are:

- models: pydantic models that used in crud or handlers
- crud: CRUD for types from models (create new user/article/comment, check if user is followed by another, etc)
- db: db specific utils
- core: some general components (jwt, security, configuration)
- api: handlers for routes
- main.py: FastAPI application instance, CORS configuration and api router including

## Installation

### Get the code

First of all you need to get the code:

```
git clone https://github.com/ai4mat/mi-api.git
```

and jump to its folder:

```bash
cd mi-api
```

### Make some configurations

You first need to setup configurations into the environments file. Copy the `env.sample` into `.env` and edit this file for each variable.

### Start for development

#### 1 - Export the variables

First of all you need to export variables into the environment with:

```bash
export $(xargs < .env)
```

After that you need to create the python environment. You can choose to use `pip` or `poetry`.

#### 2a - Setup python environment with pip

Create the virtualenv (assuming you have python 3.X) and activate it:

```bash
python3 -m venv <your-virtual-env>
source <your-virtual-env>/bin/activate
```

Then install requirements:

```bash
pip install -r requirements
```

#### 2b - Setup python environment with poetry

Install `poetry`:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Run the following commands to bootstrap your environment with `poetry`:

```bash
poetry install
poetry shell
```

#### 3 - Run the server

Now you're ready to start the API just with:

```bash
cd app/
uvicorn main:app --reload
```

### Run as container (Producion)

#### 0 - Prerequisites

In the following we are assuming that you can manage docker with a non-root user. To do so, run the following commands:

```bash
sudo groupadd docker
sudo usermod -aG docker $USER
```

You had created the `docker` group first and then added your user to it. This way now you can build, run and stop containers with your user, without worrying about `sudo`.

#### 1 - Configuration

Add this to your server `.bashrc` or `.profile`:

```bash
export FILESDIR=<absoloute path where uploaded files are stored>
```

to set this variable both inside and outside container.

#### 2 - Build image and run container

Run the following command to build the image and run the container:

```bash
make all
```

> #### Note 1: Commands list
>
> To simplify container managment, a `Makefile` is provided. In the following are summarized all the available commands.
>
> | Action                                                       | `command`    |
> | :----------------------------------------------------------- | :----------- |
> | Build and run                                                | `make all`   |
> | Build image                                                  | `make build` |
> | Run container with FS                                        | `make run`   |
> | Stop container                                               | `make stop`  |
> | Start container                                              | `make start` |
> | Kill (stop & remove) container)                              | `make kill`  |
> | Clean (remove eventually dead containers and remove images)) | `make clean` |

> #### Note 2: Run multiple containers
>
> As said before, you can run mutliple container on the same server, but you need to set ports. To do so, you need to run the following command:
>
> ```bash
> make HOST_PORT=<port> run
> ```

#### 3 - Configure NGINX as reverse proxy

Create a new virtual host in your `/etc/nginx/sites-available` folder and add the following configuration (supposing you are running with SSL/TLS encryption):

```bash
server {
    listen 80;
    server_name <your-domain-name>;
    return 301 https://$server_name$request_uri;
}
server {
    listen 443 ssl;
    server_name <your-domain-name>;
    ssl_certificate /etc/letsencrypt/live/<your-domain-name>/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/<your-domain-name>/privkey.pem;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-NginX-Proxy true;
        proxy_redirect off;
        proxy_pass_request_headers on;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

#### 3 Bis - Configure NGINX as load balancer

If you're running multiple containers on the same server, you can configure NGINX as load balancer. To do so, you need to create a new virtual host in your `/etc/nginx/sites-available` folder and add the following configuration:

```bash
upstream backend {
    least_conn;
    server 127.0.0.1:<port1>;
    server 127.0.0.1:<port2>;
    ...
}
server {
    listen 80;
    server_name <your-domain-name>;
    return 301 https://$server_name$request_uri;
}
server {
    listen 443 ssl;
    server_name <your-domain-name>;
    ssl_certificate /etc/letsencrypt/live/<your-domain-name>/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/<your-domain-name>/privkey.pem;
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-NginX-Proxy true;
        proxy_redirect off;
        proxy_pass_request_headers on;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Please note that we have configured the load balancer with the _Least connections_ algorithm. This means that the server with the least connections will be used. If you want to use the _Round-Robin_ algorithm, you can change the `least_conn` in the `upstream` definition to `round_robin`.

#### 4 - Check and restart NGINX

Check the configuration and activate the new virtual host:

```bash
sudo nginx -t
```

If the check is ok, then create the symbolic link into the `/etc/nginx/sites-enabled` folder:

```bash
ln -s /etc/nginx/sites-available/<your-vhost-name> /etc/nginx/sites-enabled/<your-vhost-name>
```

Then restart the server:

```bash
systemctl restart nginx
```

### Check API

- 1a- Check if the API is running locally

```bash
curl http://localhost:8000
```

- 1b- Check if the API is running on the server (with SSL/TLS encryption)

```bash
curl https://<server-hostname>
```

- 2- Expected behavior
  If all is working properly, you'll get this output:

```json
{
  "request_method": "GET",
  "path_name": "",
  "message": "Reply from IEMAP API at <current time and date>"
}
```

# Check documentation

Go to [http://0.0.0.0/api/docs](http://0.0.0.0/api/docs) to get a complete and interactive documentation on APIs, where you can test routes.

# ToDo

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
[JETBRAIN - Developing FastAPI Application using K8s & AWS](https://www.jetbrains.com/pycharm/guide/tutorials/fastapi-aws-kubernetes/introduction/)  
[Python API Development - Comprehensive Course for Beginners (19 hours)](https://www.youtube.com/watch?v=0sOvCWFmrtA)  
[FASTAPI Playlist ITALIANO](https://www.youtube.com/watch?v=17pKUjh5oj0&list=PLyaoAB2kb_ZFSo7IMOkWdZKJqvsj4dwV5)  
[Modern Python through FastAPI and friends. Sebastián Ramírez.](https://www.youtube.com/watch?v=37CcB2GBdlY)  
[Strategies for limiting upload file size](https://github.com/tiangolo/fastapi/issues/362)  
[Catch `Exception` in fast api globally](https://stackoverflow.com/questions/61596911/catch-exception-in-fast-api-globally)  
[The Simplest Guide to FastAPI Dependency Injection using Depends](https://progressivecoder.com/fastapi-dependency-injection-using-depends/)  
[FASTAPI error running UVICORN](https://stackoverflow.com/questions/60819376/fastapi-throws-an-error-error-loading-asgi-app-could-not-import-module-api)  
[5 Advanced Features of FastAPI You Should Try](https://levelup.gitconnected.com/5-advance-features-of-fastapi-you-should-try-7c0ac7eebb3e)

### JWT Authentication

[Securing FastAPI with JWT Token-based Authentication](https://testdriven.io/blog/fastapi-jwt-auth/)
[Fast API JWT Authentication with the FastAPI-JWT-Auth Extension](https://www.youtube.com/watch?v=1y4Nk4gH53Y)
[Adding Authentication to Your FARM Stack App](https://www.mongodb.com/developer/how-to/FARM-Stack-Authentication/)  
[FASTAPI-USERS](https://fastapi-users.github.io/fastapi-users/10.0/configuration/authentication/)

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
[Knowledge Graph App in 15min](https://levelup.gitconnected.com/knowledge-graph-app-in-15min-c76b94bb53b3)

### ML FASTAPI

[Deploying PyTorch Model to Production with FastAPI in CUDA-supported Docker](https://medium.com/@mingc.me/deploying-pytorch-model-to-production-with-fastapi-in-cuda-supported-docker-c161cca68bb8)

### MongoDB

[Getting Started with MongoDB and FastAPI](https://www.mongodb.com/developer/quickstart/python-quickstart-fastapi/)  
[FASTAPI + Motor](https://testdriven.io/blog/fastapi-mongo/)  
[Check MongoDB is running](https://kb.objectrocket.com/mongo-db/check-if-a-mongodb-server-is-running-using-the-pymongo-python-driver-643)
[FASTAPI Contrib](https://fastapi-contrib.readthedocs.io/en/latest/)
[MongoDB Pagination](https://medium.com/swlh/mongodb-pagination-fast-consistent-ece2a97070f3)
[Paging with the Bucket Pattern - Part 1](https://www.mongodb.com/blog/post/paging-with-the-bucket-pattern--part-1)  
[Paging with the Bucket Pattern - Part 2](https://www.mongodb.com/blog/post/paging-with-the-bucket-pattern--part-2)
[7 ways to counts documents in MongoDB](https://database.guide/7-ways-to-count-documents-in-mongodb/)  
[MongoDB Pagination, Fast & Consistent](https://medium.com/swlh/mongodb-pagination-fast-consistent-ece2a97070f3)

### Deployment

[direnv – unclutter your .profile](https://direnv.net/)  
[UVICORN deployment](https://www.uvicorn.org/deployment/)  
[FASTAPI + NGINX + SUPERVISOR](https://medium.com/@travisluong/how-to-deploy-fastapi-with-nginx-and-supervisor-41f70f7fd943)  
[FASTAPI on NGINX UNIT](https://levelup.gitconnected.com/deploying-an-asynchronous-fastapi-on-nginx-unit-b038288bec5)
[FASTAPI + NGINX + PM2](https://www.travisluong.com/how-to-deploy-fastapi-with-nginx-and-pm2/)  
[Deploy FastAPI with Hypercorn HTTP/2 ASGI](https://levelup.gitconnected.com/deploy-fastapi-with-hypercorn-http-2-asgi-8cfc304e9e7a)

#### Pydantic

> to generate a Pydantic model from a JSON schema use:

> `datamodel-codegen --input schema_db.json --input-file-type jsonschema --output model_iemap.py`

> a schema can be generated online from a JSON file using:  
> [Free Online JSON to JSON Schema Converte](https://www.liquid-technologies.com/online-json-to-schema-converter)  
> [JSON SCHEMA TOOL](https://www.jsonschema.net/home)  
> [Tools to generate json schema](https://stackoverflow.com/questions/7341537/tool-to-generate-json-schema-from-json-data)  
>  [PyDantic datamodel code generator](https://pydantic-docs.helpmanual.io/datamodel_code_generator/)  
> [Pydantic](https://pydantic.org/)  
> [Pydantic Video Tutorial](https://youtu.be/Vj-iU-8_xLs)  
> [Validators vs Custom data types](https://towardsdev.com/pydantic-validators-v-s-custom-data-type-2c65c6402829)

#### POETRY

[Dependency Management With Python Poetry](https://realpython.com/dependency-management-python-poetry/#add-poetry-to-an-existing-project)  
[PyBites Python Poetry Training](https://www.youtube.com/watch?v=G-OAVLBFxbw)
[Python projects with Poetry and VSCode. Part 2](https://www.pythoncheatsheet.org/blog/python-projects-with-poetry-and-vscode-part-2/)

#### SENTRY

[Integrate Sentry to FastAPI](https://philstories.medium.com/integrate-sentry-to-fastapi-7250603c070f)
[Sentry ASGI Middleware for FASTAPI example](https://coveralls.io/builds/37501559/source?filename=app%2Fmain.py#L58)

#### JINJA2 templates (FORMS)

[How to Set Up a HTML App with FastAPI, Jinja, Forms & Templates](https://eugeneyan.com/writing/how-to-set-up-html-app-with-fastapi-jinja-forms-templates/)  
[Forms and File Uploads with FastAPI and Jinja2](https://www.youtube.com/watch?v=L4WBFRQB7Lk)

## Credits

- Sergio Ferlito ([sergio.ferlito@enea.it](sergio.ferlito@enea.it)) for the development and optimization of the API.
- Marco Puccini ([marco.puccini@enea.it](marco.puccini@enea.it)) for the initial idea, the first implementation and the DevOps ativities.
- Claudio Ronchetti ([claudio.ronchetti@enea.it](claudio.ronchetti@enea.it)) for data model and general support.
