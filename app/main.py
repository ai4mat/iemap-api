import uvicorn
from log_config import logging_config
from dotenv import dotenv_values

config = {
    **dotenv_values(".env.shared"),  # load shared development variables
    **dotenv_values(".env.secret"),  # load sensitive variables
    # **os.environ,  # override loaded values with environment variables
}
HOST = config["HOST"]
PORT = int(config["PORT"]) if config["PORT"].isdigit() else 8000

if __name__ == "__main__":
    uvicorn.run("server.app:app", host=HOST, port=PORT, reload=True)