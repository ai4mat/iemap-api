import enum
import hashlib
import json
from os import rename, path
import aiofiles
from pathlib import Path
from math import modf, trunc
from bson.objectid import ObjectId
from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException, UploadFile, status
from pydantic import BaseModel
from starlette.responses import JSONResponse
from core.parsing import parse_cif
from core.config import Config


def create_aliased_response(model: BaseModel) -> JSONResponse:
    return JSONResponse(content=jsonable_encoder(model, by_alias=True))


def hash_file(filename: str) -> str:
    """This function returns the SHA-1 hash
    of the file passed into it

    Args:
        filename (str): file full name (including extention) to hash

    Returns:
        str: SHA-1 hash of the file full name
    """

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


def truncate(number: float, digits: int) -> float:
    """Truncate number to given number of digits

    Args:
        number (float): number to truncate
        digits (int): desidered number of digits

    Returns:
        float: truncated number
    """
    stepper = 10.0**digits
    return trunc(stepper * number) / stepper


# Enum for size units
class SIZE_UNIT(enum.Enum):
    BYTES = 1
    KB = 2
    MB = 3
    GB = 4


def convert_unit(size_in_bytes: float, unit: SIZE_UNIT) -> float:
    """Convert the size from bytes to other units like KB, MB or GB

    Args:
        size_in_bytes (float): file size in bytes
        unit (SIZE_UNIT): desidered units

    Returns:
        float: converted size in desidered units
    """
    if unit == SIZE_UNIT.KB:
        return size_in_bytes / 1024
    elif unit == SIZE_UNIT.MB:
        return size_in_bytes / (1024 * 1024)
    elif unit == SIZE_UNIT.GB:
        return size_in_bytes / (1024 * 1024 * 1024)
    else:
        return size_in_bytes


def get_str_file_size(file_name: str, size_type: SIZE_UNIT = None) -> str:
    """Get file in size in given unit like KB, MB or GB

    Args:
        file_name (str): file full path
        size_type (SIZE_UNIT, optional): preferred size format (default to None).

    Returns:
        str: file size in KB, MB or GB
    """
    size = path.getsize(file_name)
    if size_type:
        size_converted = convert_unit(size, size_type)
        return str(truncate(size_converted, 3)) + " " + size_type.name
    for size_type in [e for e in SIZE_UNIT]:
        size_converted = convert_unit(size, size_type)
        size_truncated = truncate(size_converted, 3)
        _, int_part = modf(size_truncated)

        if len(str(int(int_part))) < 3:
            return str(size_truncated) + " " + size_type.name


async def save_file(file: UploadFile, upload_dir: str):
    """Save file to upload directory

    Args:
        file (UploadFile): file to save
        upload_dir (str): base dir where to save file

    Raises:
        HTTPException: HTTP Error 400 if file is not valid
        HTTPException: HTTP Error 500 if file cannot be saved

    Returns:
        dict:{
            "file_hash" (str): hash of the file saved,
            "file_size" (str): file size in human readable format,
            "file_ext" (str): file extension,
        }
    """
    if file.content_type not in Config.allowed_mime_types:
        raise HTTPException(400, detail="Invalid document type")
    # retrieve file extension
    file_ext = file.filename.split(".")[-1]

    # get directory path for uploaded_dir (abs path)
    base_dir = Path(path.dirname(path.realpath(__file__))).parent.parent / upload_dir

    # path for file to write on file system
    file_to_write = path.join(base_dir, file.filename)

    # print(f"{upload_dir}/{file.filename}")
    # print(file_to_write)

    # write file to disk in chunks
    file_hash, str_file_size = None, None
    try:
        with open(file_to_write, "wb+") as file_object:
            # SLOWER VERSION BUT DOES NOT LOAD ENTIRE FILE IN MEMORY
            async with aiofiles.open(file_to_write, "wb") as out_file:
                while content := await file.read(1024 * 1024):  # async read chunk
                    await out_file.write(content)  # async write chunk
            file_hash = hash_file(file_to_write)
            # full path of new file name
            new_file_name = path.join(base_dir, f"{file_hash}.{file_ext}")
            rename(file_to_write, new_file_name)
        str_file_size = get_str_file_size(new_file_name)
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return file_hash, str_file_size, file_ext


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


def get_dir_uploaded(upload_dir: str) -> str:
    """Get full path of upload directory

    Args:
        upload_dir (str): directory name where to save file

    Returns:
        str: full path of upload directory
    """
    return (
        Path.cwd().parent / upload_dir
        if "app" in str(Path.cwd()).split("/")
        else Path.cwd() / upload_dir
    )


# https://www.programiz.com/python-programming/examples/hash-file
