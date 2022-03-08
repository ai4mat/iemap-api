from fastapi import APIRouter, Body
from fastapi.encoders import jsonable_encoder

from server.database import (
    retrieve_items,
    retrieve_item,
    retrieve_items_fts,
)

from server.models.item import (
    ResponseModel,
    ErrorResponseModel,
)

router = APIRouter()

@router.get("/listItems", response_description="Items retrieved")
async def get_items():
    items = await retrieve_items()
    if items:
        return ResponseModel(items, "Items data retrieved successfully")
    return ResponseModel(items, "Empty list returned")

@router.get("/getItem/{id}", response_description="Item data retrieved")
async def get_item_data(id):
    item = await retrieve_item(id)
    if item:
        return ResponseModel(item, "Item data retrieved successfully")
    return ErrorResponseModel("An error occurred.", 404, "Item doesn't exist.")

@router.get("/fts/getItem/{string}", response_description="Item data retrieved")
async def get_fulltextsearch_item_data(string):
    items = await retrieve_items_fts(string)
    if items:
        return ResponseModel(items, "Items data retrieved successfully")
    return ResponseModel(items, "Empty list returned")
