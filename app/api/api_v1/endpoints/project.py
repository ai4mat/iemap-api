import json
import logging
from models.iemap import FileProject, ProjectFileForm, Property, Publication, fileType
import aiofiles
from typing import Optional
from bson.objectid import ObjectId as BsonObjectId
from core.parsing import parse_cif
from core.utils import get_str_file_size, hash_file, save_file
from os import rename, getcwd, path
from dotenv import dotenv_values, find_dotenv
from pydantic import Json
from fastapi import (
    APIRouter,
    Depends,
    status,
    File,
    Form,
    UploadFile,
    HTTPException,
    Request,
)
from fastapi.responses import JSONResponse, FileResponse
from db.mongodb import AsyncIOMotorClient, get_database
from crud.projects import (
    add_project,
    add_project_file,
    add_project_file_and_data,
    add_property,
    count_projects,
    find_all_project_paginated,
    list_project_properties_files,
    list_projects,
    add_property_file,
)
from models.iemap import (
    PropertyFile,
    PropertyForm,
    newProject as NewProjectModel,
    ObjectIdStr,
)

from core.config import Config

upload_dir = Config.files_dir

logger = logging.getLogger("ai4mat")


router = APIRouter()


# http://0.0.0.0:8001/api/v1/project/list/?page_size=1&page_number=3
# GET ALL PROJECTS PAGINATED (using skip & limit)
@router.get(
    "/project/list/",
    tags=["projects"],
    status_code=status.HTTP_200_OK,
    # response_model=ProjectModel,
)
async def show_projects(
    db: AsyncIOMotorClient = Depends(get_database),
    project: NewProjectModel = None,
    page_size: Optional[int] = 10,
    page_number: Optional[int] = 1,
):

    # id is a ObjectId
    n_docs = await count_projects(db)
    skip = page_size * (page_number - 1)
    page_tot = n_docs // page_size
    result = await list_projects(db, project, page_size, skip)

    return {
        "skip": skip,
        "page_size": page_size,
        "page_number": page_number,
        "page_tot": page_tot,
        "number_docs": n_docs,
        "data": result,
    }


# http://0.0.0.0:8001/api/v1/project/list/?page_size=1&page_number=3&next_key=
# GET ALL PROJECTS PAGINATED (using skip & limit)
@router.get(
    "/project/listfast/",
    tags=["projects"],
    status_code=status.HTTP_200_OK,
    # response_model=ProjectModel,
)
async def show_projects(
    db: AsyncIOMotorClient = Depends(get_database),
    next_key: str = None,
    page_size: Optional[int] = 10,
    page_number: Optional[int] = 1,
):

    # id is a ObjectId
    n_docs = await count_projects(db)
    page_tot = n_docs // page_size
    result, next = await find_all_project_paginated(
        db, query={}, limit=page_size, sort=["_id", -1], next_key=next_key
    )

    return {
        "next_key": str(next),
        "page_size": page_size,
        "page_number": page_number,
        "page_tot": page_tot,
        "number_docs": n_docs,
        "data": [{k: d[k] for k in set(list(d.keys())) - set(["_id"])} for d in result],
    }


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
    """Add a new project

    Parameters: NewProjectModel - the project to add
    Returns: dict - {"inserted_id": ObjectID} where ObjectID is the document ID inserted in DB
                    (use this ID as path parameter to add files to project)
    """
    logger.info(f"add_new_project: {project.dict()}")
    # id is a ObjectId
    id = await add_project(db, project=project)
    # content=json.dumps(dict(project), default=str)
    # JSONResponse(content=json.dumps(dict(project), default=str))
    return {"inserted_id": str(id)}


# ADD PROJECT FILES
# REQUIRES PROJECT_ID AND FILE_NAME
# http://0.0.0.0:8001/api/v1/project/addfile/?project_id=5eb8f8f8f8f8f8f8f8f8f8f8&file=TEST.pdf
@router.post("/project/add/file/", tags=["projects"])
async def create_project_file(
    file_name: str,
    project_id: ObjectIdStr,
    file: UploadFile = File(...),
    db: AsyncIOMotorClient = Depends(get_database),
):
    """Add a new file to a project

    Parameters:
    ----------
                project_id: ObjectID - the project ID (returned by {URI}/api/v1/project/add)
                file_name: str - the file name
                NOTE!   file_name is the file name without the extension
                        file extention is checked against extensions already in the database
                        if the extention of file uploaded and that present in DB doest not match
                        nothing is added to the database and a HTTP_500_INTERNAL_SERVER_ERROR is returned
    Returns:
    ----------
        dict - {"file_name": str,  "file_hash": str, "file_size": str}

    Raises:
    -------
        HTTPException 400 if a file type is not allowed
        (Allowed file types are: CSV, PDF, TXT, CIF, DOC)

        HTTPException 500 if document was not updated
    """
    # convert path parameter "project_id" to ObjectId
    id_mongodb = BsonObjectId(project_id)
    # Check file MimeType
    if file.content_type not in Config.allowed_mime_types:
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
        # compute file hash  & rename file on FileSystem accordgly    ###########
        hash = hash_file(file_to_write)
        new_file_name = f"{upload_dir}/{hash}.{file_ext}"
        rename(file_to_write, new_file_name)
        #########################################################################
        # get file size
        file_size = get_str_file_size(new_file_name)

        # add file to docoment in DB having id == project_id
        update_modified_count = await add_project_file(
            db, id_mongodb, hash, file_size, file_ext, file_name.split(".")[0]
        )
        if update_modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Document not updated",
            )
    return {
        "file_name": f"{file.filename}",
        "file_hash": f"{hash}",
        "file_size": file_size,
    }


# ADD PROPERTY FILE TO PROJECT
# REQUIRES PROJECT ID, PROPERTY NAME AND PROPERTY TYPE
# http://0.0.0.0:8001/api/v1/project/add/file/?project_id=62752dd88856514dab27dd8e&property_name=H2o&property_type=2D
@router.post("/project/add/propertyfile/", tags=["projects"])
async def create_property_file(
    project_id: ObjectIdStr,
    property_name: str,
    property_type: str,
    file: UploadFile = File(...),
    db: AsyncIOMotorClient = Depends(get_database),
):
    id_mongodb = BsonObjectId(project_id)
    # Check file MimeType
    if file.content_type not in Config.allowed_mime_types:
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
# LIST PROPERTIES FILES BY AFFILIATION & PROJECT NAME
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


@router.post("/project/add_property_and_file/{project_id}", tags=["projects"])
async def login(
    project_id: ObjectIdStr,
    form_data: PropertyForm = Depends(PropertyForm.as_form),
    fileupload: Optional[UploadFile] = File(None),
    db: AsyncIOMotorClient = Depends(get_database),
):
    if fileupload is not None:
        file = PropertyFile()
        file.extention = fileupload.filename.split(".")[-1]
        file.name = fileupload.filename.split(file.extention)[0]
        upload_dir = Config.files_dir
        file_hash, file_size, file_ext = await save_file(fileupload, upload_dir)
        file.hash = file_hash
        file.size = file_size

        if file_hash:
            modified_count = await add_property(
                db, project_id, Property(**form_data.dict(), file=file)
            )
            return {
                "hash_file": file.hash,
                "file_size": file.size,
                "file_ext": file.extention,
            }
        else:
            raise HTTPException(400, detail="Unable to save file")
    modified_count, _ = await add_property(
        db, project_id, Property(**form_data.dict(), file=None)
    )
    return {"modified_count": modified_count}

    # f.size = fileupload.size
    # if username == "admin" and password == "admin":
    #     return JSONResponse(content={"message": "Logged in successfully"})


# ADD FILE TO PROJECT WITH DATA ****USING FORM****
# http://0.0.0.0:8001/api/v1/project/add_file/62761c48856da47202945e05
@router.post("/project/add_file/{project_id}", tags=["projects"])
async def login(
    project_id: ObjectIdStr,
    form_data: ProjectFileForm = Depends(ProjectFileForm.as_form),
    fileupload: UploadFile = File(...),
    db: AsyncIOMotorClient = Depends(get_database),
):
    if fileupload is not None and fileupload.filename != "":
        if fileupload.content_type not in Config.allowed_mime_types:
            raise HTTPException(400, detail="Invalid document type")
        extention = fileupload.filename.split(".")[-1]
        file_name = fileupload.filename.split(extention)[0]
        upload_dir = Config.files_dir
        file_hash, file_size, _ = await save_file(fileupload, upload_dir)

        if file_hash:
            file = FileProject(
                name=form_data.name,
                description=form_data.description,
                type=fileType.from_str(form_data.type.lower()),
                hash=file_hash,
                size=file_size,
                extention=extention,
                isProcessed=form_data.isProcessed,
            )
            if form_data.publication_name:
                file.publication = Publication(
                    name=form_data.publication_name,
                    date=form_data.publication_date,
                    url=form_data.publication_url,
                )

            result = await add_project_file_and_data(db, project_id, file)
            return {
                "hash_file": file.hash,
                "file_size": file.size,
                "file_ext": file.extention,
            }
        else:
            raise HTTPException(400, detail="Unable to save file")
    raise HTTPException(400, detail="You must provide a file")


# https://github.com/tiangolo/fastapi/issues/362
# https://stackoverflow.com/questions/65504438/how-to-add-both-file-and-json-body-in-a-fastapi-post-request/70640522#70640522
