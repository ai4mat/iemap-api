import os

from dotenv import load_dotenv, find_dotenv, dotenv_values
from starlette.datastructures import CommaSeparatedStrings, Secret

# from databases import DatabaseURL

API_V1_STR = "/api"

JWT_TOKEN_PREFIX = "Token"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # one week

# load_dotenv(find_dotenv(raise_error_if_not_found=True))

path_dot_env = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../.env")

config = {
    **dotenv_values(path_dot_env),  # load shared development variables
    # find_dotenv(raise_error_if_not_found=True, usecwd=False)
    # ),  # load shared development variables
    # **dotenv_values(".env.secret"),  # load sensitive variables
    # **os.environ,  # override loaded values with environment variables
}


class Config(object):
    # mongodb
    mongo_db = config["MONGO_DATABASE"]
    mongo_uri = config["MONGO_URI"]
    mongo_coll = config["MONGO_COLLECTION"]
    mongo_coll_users = config["MONGO_COLLECTION_USERS"]
    max_conn = int(os.getenv("MAX_CONNECTIONS_COUNT", 10))
    min_conn = int(os.getenv("MIN_CONNECTIONS_COUNT", 10))
    jwt_secret_key = config["JWT_SECRET_KEY"]
    jwt_algorithm = config["JWT_ALGORITHM"]
    jwt_token_prefix = "Token"
    access_token_expire_minutes = 60 * 24 * 7  # one week
    app_name = config["APP_NAME"]
    allowed_hosts = CommaSeparatedStrings(config.get("ALLOWED_HOSTS", "*"))
    api_v1_str = config["API_V1_STR"]
    files_dir = config["FILESDIR"]


# MONGODB_URL = os.getenv("MONGODB_URL", "")  # deploying without docker-compose
# if not MONGODB_URL:
#     MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
#     MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
#     MONGO_USER = os.getenv("MONGO_USER", "admin")
#     MONGO_PASS = os.getenv("MONGO_PASSWORD", "markqiu")
#     MONGO_DB = os.getenv("MONGO_DB", "fastapi")

#     MONGODB_URL = DatabaseURL(
#         f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}"
#     )
# else:
#     MONGODB_URL = DatabaseURL(MONGODB_URL)
