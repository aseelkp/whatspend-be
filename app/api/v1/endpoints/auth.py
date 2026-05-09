from multiprocessing import Value
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse
from app.core.responses import success, error
from app.core.config import settings
from app.core.database import get_db, SessionLocal
from app.schemas.auth import (
    AuthResponse,
    RequestMagicLinkRequest,
    VerifyMagicLinkRequest,
)
from app.schemas.responses import ErrorDetail, StandardResponse
from app.services.auth_service import auth_service
from app.services.whatsapp_service import whatsapp_service


router = APIRouter()


@router.post("/request-magic-link", response_model=StandardResponse)
async def request_magic_link(
    request: RequestMagicLinkRequest, db: Session = Depends(get_db)
):

    try:
        magic_token, user_id = auth_service.generate_magic_link(
            db, request.phone_number
        )

        magic_link_url = (
            f"{settings.DASHBOARD_URL}/dashboard/verify?token={magic_token}"
        )
        message = f"""🔐 *Your Magic Link*

            Click the link below to access your dashboard:
            {magic_link_url}

            ⏰ Link expires in 15 minutes

            🔒 Never share this link with anyone!"""

        await whatsapp_service._send_whatsapp_message(request.phone_number, message)

        return success(
            message="Magic link sent successfully",
            data={"user_id": user_id, "message": "Check your WhatsApp for the link"},
        )
    except Exception as e:
        return error(
            message="Failed to send magic link",
            errors=[
                ErrorDetail(field=None, code="internal_server_error", message=str(e))
            ],
        )


@router.post("/verify-magic-link", response_model=StandardResponse)
def verify_magic_link(request: VerifyMagicLinkRequest, db: Session = Depends(get_db)):
    try:
        user_id = auth_service.verify_magic_link(db, request.token)

        access_token = auth_service.create_jwt_token(user_id)

        return success(
            message="Authentication successful",
            data=AuthResponse(access_token=access_token, user_id=user_id),
        )

    except ValueError as e:
        return error(
            message="Authentication failed",
            errors=[ErrorDetail(field=None, code="invalid_token", message=str(e))],
        )
    except Exception as e:
        return error(
            message="Authentication failed",
            errors=[
                ErrorDetail(field=None, code="internal_server_error", message=str(e))
            ],
        )


@router.get("/me", response_model=StandardResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    try:
        return success(
            message="User information retrieved successfully",
            data=UserResponse.model_validate(current_user),
        )
    except Exception as e:
        return error(
            message="Failed to retrieve user information",
            errors=[
                ErrorDetail(field=None, code="internal_server_error", message=str(e))
            ],
        )
