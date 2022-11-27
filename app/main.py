import mimetypes
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from datetime import datetime
from os import getcwd, path
from logging.config import dictConfig
from fastapi import FastAPI, Request, Depends, status, HTTPException
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from core.utils import get_dir_uploaded

# from starlette.exceptions import HTTPException
# from starlette.middleware.cors import CORSMiddleware

# from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

# Initialize Sentry remote error tracking
sentry_sdk.init(
    dsn="https://51844a09de0c494aaaa788de000153c9@o4504162406760448.ingest.sentry.io/4504162409578496",
    # "https://b7d66adc74fd443da385f61725111863@o1111757.ingest.sentry.io/6381392",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,
)
# import routes from a specific version
from api.api_v1.api import router as api_router

from api.on_premise_auth import router as on_premise_auth_router

# import configuration
from core.config import Config

# from core.errors import http_422_error_handler, http_error_handler
from db.mongodb_utils import close_mongo_connection, connect_to_mongo

# loads logging configuration
from core.log_config import logging_config

# configure logging using a dictionary from core.log_config
dictConfig(logging_config)


# NECESSARY TO HANDLE FASTAPI_USERS
from db.mongodb_utils import UserAuth
from models.users import fastapi_users

# define FASTAPI application
app = FastAPI(
    title="Mission Innovation IEMAP API",
    description="RESTful/GraphQL API for Mission Innovation - IEMAP stored data",
    version="1.1.1",
    terms_of_service="",
    contact={
        "name": "IEMAP API info",
        "url": "https://github.com/ai4mat/mi-api/",
        "email": "iemap-api@enea.it",
    },
    license_info={"name": "MIT", "url": "https://mit-license.org/"},
    # openapi_url="/openapi.json",
    # root_path="/iemap",
)
# ADD SENTRY ASGI MIDDLEWARE, works fine with FastAPI
app.add_middleware(SentryAsgiMiddleware)

# GLOBAL ERROR HANDLING
# async def catch_exceptions_middleware(request: Request, call_next):
#     try:
#         return await call_next(request)
#     except Exception:
#         # you probably want some kind of logging here195f4160af4f
#         return Response(
#             content={"Watch out!!"},
#             media_type="application/json",
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         )
# app.middleware("http")(catch_exceptions_middleware)


@app.exception_handler(Exception)
async def validation_exception_handler(request, err):
    local = request.client.host == "127.0.0.1"
    message = "Something went wrong!!"
    if local:
        message = f"Failed to execute: {request.method}: {request.url}"
        return JSONResponse(
            status_code=400, content={"message": message, "error": str(err)}
        )
    # Change here to LOGGER
    return JSONResponse(status_code=400, content={"message": message})


# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=Config.allowed_hosts,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)


# actualy add routes
app.include_router(api_router, prefix=Config.api_v1_str)


if Config.enable_onpremise_auth:
    app.include_router(on_premise_auth_router)

# Jinja2 templates for static files
# MOUNT A STATIC DIR IS NECESSARY!!!!
app.mount(
    "/static",
    StaticFiles(directory=path.join(path.dirname(path.realpath(__file__)), "./static")),
    name="static",
)
templates = Jinja2Templates(
    directory=path.join(path.dirname(path.realpath(__file__)), "./templates")
)


@app.get("/items/{id}", response_class=HTMLResponse)
async def read_item(request: Request, id: str):
    return templates.TemplateResponse("item.html", {"request": request, "id": id})


@app.get("/form", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})


current_user = fastapi_users.current_user(verified=True)
# TO SERVE FILES
# http://0.0.0.0:8001/file/hashfile
@app.api_route("/file/{name_file}", methods=["GET"])
def get_file(
    name_file: str,
    # comment row below to remove authentication for this endpoint
    user: UserAuth = Depends(current_user),
):
    """Download file from server

    Args:
        name_file (str): file name expressed as <hash>.<extension>

    Raises:
        HTTPException: HTTP_404_NOT_FOUND if file was not found

    Returns:
        stream: binary data of file
    """

    upload_dir = Config.files_dir
    base_dir = get_dir_uploaded(upload_dir)
    # path for file to write on file system
    file_path = base_dir / name_file
    # print(file_path)
    isExisting = file_path.is_file()
    if isExisting:
        mtype, _ = mimetypes.guess_type(file_path)
        return FileResponse(file_path)  # , media_type=mtype)
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found!!"
        )


# CATCH ALL ROUTE IT NEEDS TO BE LAST
@app.api_route("/{path_name:path}", methods=["GET"])
async def catch_all(request: Request, path_name: str):
    return {
        "request_method": request.method,
        "path_name": path_name,
        "message": "Reply from IEMAP API at " +
        #  naturaltime(date=datetime.now())
        datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


# if __name__ == "__main__":
#     # Use this for debugging purposes only
#     import uvicorn

#     uvicorn.run(
#         "main:app",
#         host="0.0.0.0",
#         port=Config.app_port,
#         log_level="info",
#         reload=True,
#     )
