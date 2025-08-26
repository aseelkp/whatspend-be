from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.responses import success, error
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryResponse
from app.schemas.responses import StandardResponse, ErrorDetail


router = APIRouter()


@router.get("/", response_model=StandardResponse)
def get_categories(db: Session = Depends(get_db)):

    categories = db.query(Category).filter(Category.is_active == True).all()

    category_data = [CategoryResponse.model_validate(cat) for cat in categories]
    return success("Categories retrieved successfully", data=category_data)


@router.post("/", response_model=StandardResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):

    existing = db.query(Category).filter_by(name=category.name).first()
    if existing:
        return error(
            message="Category creation failed",
            errors=[
                ErrorDetail(
                    field="name",
                    code="duplicate",
                    message="Category with this name already exists",
                )
            ],
        )

    category = Category(
        name=category.name,
        display_name=category.display_name,
        description=category.description,
        icon=category.icon,
        color=category.color,
    )

    try:
        db.add(category)
        db.commit()
        db.refresh(category)

        return success(
            "Category created successfully",
            data=CategoryResponse.model_validate(category).model_dump(),
        )

    except Exception as e:
        db.rollback()
        return error(
            message="Category creation failed",
            errors=[
                ErrorDetail(
                    field=None,
                    code="database_error",
                    message="Failed to create category",
                )
            ],
        )
