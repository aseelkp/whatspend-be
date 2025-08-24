from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def placeholder():
    return {"message": "Auth endpoint placeholder - implement later"}