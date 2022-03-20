from datetime import datetime
from fastapi import FastAPI, Request
from fastapi_versioning import VersionedFastAPI, version
# from humanize import naturaltime
from server.routes.items import router as ItemRouter
from server.routes.files import router as FilesRouter
from fastapi.middleware.cors import CORSMiddleware

from ariadne import make_executable_schema, load_schema_from_path, \
    snake_case_fallback_resolvers
from ariadne.asgi import GraphQL
from server.mutations import mutation
from server.queries import query
from server.subscriptions import subscription

from os.path import dirname, abspath, join

dirname = dirname(dirname(abspath(__file__)))

type_defs = load_schema_from_path(join(dirname, './graphql/schema.graphql'))

schema = make_executable_schema(type_defs, query, mutation, subscription,
                                snake_case_fallback_resolvers)

graphql_app = GraphQL(schema, debug=True)

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

# app.add_route('/graphql', graphql_app)
app.include_router(ItemRouter, tags=["Items"], prefix="/api")

app.include_router(FilesRouter, tags=["Files"], prefix="/api")


@app.get("/api", tags=["Root"])
# @version(1, 0)
async def read_root():
    return {"message": "Welcome to the IEMAP API"}


@app.get("/api", tags=["Root latest"])
# @version(1, 1)
async def read_root():
    return {"message": "Welcome to the IEMAP API LATEST"}


@app.api_route("/v1_0/{path_name:path}", methods=["GET"])
async def catch_all(request: Request, path_name: str):
    return {
        "request_method":
        request.method,
        "path_name":
        path_name,
        "message":
        "Reply from IEMAP API at " +
        #  naturaltime(date=datetime.now())
        datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }


# APPLY VERSIONING
app = VersionedFastAPI(app, default_version=(1, 0), enable_latest=True)
app.add_route('/graphql', graphql_app)
