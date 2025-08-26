from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.responses import success, error
from app.models import User
from app.core.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.schemas.responses import StandardResponse, ErrorDetail

router = APIRouter()


@router.post("/", response_model=StandardResponse)
def create_user(
    user_data: UserCreate, db: Session = Depends(get_db)
) -> StandardResponse:
    # Check if user already exists
    existing_user = (
        db.query(User).filter(User.phone_number == user_data.phone_number).first()
    )
    if existing_user:
        return error(
            message="User creation failed",
            errors=[
                ErrorDetail(
                    field="phone_number",
                    code="duplicate",
                    message="User with this phone number already exists",
                )
            ],
        )

    # Create new user
    user = User(phone_number=user_data.phone_number, name=user_data.name)

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return success(
            "User created successfully",
            data=UserResponse.model_validate(user).model_dump(),
        )
    except Exception as e:
        db.rollback()
        return error(
            message="User creation failed",
            errors=[
                ErrorDetail(
                    field=None,
                    code="database_error",
                    message="Failed to create user",
                )
            ],
        )

@router.get("/", response_model=StandardResponse)
def get_users(db: Session = Depends(get_db)) -> StandardResponse:
    users = db.query(User).all()
    return success("Users retrieved successfully", data=[UserResponse.model_validate(user).model_dump() for user in users])

@router.get("/{user_id}", response_model=StandardResponse)
def get_user(user_id: str, db: Session = Depends(get_db)) -> StandardResponse:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return error(
            message="User not found",
            errors=[
                ErrorDetail(
                    field="user_id",
                    code="not_found",
                    message="User with this ID does not exist",
                )
            ],
        )
    return success("User retrieved successfully", data=UserResponse.model_validate(user).model_dump())
