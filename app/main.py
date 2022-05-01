from datetime import datetime
from logging.config import dictConfig
from fastapi import FastAPI, Request
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

# import routes from a specific version
from api.api_v1.api import router as api_router

# import configuration
from core.config import Config
from core.errors import http_422_error_handler, http_error_handler
from db.mongodb_utils import close_mongo_connection, connect_to_mongo

# loads logging configuration
from core.log_config import logging_config

# configure logging using a dictionary from core.log_config
dictConfig(logging_config)

# define FASTAPI application
app = FastAPI(title=Config.app_name)


app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.allowed_hosts,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

app.add_exception_handler(HTTPException, http_error_handler)
app.add_exception_handler(HTTP_422_UNPROCESSABLE_ENTITY, http_422_error_handler)


# actualy add routes
app.include_router(api_router, prefix=Config.api_v1_str)


# CATCH ALL ROUTE IT NEEDS TO BE LAST
# @app.api_route("/{path_name:path}", methods=["GET"])
# async def catch_all(request: Request, path_name: str):
#     return {
#         "request_method": request.method,
#         "path_name": path_name,
#         "message": "Reply from IEMAP API at " +
#         #  naturaltime(date=datetime.now())
#         datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
#     }


if __name__ == "__main__":
    # Use this for debugging purposes only
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8001, log_level="info", reload=True)
