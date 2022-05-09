import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from datetime import datetime
from os import getcwd, path
from logging.config import dictConfig
from fastapi import FastAPI, Request, Response, status, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware

# from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

# Initialize Sentry remote error tracking
sentry_sdk.init(
    "https://b7d66adc74fd443da385f61725111863@o1111757.ingest.sentry.io/6381392",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,
)
# import routes from a specific version
from api.api_v1.api import router as api_router

# import configuration
from core.config import Config

# from core.errors import http_422_error_handler, http_error_handler
from db.mongodb_utils import close_mongo_connection, connect_to_mongo

# loads logging configuration
from core.log_config import logging_config

# configure logging using a dictionary from core.log_config
dictConfig(logging_config)


# define FASTAPI application
app = FastAPI(title=Config.app_name)
# ADD SENTRY ASGI MIDDLEWARE, works fine with FastAPI
app.add_middleware(SentryAsgiMiddleware)

# GLOBAL ERROR HANDLING
# async def catch_exceptions_middleware(request: Request, call_next):
#     try:
#         return await call_next(request)
#     except Exception:
#         # you probably want some kind of logging here
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


# Alternative approach using a custom middleware
# @app.middleware("http")
# async def sentry_exception(request: Request, call_next):
#     try:
#         response = await call_next(request)
#         return response
#     except Exception as e:
#         with sentry_sdk.push_scope() as scope:
#             scope.set_context("request", request)
#             # user_id = "database_user_id"  # when available
#             scope.user = ({"ip_address": request.client.host},)  # , "id": user_id}
#             sentry_sdk.capture_exception(e)
#         raise e


app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.allowed_hosts,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

# app.add_exception_handler(HTTPException, http_error_handler)
# app.add_exception_handler(HTTP_422_UNPROCESSABLE_ENTITY, http_422_error_handler)


# actualy add routes
app.include_router(api_router, prefix=Config.api_v1_str)

# TO SERVE FILES
@app.api_route("/file/{name_file}", methods=["GET"])
def get_file(name_file: str):
    file_full_path = getcwd() + "/uploaded/" + name_file
    if path.exists(file_full_path):
        return FileResponse(path=getcwd() + "/uploaded/" + name_file)
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


if __name__ == "__main__":
    # Use this for debugging purposes only
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8001, log_level="info", reload=True)
