# IEMAP RESTful/GraphQL API

## General Informations

This API allow you to do some CRUD operation with RESTful methods over the Mission Innovation mongoDB.

This API can run in _development mode_ in you local machine or deployed as containerized _production-ready_ service on your server and/or on common public cloud providers.

### Official site

You can find the last working API version on the official site: [ai4mat.enea.it](https://ai4mat.enea.it)

### Official documentation

All routes are available on [`/docs`](https://ai4mat.enea.it/docs) or [`/redoc`](https://ai4mat.enea.it/redoc) paths with Swagger or ReDoc.

## Project structure
All files related to the application are in the `app` directory into the following subfolders:
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


### Run as container (Production)
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
You can also run multiple containers from the same builded image. You need to build first and then run each container on different port. To do so, run the following command:
```bash
make build
```
And then run each container:
```bash
make HOST_PORT=<port> run
```
In the following a complete list of commands defined into the `Makefile`, to simplify container managment:
| Action | `command` |
|:---|:---|
| Build and run | `make all` |
| Build image | `make build` |
| Run container | `make run` |
| Stop container | `make stop` |
| Start container | `make start` |
| Kill (stop & remove) container) | `make kill` |
| Clean (remove eventually dead containers and remove images)) | `make clean` |

>Remeber: to get the list of running containers (with their IDs), run:
>```bash
>docker ps
>```

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

#### 1a - Check if the API is running locally
```bash
curl http://localhost:8000
``` 
#### 1b - Check if the API is running on the server (with SSL/TLS encryption)
```bash
curl https://<server-hostname>
```
#### 2 - Expected behavior
If all is working properly, you'll get this output:
```json
{
  "request_method": "GET",
  "path_name": "",
  "message": "Reply from IEMAP API at <current time and date>"
}
```

## Credits

- Sergio Ferlito ([sergio.ferlito@enea.it](sergio.ferlito@enea.it)) for the development and optimization of the API.
- Marco Puccini ([marco.puccini@enea.it](marco.puccini@enea.it)) for the initial idea, the first implementation and the DevOps ativities.
- Claudio Ronchetti ([claudio.ronchetti@enea.it](claudio.ronchetti@enea.it)) for data model and general support.
