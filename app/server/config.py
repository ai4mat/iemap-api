import os

class Config(object):
    # mongodb
    mongo_db = os.getenv('MONGO_DATABASE')
    mongo_uri = os.getenv('MONGO_URI')