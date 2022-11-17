import logging
import aiofiles.os
from typing import Optional, List, Union
from bson.objectid import ObjectId as BsonObjectId
from core.parsing import parse_cif
from core.utils import (
    get_dir_uploaded,
    get_str_file_size,
    hash_file,
    rename_file_with_its_hash,
    save_file,
)
from os import path, rename
from dotenv import dotenv_values, find_dotenv
from pydantic import Json
from fastapi import (
    APIRouter,
    Depends,
    status,
    File,
    Form,
    Query,
    UploadFile,
    HTTPException,
    Request,
)

from fastapi.responses import JSONResponse
from sentry_sdk import capture_exception
from db.mongodb import AsyncIOMotorClient, get_database

# NECESSARY TO HANDLE FASTAPI_USERS
from db.mongodb_utils import UserAuth
from models.users import fastapi_users

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
    exec_query,
)
from models.iemap import (
    PropertyFile,
    PropertyForm,
    newProject as NewProjectModel,
    newProjectResponse,
    # PydanticObjectId,
    ObjectIdStr,
    Provenance,
    FileProject,
    ProjectFileForm,
    Property,
    fileType,
    newProjectResponse,
    queryModel,
)


from core.config import Config


logger = logging.getLogger("ai4mat")

router = APIRouter()

upload_dir = Config.files_dir

# Get the current user (active or not)¶
current_user = fastapi_users.current_user(verified=True)

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
    # project: NewProjectModel = None,
    page_size: Optional[int] = 10,
    page_number: Optional[int] = 1,
):
    """Get all projects paginated (using skip & limit)

    Args:
        db (AsyncIOMotorClient): Motor client connection to MongoDB. Defaults to Depends(get_database).
        page_size (Optional[int], optional): size paginated results. Defaults to 10.
        page_number (Optional[int], optional): actual page number returned. Defaults to 1.

    Returns:
        dict:  {"skip" (int): number of docs to skip,
                "page_size" (int): number of results to return in a single page,
                "page_number" (int): actual page number returned,
                "page_tot" (int): total number of pages available,
                "number_docs" (int): total number of documents in collection,
                "data" list[ProjetModel]: list of all projects saved in database}
    """

    # id is a ObjectId
    n_docs = await count_projects(db)
    skip = page_size * (page_number - 1)
    if page_size > n_docs:
        page_tot = 1
    else:
        page_tot = (n_docs // page_size) + (n_docs - page_size) if n_docs > 0 else 0
    result = await list_projects(db, page_size, skip)

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
@router.post("/project/add", tags=["projects"], status_code=status.HTTP_200_OK)
async def add_new_project(
    project: NewProjectModel,
    db: AsyncIOMotorClient = Depends(get_database),
    # COMMENT user:...below TO REMOVE AUTHORIZATION ~~~~~~~~~~~~~~~
    # IF USER ACCOUNT IS NOT VERIFIED IT RETURNS FORBIDDEN ~~~~~~~~~~~~~~~~
    # Options defined in current_user RULE how authentication works, see below
    # https://fastapi-users.github.io/fastapi-users/10.1/usage/current-user/?h=verified#get-the-current-active-and-verified-user
    user: UserAuth = Depends(current_user),
) -> newProjectResponse:
    """Add new project (metadata)

    Args:
        db (AsyncIOMotorClient, optional): Motor client connection to MongoDB. Defaults to Depends(get_database).
        project (NewProjectModel): project metadata to store on DB. Defaults to None.

    Returns:
        dict: {"inserted_id": ObjectID} where ObjectID is the document ID inserted in DB
            (use this ID as path parameter to add files to project)
    """
    # logger.info(f"add_new_project: {project.dict()}")
    # id is a ObjectId

    # RETRIEVE USER DATA FROM JWT
    project.provenance = Provenance(email=user.email, affiliation=user.affiliation)
    id = await add_project(db, project=project)
    # content=json.dumps(dict(project), default=str)
    # JSONResponse(content=json.dumps(dict(project), default=str))
    return newProjectResponse(inserted_id=id)


# ADD PROJECT FILE
# REQUIRES PROJECT_ID AND FILE_NAME
# http://0.0.0.0:8001/api/v1/project/add/file/?project_id=5eb8f8f8f8f8f8f8f8f8f8f8&file_name=TEST.pdf
@router.post("/project/add/file/", tags=["projects"])
async def create_project_file(
    project_id: ObjectIdStr,
    file_name: Optional[str] = None,
    file: UploadFile = File(...),
    db: AsyncIOMotorClient = Depends(get_database),
    # COMMENT user:...below TO REMOVE AUTHORIZATION ~~~~~~~~~~~~~~~
    user: UserAuth = Depends(current_user),
):
    """Add a new file to an existing project

    Note:
        project_id, file_name and file extention (retrieved by backend) are used
        to find the project to which add the file, if these details does not match that
        already on server, the file is not added to the project,
        and a HTTP_500_INTERNAL_SERVER_ERROR is returned.

    Args:
        file_name (str): name of file to add
        project_id (ObjectIdStr): the project ID as saved on DB  (returned by {URI}/api/v1/project/add)
        file (UploadFile): the file to add to the project (saved on filesystem using its hash)
        db (AsyncIOMotorClient): Motor client connection to MongoDB.

    Raises:
        HTTPException: HTTP 400 if the file to add to project is not a PDF,CSV, TXT, CIF or DOC
        HTTPException: HTTP 500 INTERNAL_SERVER_ERROR if it fails to update document in DB

    Returns:
        dict:{"file_name": name of file, "file_hash": hash of file as saved on file system, "file_size": file size in human readable form}
    """

    # convert path parameter "project_id" to ObjectId
    id_mongodb = BsonObjectId(project_id)
    # Check file MimeType
    if file.content_type not in Config.allowed_mime_types:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Invalid document type (allowed only PDF,CSV, XLS, XLSX, TXT, CIF or DOC)",
        )
    # retrieve file extension
    file_ext = file.filename.split(".")[-1]
    # file to write full path
    file_to_write = get_dir_uploaded(upload_dir) / file.filename
    # write file to disk in chunks
    try:
        with open(file_to_write, "wb+") as file_object:

            # SLOWER VERSION BUT DOES NOT LOAD ENTIRE FILE IN MEMORY
            async with aiofiles.open(file_to_write, "wb") as out_file:
<<<<<<< HEAD
                # read entire file in memory NOT IN CHUNCKS
                content = await file.read()
                # # async read chunk
                # while content := await file.read(
                #     Config.files_chunk_size
                # ):
                await out_file.write(content)  # async write chunk
=======
                while content := await file.read(
                    Config.files_chunk_size
                ):  # async read chunk
                    await out_file.write(content)  # async write chunk
>>>>>>> e4b0736d68252d048b78d8aaedc6a777fb3411cb
            # content = file.file.read()
            # structure, distinct_species, lattice = None, None, None
            # if file_ext == "cif":
            #     structure, distinct_species, lattice = parse_cif(file_to_write)
    except Exception as e:
        logger.error(e)
        capture_exception(e)
    # compute file hash & rename file on FileSystem accordingly
    new_file_name = await rename_file_with_its_hash(file_to_write, file_ext, upload_dir)

    if new_file_name != None:
        # extract HASH part only
        hash = str(new_file_name).split("/")[-1].split(".")[0]
        # get file size
        file_size = get_str_file_size(new_file_name)
        fp = FileProject(
            hash=hash,
            # if file_name is not passed as property in url endpoint then save file name in DB
            # as the name of uploaded file
            name=file_name.split(".")[0] if file_name else file.filename,
            extention=file_ext,
            size=file_size,
        )
        # add file to docoment in DB having id == project_id
        update_modified_count, update_matched_count = await add_project_file(
            db, id_mongodb, fp
        )
        if update_modified_count > 0:
            return {
                "file_name": fp.name,
                "file_hash": hash,
                "file_size": file_size,
            }
        if update_modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Document not updated",
            )
    if new_file_name == None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File yet existing, unable to overwite. Please first delete it before replacing it with new content!",
        )


# ADD PROPERTY FILE TO PROJECT
# REQUIRES PROJECT ID, PROPERTY NAME AND PROPERTY TYPE
# http://0.0.0.0:8001/api/v1/project/add/propertyfile/?project_id=62752dd88856514dab27dd8e&name=temperature
@router.post("/project/add/file_property/", tags=["projects"])
async def create_property_file(
    project_id: ObjectIdStr,
    name: str,
    file: UploadFile = File(...),
    db: AsyncIOMotorClient = Depends(get_database),
    # COMMENT user:...below TO REMOVE AUTHORIZATION ~~~~~~~~~~~~~~~
    user: UserAuth = Depends(current_user),
):
    """Add a new property file to an existing project

    Args:
        project_id (ObjectIdStr): id of project to add property file to
        property_name (str): name of property to which add the file
        property_type (str): name of property type to which add the file
        file (UploadFile): file to upload. Defaults to File(...).
        db (AsyncIOMotorClient, optional): Motor client connection to MongoDB. Defaults to Depends(get_database).

    Raises:
        HTTPException: HTTP Error 400 is returned if a file not allowed is uploaded
        HTTPException: HTTP Error 400 is returned no file is provided
        HTTPException: HTTP Error 500 is returned if it was not possible to add the file to the project

    Returns:
        dict:{
            "file_name": name of file added to property,
            "file_hash": hash of file as saved on file system,
            "file_size": file size in human readable form
        }
    """

    id_mongodb = BsonObjectId(project_id)
    # Check file MimeType
    if file.content_type not in Config.allowed_mime_types:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid document type")
    if file.filename == "":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="No file provided")
    # retrieve file extension
    file_ext = file.filename.split(".")[-1]
    # file to write path
    file_to_write = get_dir_uploaded(upload_dir) / file.filename
    # write file to disk in chunks
    with open(file_to_write, "wb+") as file_object:

        # SLOWER VERSION BUT DOES NOT LOAD ENTIRE FILE IN MEMORY
        async with aiofiles.open(file_to_write, "wb") as out_file:
            while content := await file.read(
                Config.files_chunk_size
            ):  # async read chunk
                await out_file.write(content)  # async write chunk
        # content = file.file.read()
        # structure, distinct_species, lattice = None, None, None
        # if file_ext == "cif":
        #     structure, distinct_species, lattice = parse_cif(file_to_write)
        # h.update(content)
        # hash = h.hexdigest()
        # file_object.write(file.file.read())
    # compute file hash & rename file on FileSystem accordingly
    new_file_name = await rename_file_with_its_hash(file_to_write, file_ext, upload_dir)

    if new_file_name != None:
        # extract HASH part only
        hash = str(new_file_name).split("/")[-1].split(".")[0]
        str_file_size = get_str_file_size(new_file_name)

        fp = FileProject(
            hash=hash,
            # if file_name is not passed as property in url endpoint then save file name in DB
            # as the name of uploaded file
            name=name.split(".")[0] if name else file.filename,
            extention=file_ext,
            size=str_file_size,
        )
        modified_count, matched_count = await add_property_file(
            db, id_mongodb, fp, name
        )
        if modified_count == 0:
            await aiofiles.os.remove(new_file_name)
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to add property file",
            )
        return {
            "file_name": f"{file.filename}",
            "file_hash": f"{hash}",
            "file_size": str_file_size,
        }
    if new_file_name == None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File yet existing, unable to overwite. Please first delete it before replacing it with new content!",
        )


# @router.get("/files/{name_file}", tags=["projects"])
# def get_file(name_file: str):

#     file_path = f"{getcwd()}/{upload_dir}/{name_file}"
#     isExisting = path.exists(file_path)
#     if isExisting:
#         content = FileResponse(file_path)
#         return content
#     else:
#         return JSONResponse(content={"error": "file not found!"}, status_code=404)


# http://0.0.0.0:8001/api/v1/project/file/list
# LIST PROPERTIES FILES BY AFFILIATION & PROJECT NAME
@router.get(
    "/project/file/list/",
    tags=["projects"],
)
async def get_list_process_properties_by_proj_name_and_affiliation(
    affiliation: str,
    projectName: str,
    request: Request,
    db: AsyncIOMotorClient = Depends(get_database),
):
    """GET list process properties associated to a project filtered by affiliation and project name

    Args:
        affiliation (str): affiliation of project's user (TODO:retrieved from JWT)
        projectName (str): name of project
        request (Request): _description_
        db (AsyncIOMotorClient, optional): Motor client connection to MongoDB. Defaults to Depends(get_database).

    Returns:
        dict: list of properties files associated to a project
             (if one or more file associated exists an additional "url" field is added within the field "file")
    """
    # retrieve a list of process properties from DB (by project name and affiliation)
    list_doc = await list_project_properties_files(db, affiliation, projectName)
    # add a field to each document to get a file url to eventually download files
    for doc in list_doc:
        file = doc.get("file")
        if file:
            file_path = file["hash"] + "." + file["extention"]
            doc["file"]["url"] = str(request.base_url) + "api/v1/files/" + file_path
    return list_doc


# ADD PROPERTY FILE TO PROJECT WITH DATA ****USING FORM****
# http://0.0.0.0:8001/api/v1/project/add_file_and_property/62761c48856da47202945e05
@router.post("/project/add_file_and_property/{project_id}", tags=["projects"])
async def form_add_property_and_file(
    project_id: ObjectIdStr,
    form_data: PropertyForm = Depends(PropertyForm.as_form),
    fileupload: Optional[UploadFile] = File(None),
    db: AsyncIOMotorClient = Depends(get_database),
):
    """Add a new property and file to an existing project

    Args:
        project_id (ObjectIdStr): id of project to add property file to
        form_data (PropertyForm, optional): project property
        fileupload (Optional[UploadFile], optional): File associated to property to upload. Defaults to File(None).
        db (AsyncIOMotorClient, optional): Motor client connection to MongoDB. Defaults to Depends(get_database).

    Raises:
        HTTPException: HTTP Error 500 if it was not possible to add the property to the project
        HTTPException: HTTP Error 500 if it was not possible save the file to project

    Returns:
        dict:{
              "modified_count" (int): modified_count,
                "hash_file" (str , Optional): hash file saved on disk,
                "file_size" (str, Optional): file size in human readable form,
                "file_ext"(str, Optional): file extension,
        }
    """
    if fileupload is not None:
        file = PropertyFile()
        file.extention = fileupload.filename.split(".")[-1]
        file.name = fileupload.filename.split(file.extention)[0]
        upload_dir = Config.files_dir
        file_hash, file_size, file_ext = await save_file(fileupload, upload_dir)
        file.hash = file_hash
        file.size = file_size

        # ADD PROPERTY having an associated file TO PROJECT only
        # if file was saved succefully
        if file_hash:
            modified_count = await add_property(
                db, project_id, Property(**form_data.dict(), file=file)
            )
            # SEND RESPONSE to client
            return {
                "modified_count": modified_count,
                "hash_file": file.hash,
                "file_size": file.size,
                "file_ext": file.extention,
            }
        else:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to save file"
            )
    else:
        # PROPERTY HAS NO FILE ASSOCIATED THEN ADD ONLY PROPERTY TO PROJECT
        modified_count, _ = await add_property(
            db, project_id, Property(**form_data.dict(), file=None)
        )
        if modified_count == 0:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to add property"
            )
        return {"modified_count": modified_count}

    # f.size = fileupload.size
    # if username == "admin" and password == "admin":
    #     return JSONResponse(content={"message": "Logged in successfully"})


# ADD FILE TO PROJECT WITH DATA ****USING FORM****
# http://0.0.0.0:8001/api/v1/project/add_file/62761c48856da47202945e05
@router.post("/project/add_file_and_data/{project_id}", tags=["projects"])
async def form_add_project_file(
    project_id: ObjectIdStr,
    form_data: ProjectFileForm = Depends(ProjectFileForm.as_form),
    fileupload: UploadFile = File(...),
    db: AsyncIOMotorClient = Depends(get_database),
):
    """Add file to project using Multi-Part Form data

    Args:
        project_id (ObjectIdStr): document id to add file to
        form_data (ProjectFileForm): form data fields. Defaults to Depends(ProjectFileForm.as_form).
        fileupload (UploadFile ): file to upload (as form key use 'fileupload').
        db (AsyncIOMotorClient ): Motor client connection to MongoDb. Defaults to Depends(get_database).

    Raises:
        HTTPException: HTTP 500 Internal Server Error if unable to save file
        HTTPException: HTTP 400 bad request if file was not provided


    Returns:
        dict: {
            "hash_file"(str): hash file saved on file system,
            "file_size"(str): file size in human readable format,
            "file_ext"(str): file extension
        }
    """
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
                    date=form_data.publication_date,  # date conversion is done in Publication class
                    url=form_data.publication_url,
                )

            n_modified, n_matched = await add_project_file_and_data(
                db, project_id, file
            )
            if n_modified == 0:
                raise HTTPException(
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Unable to add file to project",
                )
            return {
                "hash_file": file.hash,
                "file_size": file.size,
                "file_ext": file.extention,
            }
        else:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to save file"
            )
    raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="You must provide a file")


@router.get("/project/query/", tags=["projects"])
async def form_add_project_file(
    params: queryModel = Depends(),
    db: AsyncIOMotorClient = Depends(get_database),
    # response_model=queryModel, #THIS broke swagger auto documentation, FIX THIS!!
):
    """Add file to project using Multi-Part Form data

    Args:
        project_id (ObjectIdStr): document id to add file to
        form_data (ProjectFileForm): form data fields. Defaults to Depends(ProjectFileForm.as_form).
        fileupload (UploadFile ): file to upload (as form key use 'fileupload').
        db (AsyncIOMotorClient ): Motor client connection to MongoDb. Defaults to Depends(get_database).

    Raises:
        HTTPException: HTTP 500 Internal Server Error if unable to save file
        HTTPException: HTTP 400 bad request if file was not provided


    Returns:
        dict: {
            "hash_file"(str): hash file saved on file system,
            "file_size"(str): file size in human readable format,
            "file_ext"(str): file extension
        }
    """
    # params_as_dict = params.dict()

    result = await exec_query(db, params)
    return result


@router.get("/project/test/", tags=["projects"], status_code=status.HTTP_200_OK)
async def test_query(test: Optional[List[Union[str, float]]] = Query(None)) -> dict:
    print(test)
    return test


# https://github.com/tiangolo/fastapi/issues/362
# https://stackoverflow.com/questions/65504438/how-to-add-both-file-and-json-body-in-a-fastapi-post-request/70640522#70640522
