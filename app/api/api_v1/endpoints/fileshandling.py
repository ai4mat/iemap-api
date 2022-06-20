import hashlib
from pathlib import Path
from core.utils import get_dir_uploaded, hash_file
from os import getcwd, remove, rename, path
from dotenv import dotenv_values, find_dotenv

# import json
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse, FileResponse

# import aiofiles

router = APIRouter()
from core.config import Config

# config = {
#     **dotenv_values(
#         find_dotenv(raise_error_if_not_found=True)
#     ),  # load shared development variables
# }
upload_dir = Config.files_dir  # dir is "uploaded" set in .env.shared

# allowed_format = json.loads(
#     config["ALLOWED_FORMAT_UPLOAD"]
# )  #  [".txt", ".pdf", ".docx", ".csv",".zip"] set in .env.shared

# https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types
allowed_mime_types = [
    "text/csv",
    # "application/zip",
    "application/pdf",
    "text/plain",
    "chemical/x-cif",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]


@router.post("/files/upload", response_description="Items retrieved", status_code=201)
async def create_upload_file(file: UploadFile = File(...)):
    if file.content_type not in allowed_mime_types:
        raise HTTPException(400, detail="Invalid document type")

    file_to_write = f"{upload_dir}/{file.filename}"
    with open(file_to_write, "wb+") as file_object:
        file_object.write(file.file.read())

    # SLOWER VERSION BUT DOES NOT LOAD ENTIRE FILE IN MEMORY
    # async with aiofiles.open(file_to_write, 'wb') as out_file:
    #     while content := await file.read(1024):  # async read chunk
    #         await out_file.write(content)  # async write chunk

    # compute hash of file
    hash = hash_file(file_to_write)
    return {"info": f"file '{file.filename}' hash: {hash}"}


@router.post("/files/uploadandhashing", response_description="Items retrieved")
async def create_upload_file(file: UploadFile = File(...)):
    if file.content_type not in allowed_mime_types:
        raise HTTPException(400, detail="Invalid document type")
    file_to_write = f"{upload_dir}/{file.filename}"
    h = hashlib.sha1()
    with open(file_to_write, "wb+") as file_object:
        content = file.file.read()
        h.update(content)
        hash = h.hexdigest()
        file_object.write(file.file.read())
        ext = file.filename.split(".")[-1]
        rename(file_to_write, f"{upload_dir}/{hash}.{ext}")

        return {"info": f"file '{file.filename}' hash: {hash}"}


@router.get("/files/{name_file}")
def get_file(name_file: str) -> FileResponse:
    """Download file from server

    Args:
        name_file (str): file name to download expressed as <hash>.<ext>

    Raises:
        HTTPException: HTTP Error 404 if file not found

    Returns:
        FileResponse: binary stream of file
    """
    # get directory path for uploaded_dir
    # if app is in path then use parent (remove 'app' from path) dir and concat with uploaded_dir
    # if app in NOT in path the is not necessary to get parent dir
    base_dir = get_dir_uploaded(upload_dir)

    # path for file to write on file system
    file_path = base_dir / name_file

    # print(file_path)
    isExisting = file_path.is_file()
    if isExisting:
        content = FileResponse(file_path)
        return content
    else:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="File not found")


@router.delete("/files/delete/{name_file}")
def delete_file(name_file: str):

    file_path = f"{getcwd()}/{upload_dir}/{name_file}"
    isExisting = path.exists(file_path)
    if isExisting:
        remove(file_path)
        return JSONResponse(content={"removed": True}, status_code=200)
    else:
        return JSONResponse(
            content={"removed": False, "error_message": "File not found"},
            status_code=404,
        )


# https://stackoverflow.com/questions/63580229/how-to-save-uploadfile-in-fastapi
# https://dev.to/nelsoncode/how-to-create-server-of-files-with-fastapi-47d0
