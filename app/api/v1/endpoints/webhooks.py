from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def placeholder():
    return {"message": "Webhooks endpoint placeholder - implement later"}