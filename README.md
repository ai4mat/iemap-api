# IEMAP RESTful/GraphQL API

This API allow you to do some CRUD operation with RESTful methods over the Mission Innovation mongoDB.

## Configure

Use the `env.sample` to setup your mongoDB URI and save it as `.env`.

## Run for development (locally)

1. Get the environment varibales:
   ```bash
   export $(xargs < .env)
   ```
2. Install virtualenv:
   ```bash
   python3 -m venv $ENV_BASE_DIR/$ENVIRONMENT_NAME
   cd $ENV_BASE_DIR; virtualenv $ENVIRONMENT_NAME
   cd <path/to/>/opendigitalheritage-api
   pip install -r requirements.txt
   ```
   where:
   - $ENV_BASE_DIR: virtual envs folder
   - $ENVIRONMENT_NAME: your virtual env name
3. Run the app:
   ```bash
   python app/main.py
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
- [ ] Add GraphQL support
- [ ] Add Authentication

## Useful resources

[3 Ways to Handle Errors in FastAPI That You Need to Know](https://python.plainenglish.io/3-ways-to-handle-errors-in-fastapi-that-you-need-to-know-e1199e833039)  
[Python Asyncio, Requests, Aiohttp | Make faster API Calls](https://www.youtube.com/watch?v=nFn4_nA_yk8)  
[Implementing FastAPI Services – Abstraction and Separation of Concerns](https://camillovisini.com/article/abstracting-fastapi-services/)  
[Logging & Tracing in Python, FastApi, OpenCensus and Azure](https://dev.to/tomas223/logging-tracing-in-python-fastapi-with-opencensus-a-azure-2jcm)  
[Python API Tutorials](https://realpython.com/tutorials/api/)  
[Integrate Sentry to FastAPI](https://philstories.medium.com/integrate-sentry-to-fastapi-7250603c070f)  
[Deploying PyTorch Model to Production with FastAPI in CUDA-supported Docker](https://medium.com/@mingc.me/deploying-pytorch-model-to-production-with-fastapi-in-cuda-supported-docker-c161cca68bb8)  
[Getting Started with MongoDB and FastAPI](https://www.mongodb.com/developer/quickstart/python-quickstart-fastapi/)  
[direnv – unclutter your .profile](https://direnv.net/)  
[Integrate GraphQL into Python using Ariadne](https://blog.logrocket.com/integrate-graphql-python-using-ariadne/)  
[Getting started with GraphQL in Python with FastAPI and Ariadne](https://www.obytes.com/blog/getting-started-with-graphql-in-python-with-fastapi-and-ariadne)
