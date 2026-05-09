from app.core.database import Base

# MagicLink before User so string relationship("MagicLink") resolves at mapper init.
from .magic_link import MagicLink
from .user import User
from .category import Category
from .transaction import Transaction

__all__: list[str] = ["User", "Category", "Transaction", "MagicLink"]