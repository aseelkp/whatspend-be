from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import TransactionCreate, TransactionUpdate

class TransactionService:
    def __init__(self):
        pass
    
    async def create_transaction(
        self, 
        db: AsyncSession, 
        transaction: TransactionCreate, 
        user_id: int
    ) -> Transaction:
        """
        Create a new transaction for the specified user.
        """
        # TODO: Implement transaction creation
        db_transaction = Transaction(
            user_id=user_id,
            amount=transaction.amount,
            description=transaction.description,
            category_id=transaction.category_id,
            original_message=transaction.original_message,
            transaction_date=transaction.transaction_date
        )
        
        db.add(db_transaction)
        await db.commit()
        await db.refresh(db_transaction)
        return db_transaction
    
    async def get_user_transactions(
        self, 
        db: AsyncSession, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Transaction]:
        """
        Get transactions for a specific user with pagination.
        """
        # TODO: Implement transaction retrieval
        result = await db.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(Transaction.transaction_date.desc())
        )
        return result.scalars().all()
    
    async def update_transaction(
        self, 
        db: AsyncSession, 
        transaction_id: int, 
        transaction_update: TransactionUpdate
    ) -> Optional[Transaction]:
        """
        Update an existing transaction.
        """
        # TODO: Implement transaction update
        return None