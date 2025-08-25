from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models import User
from app.core.database import get_db
from app.schemas.user import UserCreate, UserResponse


router = APIRouter()


@router.post("/", response_model=UserResponse)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)) -> User:
    # Check if user already exists
    existing_user = db.query(User).filter(User.phone_number == user_data.phone_number).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this phone number already exists")

    print(user_data)

    # Create new user
    user = User(
        phone_number=user_data.phone_number,
        name=user_data.name
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user