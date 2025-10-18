from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.services.auth_service import auth_service

reusable_oauth2 = HTTPBearer()


def get_token_from_header(authorization : str) :
    if not authorization : 
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Missing Authorization header"
        )
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" : 
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid Authorization header"
        )
    
    return parts[1]

def get_current_user(authorization : str , db : Session = Depends(get_db)) :

    try : 
        token = get_token_from_header(authorization)
        
        user_id = auth_service.verify_jwt_token(token)

        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED , detail="User not found")
        
        if not user.is_active.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN , detail="User is not active")

        return user
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED , detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR , detail=str(e))

        
