from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryResponse


router = APIRouter()

@router.get("/", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):

    categories = db.query(Category).filter(Category.is_active == True).all()
    return categories


@router.post("/", response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):

    existing = db.query(Category).filter_by(name=category.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")

    category = Category(
        name = category.name,
        display_name = category.display_name,
        icon = category.icon,
        color = category.color,
    )

    db.add(category)
    db.commit()
    db.refresh(category)
    
    return category