from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.config import settings
from app.core.database import get_session

reusable_oauth2 = HTTPBearer()

async def get_db() -> Generator:
    try:
        db = get_session()
        yield db
    finally:
        await db.aclose()

async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> dict:
    try:
        payload = jwt.decode(
            token.credentials, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        token_data = payload.get("sub")
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    
    # TODO: Implement user lookup from database
    user = {"id": token_data}  # Placeholder
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user