from datetime import datetime
from fastapi import FastAPI, Request
# from humanize import naturaltime
from server.routes.items import router as ItemRouter

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(openapi_url="/api/openapi.json",
              docs_url="/api/docs",
              redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ItemRouter, tags=["Items"], prefix="/api")


@app.get("/api", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the IEMAP API"}


@app.api_route("/{path_name:path}", methods=["GET"])
async def catch_all(request: Request, path_name: str):
    return {
        "request_method":
        request.method,
        "path_name":
        path_name,
        "message":
        "Reply from Open Digital Heritage API at " +
        #  naturaltime(date=datetime.now())
        datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }
