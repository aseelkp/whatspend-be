from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def placeholder():
    return {"message": "Transactions endpoint placeholder - implement later"}