import enum
import hashlib
import json
import os
from math import modf, trunc
from bson.objectid import ObjectId
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from starlette.responses import JSONResponse


def create_aliased_response(model: BaseModel) -> JSONResponse:
    return JSONResponse(content=jsonable_encoder(model, by_alias=True))


def hash_file(filename):
    """ "This function returns the SHA-1 hash
    of the file passed into it"""

    # make a hash object
    h = hashlib.sha1()

    # open file for reading in binary mode
    with open(filename, "rb") as file:

        # loop till the end of the file
        chunk = 0
        while chunk != b"":
            # read only 1024 bytes at a time
            chunk = file.read(1024)
            h.update(chunk)

    # return the hex representation of digest
    return h.hexdigest()


def truncate(number, digits) -> float:
    stepper = 10.0**digits
    return trunc(stepper * number) / stepper


# Enum for size units
class SIZE_UNIT(enum.Enum):
    BYTES = 1
    KB = 2
    MB = 3
    GB = 4


def convert_unit(size_in_bytes, unit):
    """Convert the size from bytes to other units like KB, MB or GB"""
    if unit == SIZE_UNIT.KB:
        return size_in_bytes / 1024
    elif unit == SIZE_UNIT.MB:
        return size_in_bytes / (1024 * 1024)
    elif unit == SIZE_UNIT.GB:
        return size_in_bytes / (1024 * 1024 * 1024)
    else:
        return size_in_bytes


def get_str_file_size(file_name, size_type=None):
    """Get file in size in given unit like KB, MB or GB"""
    size = os.path.getsize(file_name)
    if size_type:
        size_converted = convert_unit(size, size_type)
        return str(truncate(size_converted, 3)) + " " + size_type.name
    for size_type in [e for e in SIZE_UNIT]:
        size_converted = convert_unit(size, size_type)
        size_truncated = truncate(size_converted, 3)
        _, int_part = modf(size_truncated)

        if len(str(int(int_part))) < 3:
            return str(size_truncated) + " " + size_type.name


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


# https://www.programiz.com/python-programming/examples/hash-file
