import datetime
import json
import logging
import hashlib
from typing import Optional
import aiofiles

from bson.objectid import ObjectId as BsonObjectId
from core.parsing import parse_cif
from core.utils import hash_file
from os import getcwd, remove, rename, path
from dotenv import dotenv_values

from fastapi import (
    APIRouter,
    Depends,
    Response,
    status,
    File,
    UploadFile,
    HTTPException,
)
from fastapi.responses import JSONResponse
from db.mongodb import AsyncIOMotorClient, get_database
from crud.projects import add_project, list_projects
from models.iemap import newProject as NewProjectModel, ObjectIdStr

config = {
    **dotenv_values(".env"),  # load shared development variables
}
upload_dir = config["FILESDIR"]

logger = logging.getLogger("ai4mat")

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

router = APIRouter()


# http://0.0.0.0:8001/api/v1/project/list/10/1
@router.get(
    "/project/list/",
    tags=["projects"],
    status_code=status.HTTP_200_OK,
    # response_model=ProjectModel,
)
async def show_projects(
    db: AsyncIOMotorClient = Depends(get_database),
    project: NewProjectModel = None,
    skip: Optional[int] = 0,
    limit: Optional[int] = 10,
):

    # id is a ObjectId
    result = await list_projects(db, project, limit, skip)
    # content=json.dumps(dict(project), default=str)
    # JSONResponse(content=json.dumps(dict(project), default=str))
    return {"skip": skip, "limit": limit, "data": result}


# http://0.0.0.0:8001/api/v1/project/add
@router.post(
    "/project/add",
    tags=["projects"],
    status_code=status.HTTP_200_OK,
    # response_model=ProjectModel,
)
async def add_new_project(
    db: AsyncIOMotorClient = Depends(get_database),
    project: NewProjectModel = None,
):
    logger.info(f"add_new_project: {project.dict()}")
    # id is a ObjectId
    id = await add_project(db, project=project)
    # content=json.dumps(dict(project), default=str)
    # JSONResponse(content=json.dumps(dict(project), default=str))
    return {"inserted_id": str(id)}


# http://0.0.0.0:8001/api/v1/project/addfile/{project_id}
@router.post("/project/add/file/{project_id}", tags=["projects"])
async def create_upload_file(project_id: ObjectIdStr, file: UploadFile = File(...)):
    id_mongodb = BsonObjectId(project_id)
    # Check file MimeType
    if file.content_type not in allowed_mime_types:
        raise HTTPException(400, detail="Invalid document type")
    # if len(file) > 1000000:
    #     raise HTTPException(400, detail="File too large")
    # file_type
    file_ext = file.filename.split(".")[-1]

    file_to_write = f"{upload_dir}/{file.filename}"

    with open(file_to_write, "wb+") as file_object:

        # SLOWER VERSION BUT DOES NOT LOAD ENTIRE FILE IN MEMORY
        async with aiofiles.open(file_to_write, "wb") as out_file:
            while content := await file.read(1024 * 1024):  # async read chunk
                await out_file.write(content)  # async write chunk
        # content = file.file.read()
        structure, distinct_species, lattice = None, None, None
        if file_ext == "cif":
            structure, distinct_species, lattice = parse_cif(file_to_write)
        hash = hash_file(file_to_write)
        # h.update(content)
        # hash = h.hexdigest()
        # file_object.write(file.file.read())
        ext = file.filename.split(".")[-1]
        rename(file_to_write, f"{upload_dir}/{hash}.{ext}")

        return {"file_name": f"{file.filename}", "file_hash": f"{hash}"}
