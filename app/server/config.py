import os
from dotenv import dotenv_values

config = {
    **dotenv_values(".env.shared"),  # load shared development variables
    **dotenv_values(".env.secret"),  # load sensitive variables
    # **os.environ,  # override loaded values with environment variables
}


class Config(object):
    # mongodb
    mongo_db = config["MONGO_DATABASE"]
    mongo_uri = config['MONGO_URI']
    mongo_coll = config['MONGO_COLLECTION']
