from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.responses import create_pagination_info, success, error
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.models.category import Category
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
)
from app.schemas.responses import StandardResponse, ErrorDetail

router = APIRouter()


@router.post("/", response_model=StandardResponse)
def create_transaction(
    transaction_data: TransactionCreate, db: Session = Depends(get_db)
):
    """Create a new transaction"""

    user = db.query(User).filter(User.id == transaction_data.user_id).first()
    if not user:
        return error(
            message="Transaction creation failed",
            errors=[
                ErrorDetail(
                    field="user_id", code="not_found", message="No user with this ID"
                )
            ],
        )

    category = (
        db.query(Category).filter(Category.id == transaction_data.category_id).first()
    )
    if not category:
        return error(
            message="Transaction creation failed",
            errors=[
                ErrorDetail(
                    field="category_id",
                    code="not_found",
                    message="No category with this ID",
                )
            ],
        )

    transaction = Transaction(
        user_id=transaction_data.user_id,
        category_id=transaction_data.category_id,
        amount=transaction_data.amount,
        transaction_type=transaction_data.transaction_type,
        description=transaction_data.description,
        raw_message=transaction_data.raw_message,
    )

    print("Transaction created:", transaction.id)
    try:
        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        transaction_response = build_transaction_response(transaction, db)

        return success(
            message="Transaction created successfully", data=TransactionResponse.model_validate(transaction_response).model_dump()
        )
    except Exception as e:
        db.rollback()
        return error(
            message="Transaction creation failed",
            errors=[
                ErrorDetail(
                    field="transaction",
                    code="internal_error",
                    message=str(e),
                )
            ],
        )


@router.get("/{transaction_id}", response_model=StandardResponse)
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    """Get a transaction by ID"""

    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        return error(
            message="Transaction not found",
            errors=[
                ErrorDetail(
                    field="transaction_id",
                    code="not_found",
                    message="No transaction with this ID",
                )
            ],
        )

    transaction_response = build_transaction_response(transaction, db)

    return success(
        message="Transaction retrieved successfully", data=transaction_response
    )


@router.get("/", response_model=StandardResponse)
def get_transactions(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Transactions per page"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    transaction_type: Optional[str] = Query(
        None, description="Filter by transaction type"
    ),
    date_from: Optional[datetime] = Query(None, description="Filter by start date"),
    date_to: Optional[datetime] = Query(None, description="Filter by end date"),
    min_amount: Optional[float] = Query(
        None, ge=0, description="Filter by minimum amount"
    ),
    max_amount: Optional[float] = Query(
        None, ge=0, description="Filter by maximum amount"
    ),
    db: Session = Depends(get_db),
):
    """Get a list of transactions with filters and pagination"""

    query = db.query(Transaction)

    if user_id:
        query = query.filter(Transaction.user_id == user_id)

    if category_id:
        query = query.filter(Transaction.category_id == category_id)

    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)

    if date_from:
        query = query.filter(Transaction.created_at >= date_from)

    if date_to:
        query = query.filter(Transaction.created_at <= date_to)

    if min_amount:
        query = query.filter(Transaction.amount >= min_amount)

    if max_amount:
        query = query.filter(Transaction.amount <= max_amount)

    total = query.count()

    offset = (page - 1) * per_page

    transactions = (
        query.order_by(Transaction.created_at.desc())
        .offset(offset)
        .limit(per_page)
        .all()
    )




    transaction_data = [build_transaction_response(txn, db) for txn in transactions]

    pagination = create_pagination_info(page=page, per_page=per_page, total=total)

    return success(
        message=f"Retrieved {len(transaction_data)} transactions successfully",
        data=transaction_data,
        pagination=pagination,  # Add this line
    )


@router.patch("/{transaction_id}", response_model=StandardResponse)
def update_transaction(
    transaction_id: str,
    transaction_data: TransactionUpdate,
    db: Session = Depends(get_db),
):
    """ " Update a transaction"""

    transaction: Transaction | None = (
        db.query(Transaction).filter(Transaction.id == transaction_id).first()
    )
    if not transaction:
        return error(
            message="Transaction not found",
            errors=[
                ErrorDetail(
                    field="transaction_id",
                    code="not_found",
                    message="No transaction with this ID",
                )
            ],
        )

    if transaction_data.category_id:
        category = (
            db.query(Category)
            .filter(Category.id == transaction_data.category_id)
            .first()
        )
        if not category:
            return error(
                message="Transaction update failed",
                errors=[
                    ErrorDetail(
                        field="category_id",
                        code="not_found",
                        message="Category does not exist",
                    )
                ],
            )

    if transaction_data.amount is not None:
        transaction.amount = transaction_data.amount

    if transaction_data.category_id:
        transaction.category_id = transaction_data.category_id

    if transaction_data.description is not None:
        transaction.description = transaction_data.description

    if transaction_data.raw_message is not None:
        transaction.raw_message = transaction_data.raw_message

    if transaction_data.transaction_type:
        transaction.transaction_type = transaction_data.transaction_type

    try:
        db.commit()
        db.refresh(transaction)

        transaction_response = build_transaction_response(transaction, db)

        return success(
            message="Transaction updated successfully", data=transaction_response
        )

    except Exception as e:
        db.rollback()
        return error(
            message="Transaction update failed",
            errors=[
                ErrorDetail(
                    field="transaction",
                    code="update_failed",
                    message=str(e),
                )
            ],
        )


@router.delete("/{transaction_id}", response_model=StandardResponse)
def delete_transaction(transaction_id: str, db: Session = Depends(get_db)):
    """Delete a transaction"""

    transaction: Transaction | None = (
        db.query(Transaction).filter(Transaction.id == transaction_id).first()
    )
    if not transaction:
        return error(
            message="Transaction not found",
            errors=[
                ErrorDetail(
                    field="transaction_id",
                    code="not_found",
                    message="No transaction with this ID",
                )
            ],
        )

    try:
        db.delete(transaction)
        db.commit()

        return success(message="Transaction deleted successfully")

    except Exception as e:
        db.rollback()
        return error(
            message="Transaction deletion failed",
            errors=[
                ErrorDetail(
                    field="transaction",
                    code="delete_failed",
                    message=str(e),
                )
            ],
        )


def build_transaction_response(transaction: Transaction, db: Session):
    category = db.query(Category).filter(Category.id == transaction.category_id).first()

    return {
        "id": str(transaction.id),
        "user_id": str(transaction.user_id),
        "amount": transaction.amount,
        "transaction_type": transaction.transaction_type,
        "category_id": str(transaction.category_id),
        "description": transaction.description,
        "raw_message": transaction.raw_message,
        "created_at": transaction.created_at.isoformat(),
        "updated_at": transaction.updated_at.isoformat(),
        "category_name": category.name if category else None,
        "category_display_name": category.display_name if category else None,
        "category_icon": category.icon if category else None,
    }