from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def placeholder():
    return {"message": "Users endpoint placeholder - implement later"}