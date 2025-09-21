from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.user import User
from app.models.transaction import Transaction
from app.models.category import Category
from app.schemas.transaction import TransactionCreate, TransactionUpdate


class TransactionService:

    def create_transaction(
        self, db: Session, transaction_data: TransactionCreate
    ) -> Transaction:
        try:

            user = db.query(User).filter(User.id == transaction_data.user_id).first()

            if not user:
                raise ValueError("User not found")

            category = (
                db.query(Category)
                .filter(Category.id == transaction_data.category_id)
                .first()
            )
            if not category:
                raise ValueError("Category not found")

            new_transaction = Transaction(
                user_id=transaction_data.user_id,
                category_id=transaction_data.category_id,
                amount=transaction_data.amount,
                transaction_type=transaction_data.transaction_type,
                description=transaction_data.description,
                raw_message=transaction_data.raw_message,
            )
            db.add(new_transaction)
            db.commit()
            db.refresh(new_transaction)
            return new_transaction
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error creating transaction: {e}")
            raise

    def update_transaction(
        self, db: Session, transaction_id: int, transaction_data: TransactionUpdate
    ) -> Optional[Transaction]:
        try:
            transaction = (
                db.query(Transaction).filter(Transaction.id == transaction_id).first()
            )
            if not transaction:
                return None

            for key, value in transaction_data.dict(exclude_unset=True).items():
                setattr(transaction, key, value)

            db.commit()
            db.refresh(transaction)
            return transaction
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error updating transaction: {e}")
            raise

    def delete_transaction(self, db: Session, transaction_id: int) -> bool:
        try:
            transaction = (
                db.query(Transaction).filter(Transaction.id == transaction_id).first()
            )
            if not transaction:
                return False

            db.delete(transaction)
            db.commit()
            return True
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Error deleting transaction: {e}")
            raise

    def find_category_by_name(
        self, db: Session, category_name: str
    ) -> Optional[Category]:
        category = (
            db.query(Category)
            .filter(Category.name == category_name, Category.is_active == True)
            .first()
        )

        if category:
            return category

        # Fallback to 'other' category
        other_category = (
            db.query(Category)
            .filter(Category.name == "other", Category.is_active == True)
            .first()
        )

        if not other_category:
            raise ValueError("No 'other' category found - check category seeding")

        return other_category

transaction_service = TransactionService()