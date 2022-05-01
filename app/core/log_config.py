LOG_LEVEL: str = "DEBUG"
FORMAT: str = "%(levelname)s: %(asctime)s - %(name)s -  - %(message)s"


logging_config = {
    "version": 1,  # mandatory field
    # if you want to overwrite existing loggers' configs
    "disable_existing_loggers": False,
    "formatters": {
        "basic": {
            "()": "uvicorn.logging.DefaultFormatter",
            "format": FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "colored": {
            "()": "colorlog.ColoredFormatter",
            "format": "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s",
        },
    },
    "handlers": {
        "console": {
            "formatter": "colored",  # "basic",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
            "level": LOG_LEVEL,
        }
    },
    "loggers": {
        "ai4mat": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            # "propagate": False
        }
    },
}
