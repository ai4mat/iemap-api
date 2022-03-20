from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from server.utils.hashing_file import hash_file
from os import getcwd, remove, path
from dotenv import dotenv_values

import aiofiles

router = APIRouter()

config = {
    **dotenv_values(".env.shared"),  # load shared development variables
}
upload_dir = config["FILESDIR"]


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