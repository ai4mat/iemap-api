import hashlib
import json
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from server.utils.hashing_file import hash_file
from os import getcwd, remove, rename, path
from dotenv import dotenv_values

import aiofiles

router = APIRouter()

config = {
    **dotenv_values(".env.shared"),  # load shared development variables
}
upload_dir = config["FILESDIR"]  # dir is "uploaded" set in .env.shared

allowed_format = json.loads(
    config["ALLOWED_FORMAT_UPLOAD"]
)  #  [".txt", ".pdf", ".docx", ".csv",".zip"] set in .env.shared

# https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types
allowed_mime_types = [
    "text/csv", "application/zip", "application/pdf", "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
]


@router.post("/upload", response_description="Items retrieved")
async def create_upload_file(file: UploadFile = File(...)):

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


@router.post("/uploadandhashing", response_description="Items retrieved")
async def create_upload_file(file: UploadFile = File(...,
                                                     format=allowed_format)):
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


@router.get("/file/{name_file}")
def get_file(name_file: str):

    file_path = f"{getcwd()}/{upload_dir}/{name_file}"
    isExisting = path.exists(file_path)
    if isExisting:
        content = FileResponse(file_path)
        return content
    else:
        return JSONResponse(content={"error": "file not found!"},
                            status_code=404)


@router.delete("/delete/file/{name_file}")
def delete_file(name_file: str):

    file_path = f"{getcwd()}/{upload_dir}/{name_file}"
    isExisting = path.exists(file_path)
    if isExisting:
        remove(file_path)
        return JSONResponse(content={"removed": True}, status_code=200)
    else:
        return JSONResponse(content={
            "removed": False,
            "error_message": "File not found"
        },
                            status_code=404)


#https://stackoverflow.com/questions/63580229/how-to-save-uploadfile-in-fastapi
#https://dev.to/nelsoncode/how-to-create-server-of-files-with-fastapi-47d0