import re

from typing import Dict, Optional
from decimal import Decimal
from app.models.transaction import TransactionType
from app.services.llm_service import llm_service
import logging

logger = logging.getLogger(__name__)


class MessageParser:
    """Regex-based message parser for transaction data"""

    def __init__(self):
        self.currency_patterns = [
            r"₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)",  # ₹500, ₹1,000.50
            r"rs\.?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)",  # Rs. 500, rs 1000
            r"(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:₹|rs\.?|rupees?|bucks?)",  # 500₹, 500 rs, 500 rupees, 500 bucks
            r"(\d+(?:\.\d+)?)\s*k\s*(?:rupees?|bucks?|₹|rs\.?)?",  # 2k, 1.5k rupees
            r"(?:cost|paid|spent|price)\s*(?:of|is|was)?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)",  # cost 500, paid 1000
        ]

        self.category_keywords = {
            "groceries": [
                "grocery",
                "groceries",
                "vegetables",
                "fruits",
                "sabzi",
                "market",
                "vegetable",
                "fruit",
                "dmart",
                "reliance",
                "food",
                "meal",
                "dinner",
                "lunch",
                "breakfast",
                "restaurant",
                "zomato",
                "swiggy",
                "eating",
            ],
            "transportation": [
                "uber",
                "ola",
                "taxi",
                "auto",
                "rickshaw",
                "bus",
                "metro",
                "petrol",
                "diesel",
                "fuel",
                "parking",
                "toll",
                "rapido",
                "transport",
            ],
            "entertainment": [
                "movie",
                "cinema",
                "netflix",
                "prime",
                "spotify",
                "game",
                "entertainment",
                "ticket",
                "show",
                "pvr",
                "inox",
                "concert",
                "party",
            ],
            "healthcare": [
                "medicine",
                "doctor",
                "hospital",
                "pharmacy",
                "medical",
                "health",
                "appointment",
                "checkup",
                "prescription",
                "healthcare",
            ],
            "other": [],
        }

        # Transaction type indicators
        self.expense_indicators = [
            "spent",
            "paid",
            "bought",
            "purchase",
            "cost",
            "expense",
            "bill",
            "charge",
        ]

        self.income_indicators = [
            "salary",
            "income",
            "earned",
            "received",
            "got",
            "credited",
            "bonus",
            "profit",
        ]

    def parse_message(self, message: str, user_id: Optional[str] = None):
        """Parse the message and extract transaction details."""

        if not message or not message.strip():
            raise ValueError("Message cannot be empty")

        try:
            logger.info(f"Attempting to parse message with LLM : {message}")
            ai_result = llm_service.parse_message_with_llm(message , user_id=user_id)
            logger.info(
                f"LLM parsed message successfully with result: {ai_result} and is_multiple: {ai_result['is_multiple'] if ai_result else False}"
            )
            return ai_result
        except Exception as e:
            logger.warning(
                f"Error parsing message with LLM , falling back to regex: {e}"
            )
            pass
        message = message.lower().strip()

        amount = self._extract_amount(message)
        if not amount:
            raise ValueError("No amount found in the message")

        if amount < 0.01 or amount > 10000:
            raise ValueError("Amount must be between 0.01 and 10000")

        transaction_type = self._determine_transaction_type(message)

        category = self._determine_category(message, transaction_type)

        description = self._generate_description(
            message, amount, category, transaction_type.value
        )

        confidence = self._calculate_confidence(message, amount, category)

        return {
            "amount": float(amount),
            "transaction_type": transaction_type.value,
            "category": category,
            "description": description,
            "confidence": confidence,
        }

    def _extract_amount(self, message: str) -> Optional[Decimal]:
        for pattern in self.currency_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(",", "")

                if "k" in pattern and "k" in message:
                    try:
                        base_amount = float(amount_str)
                        return Decimal(str(base_amount * 1000))
                    except (ValueError, TypeError):
                        continue

                try:
                    return Decimal(amount_str)
                except ValueError:
                    continue
        return None

    def _determine_transaction_type(self, message: str) -> TransactionType:
        for indicator in self.income_indicators:
            if indicator in message:
                return TransactionType.INCOME

        for indicator in self.expense_indicators:
            if indicator in message:
                return TransactionType.EXPENSE

        return TransactionType.EXPENSE

    def _determine_category(
        self, message: str, transaction_type: TransactionType
    ) -> str:
        if transaction_type == TransactionType.INCOME:
            return "income"

        # For expenses, find matching category
        for category, keywords in self.category_keywords.items():
            if category == "other":
                continue

            for keyword in keywords:
                if keyword.lower() in message.lower():
                    return category

        return "other"  # Default fallback

    def _generate_description(
        self, message: str, amount: Decimal, category: str, transaction_type: str
    ) -> str:

        clean_msg = message
        for pattern in self.currency_patterns:
            clean_msg = re.sub(pattern, "", clean_msg, flags=re.IGNORECASE)

        # Remove common words and clean up
        clean_msg = re.sub(r"\b(spent|paid|bought|for|on|of)\b", "", clean_msg)
        clean_msg = re.sub(r"\s+", " ", clean_msg).strip()

        # Capitalize first letter
        if clean_msg:
            return clean_msg.capitalize()

        return f"{transaction_type.capitalize()} of {amount} in {category}"

    def _calculate_confidence(
        self, message: str, amount: Decimal, category: str
    ) -> float:
        """Calculate confidence score for the parsing result"""

        confidence = 0.5

        if any(
            ind in message for ind in self.income_indicators + self.expense_indicators
        ):
            confidence += 0.2

        if category != "other":
            confidence += 0.2

        if 10 <= amount <= 100000:
            confidence += 0.1

        return min(confidence, 1.0)


message_parser = MessageParser()
