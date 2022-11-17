import enum
import hashlib
import json
import logging
from os import path
from typing import Union

from sentry_sdk import capture_exception

logger = logging.getLogger("ai4mat")
# from aiofiles.os import rename, remove
import aiofiles
from os import rename, remove

from pathlib import Path, PosixPath
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
            chunk = file.read(Config.files_chunk_size)
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
                while content := await file.read(
                    Config.files_chunk_size
                ):  # async read chunk
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


def get_dir_uploaded(upload_dir: str) -> Path:
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


async def rename_file_with_its_hash(
    file_to_write: PosixPath, file_ext: str, upload_dir: str
) -> Union[str, None]:
    """Rename file with its hash if it already DOES NOT exists
       otherwise delete file (not yet renamed with its hash)

    Args:
        file_to_write (PosixPath): full path file to write
        file_ext (str): file extention to
        upload_dir (str): name folder where save data
    Returns:
        str|None: new file name (hash+original extention) or None if file yet existing (no overwrite allowed)

    """
    # compute file hashing (data saved in chunk)
    # hash computed after saving file with its original name
    try:
        hash = hash_file(file_to_write)
        # get new file name = HASH+extention
        new_file_name = get_dir_uploaded(upload_dir) / f"{hash}.{file_ext}"
        if not new_file_name.exists():
            # await rename(file_to_write, new_file_name)
            rename(file_to_write, new_file_name)
            return new_file_name
        else:
            # delete original file before returning None, i.e. no file uploaded
            # await remove(file_to_write)
            remove(file_to_write)
            return None
    except Exception as e:
        logger.error(e)
        capture_exception(e)


def get_value_float_or_str(x):
    """Get value as float or string
        first check if value can be correctly converted to float
        if not return it as string
        if None return it as is
    Args:
        x (str|float|None): value to convert

    Returns:
        str|float|None: value converted
    """
    if x == None:
        return None
    try:
        return float(x)
    except ValueError:
        return x


# https://www.programiz.com/python-programming/examples/hash-file
