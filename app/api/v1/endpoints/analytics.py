from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def placeholder():
    return {"message": "Analytics endpoint placeholder - implement later"}