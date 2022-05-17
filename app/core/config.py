import os

from dotenv import load_dotenv, find_dotenv, dotenv_values
from starlette.datastructures import CommaSeparatedStrings, Secret

# from databases import DatabaseURL

API_V1_STR = "/api"

JWT_TOKEN_PREFIX = "Token"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # one week

# load_dotenv(find_dotenv(raise_error_if_not_found=True))

# https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types
allowed_mime_types = [
    "text/csv",
    # "application/zip",
    "application/octet-stream",  # .cif
    "application/pdf",
    "text/plain",
    "chemical/x-cif",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]

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
    allowed_mime_types = allowed_mime_types
