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
    "application/x-zip-compressed",
    "application/zip-compressed",
    "application/octet-stream",
    "application/pdf",
    "text/plain",
    "chemical/x-cif",
    "application/vnd.multiad.creator.cif",  # .cif
    "text/x-markdown",
    "application/rtf",
    "application/doc",
    "application/msword",
    "application/rtf",
    "application/x-rtf",
    "application/x-soffice",
    "image/png",
    "image/jpeg",
    "image/bmp",
    "image/tiff",
    "text/richtext",
    "application/json",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
]

path_dot_env = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../.env")
# load environment variables
config = {
    **os.environ,
}
if os.path.exists(path_dot_env):
    # override loaded values with environment variables from .env file
    config = {
        **dotenv_values(path_dot_env),
    }


class Config(object):
    # mongodb
    app_port = int(config.get("PORT", 80))
    mongo_db = config["MONGO_DATABASE"]
    mongo_uri = config["MONGO_URI"]
    mongo_coll = config["MONGO_COLLECTION"]
    mongo_coll_users = config["MONGO_COLLECTION_USERS"]
    max_conn = int(os.getenv("MAX_CONNECTIONS_COUNT", 10))
    min_conn = int(os.getenv("MIN_CONNECTIONS_COUNT", 10))
    jwt_secret_key = config["JWT_SECRET_KEY"]
    jwt_algorithm = config["JWT_ALGORITHM"]
    jwt_token_prefix = "Token"
    jwt_lifetime = (
        int(config["JWT_LIFETIME"]) if config.get("JWT_LIFETIME") else 3600 * 24
    )  # 24h
    access_token_expire_minutes = 60 * 24 * 7  # one week
    app_name = config["APP_NAME"]
    allowed_hosts = CommaSeparatedStrings(config.get("ALLOWED_HOSTS", "*"))
    api_v1_str = config["API_V1_STR"]
    front_end = config["FRONTEND"]
    files_dir = config["FILESDIR"]
    files_chunk_size = int(config.get("FILES_CHUNK_SIZE", 1024 * 1024 * 10))
    allowed_mime_types = allowed_mime_types
    enable_onpremise_auth = bool(config["ENABLE_ONPREMISE_AUTH"] == "True")
    secrete_on_premise_auth = config["SECRET_ONPREMISE_AUTH"]
    smtp_server = config["SMTP_SERVER"]
    smtp_pwd = config["SMTP_PWD"]
    smtp_from = config["SMTP_FROM"]
