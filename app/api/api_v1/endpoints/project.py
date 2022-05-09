import logging
import aiofiles
from typing import Optional
from bson.objectid import ObjectId as BsonObjectId
from core.parsing import parse_cif
from core.utils import get_str_file_size, hash_file
from os import rename, getcwd, path
from dotenv import dotenv_values

from fastapi import APIRouter, Depends, status, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from db.mongodb import AsyncIOMotorClient, get_database
from crud.projects import (
    add_project,
    list_project_properties_files,
    list_projects,
    add_property_file,
)
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
async def create_project_file(project_id: ObjectIdStr, file: UploadFile = File(...)):
    id_mongodb = BsonObjectId(project_id)
    # Check file MimeType
    if file.content_type not in allowed_mime_types:
        raise HTTPException(400, detail="Invalid document type")
    # retrieve file extension
    file_ext = file.filename.split(".")[-1]
    # file to write path
    file_to_write = f"{upload_dir}/{file.filename}"
    # write file to disk in chunks
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

        return {
            "file_name": f"{file.filename}",
            "file_hash": f"{hash}",
            "file_size": get_str_file_size(file_to_write),
        }


# http://0.0.0.0:8001/api/v1/project/add/file/?project_id=62752dd88856514dab27dd8e&property_name=H2o&property_type=2D
@router.post("/project/add/file/", tags=["projects"])
async def create_property_file(
    project_id: ObjectIdStr,
    property_name: str,
    property_type: str,
    file: UploadFile = File(...),
    db: AsyncIOMotorClient = Depends(get_database),
):
    id_mongodb = BsonObjectId(project_id)
    # Check file MimeType
    if file.content_type not in allowed_mime_types:
        raise HTTPException(400, detail="Invalid document type")
    # retrieve file extension
    file_ext = file.filename.split(".")[-1]
    # file to write path
    file_to_write = f"{upload_dir}/{file.filename}"
    # write file to disk in chunks
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

        new_file_name = f"{upload_dir}/{hash}.{file_ext}"
        rename(file_to_write, new_file_name)
        str_file_size = get_str_file_size(new_file_name)
        modified_count = await add_property_file(
            db, id_mongodb, hash, str_file_size, file_ext, property_name, property_type
        )
        if modified_count == 0:
            raise HTTPException(400, detail="File Not Found")
        return {
            "file_name": f"{file.filename}",
            "file_hash": f"{hash}",
            "file_size": str_file_size,
        }


@router.get("/files/{name_file}")
def get_file(name_file: str):

    file_path = f"{getcwd()}/{upload_dir}/{name_file}"
    isExisting = path.exists(file_path)
    if isExisting:
        content = FileResponse(file_path)
        return content
    else:
        return JSONResponse(content={"error": "file not found!"}, status_code=404)


# http://0.0.0.0:8001/api/v1/project/file/list
@router.get(
    "/project/file/list/",
    tags=["projects"],
)
async def create_property_file(
    affiliation: str,
    projectName: str,
    request: Request,
    db: AsyncIOMotorClient = Depends(get_database),
):
    list_files = await list_project_properties_files(db, affiliation, projectName)
    for doc in list_files:
        file_path = doc["file"]["hash"] + "." + doc["file"]["extention"]
        doc["file"]["url"] = str(request.base_url) + "file/" + file_path
    return list_files


# https://github.com/tiangolo/fastapi/issues/362
