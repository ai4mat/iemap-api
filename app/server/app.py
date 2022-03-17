from datetime import datetime
from fastapi import FastAPI, Request
# from humanize import naturaltime
from server.routes.items import router as ItemRouter

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

app.add_route('/graphql', graphql_app)
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
        "Reply from IEMAP API at " +
        #  naturaltime(date=datetime.now())
        datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }
