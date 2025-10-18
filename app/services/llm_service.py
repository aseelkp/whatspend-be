import json
from multiprocessing import Value
from google.genai.types import GenerateContentConfig, GenerateContentResponse


from typing import Optional, Dict, Any
import openai
import logging
from app.api.v1.endpoints import categories
from app.core.database import SessionLocal
from app.models.category import Category
from google import genai
from google.genai import types
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        try:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            self.model = "gemini-2.5-flash"
            self._category_cache = None
            self._cache_timestamp = None
            logger.info(f"LLMService initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Error initializing LLMService: {e}")
            raise e

    def parse_message_with_llm(self, message: str , user_id: Optional[str] = None):

        if not self.client:
            logger.error("Client not initialized")
            return None

        try:
            prompt = self._create_extraction_prompt(message , user_id=user_id)

            response: GenerateContentResponse = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                ),
            )

            parsed_data = (
                self._parse_gemini_response(response.text) if response.text else None
            )

            logger.info(f"Gemini parsed message successfully: {parsed_data}")
            return parsed_data
        except Exception as e:
            logger.error(f"Error parsing message with Gemini: {e}")
            raise ValueError(f"Error parsing message with Gemini: {e}")

    def _create_extraction_prompt(self, message: str, user_id: Optional[str] = None) -> str:

        db = SessionLocal()
        try:
            categories = self._get_valid_categories(user_id=user_id)

            categories_text = "\n".join(
                [f"{i+1}. {cat}" for i, cat in enumerate(categories)]
            )
        finally:
            db.close()

        prompt = f"""You are a financial transaction parser. Extract transaction data and return JSON.

                    CRITICAL - Category Selection Rules:
                    You MUST use one of these EXACT category names:
                    {categories_text}

                    Additional category guidance:
                    - "groceries" - food, meals, restaurants, coffee, snacks, dining, grocery shopping
                    - "transportation" - uber, taxi, bus, metro, petrol, fuel, parking, travel
                    - "entertainment" - movies, netflix, games, concerts, shows, parties
                    - "healthcare" - medicine, doctor, hospital, pharmacy, medical appointments
                    - "other" - use ONLY if nothing else matches

                    DO NOT use any other category names. DO NOT create new categories.

                    Amount Formats: ₹500, Rs. 1000, 500 rupees, 2k (=2000), 1.5k (=1500)

                    Transaction Types:
                    - "EXPENSE" for spending money
                    - "INCOME" for receiving money

                    User message: "{message}"

                    For MULTIPLE transactions, extract ALL of them.

                    Response format:
                    {{
                        "transactions": [
                            {{
                                "amount": <number>,
                                "transaction_type": "EXPENSE" or "INCOME",
                                "category": "<exact category name from list above>",
                                "description": "<short description>",
                                "confidence": <0.0 to 1.0>
                            }}
                        ]
                    }}

                    Examples:
                    "Coffee 80" → {{"transactions": [{{"amount": 80, "transaction_type": "EXPENSE", "category": "groceries", "description": "Coffee", "confidence": 0.9}}]}}

                    "Uber 120" → {{"transactions": [{{"amount": 120, "transaction_type": "EXPENSE", "category": "transportation", "description": "Uber ride", "confidence": 0.9}}]}}

                    Parse the message. Return ONLY valid JSON."""

        return prompt

    def _parse_gemini_response(self, response: str):
        try:
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:].strip()
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]

            cleaned_response = cleaned_response.strip()

            data = json.loads(cleaned_response)

            if "transactions" in data:
                transactions = data["transactions"]

                validated_transactions = []

                for t in transactions:
                    validated_t = self._validate_transaction(t)
                    validated_transactions.append(validated_t)

                return {
                    "transactions": validated_transactions,
                    "is_multiple": len(transactions) > 1,
                }
            else:
                validated_transaction = self._validate_transaction(data)
                return {"transactions": [validated_transaction], "is_multiple": False}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response: {response}")
            raise ValueError(f"Invalid JSON response: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            raise ValueError(f"Invalid response: {str(e)}")

    def _validate_transaction(self, transaction: Dict):

        required_field = [
            "amount",
            "transaction_type",
            "category",
            "description",
            "confidence",
        ]
        for field in required_field:
            if field not in transaction:
                raise ValueError(f"Missing required field: {field}")

        if (
            not isinstance(transaction["amount"], (int, float))
            or transaction["amount"] <= 0
        ):
            raise ValueError("Invalid amount")

        if transaction["transaction_type"] not in ["EXPENSE", "INCOME"]:
            raise ValueError("Invalid transaction type")

        valid_categories = self._get_valid_categories(user_id=transaction["user_id"])
        if transaction["category"].lower() not in valid_categories:
            logger.warning(f"Invalid category: {transaction['category']}")
            transaction["category"] = "other"

        if not 0.0 <= transaction["confidence"] <= 1.0:
            raise ValueError("Invalid confidence score")

        return {
            "amount": float(transaction["amount"]),
            "transaction_type": transaction["transaction_type"],
            "category": transaction["category"].lower(),
            "description": transaction["description"],
            "confidence": float(transaction["confidence"]),
        }

    def _get_valid_categories(self, force_refresh: bool = False, user_id: Optional[str] = None):

        from datetime import datetime, timedelta

        if not force_refresh and self._category_cache is not None:
            if (
                self._cache_timestamp
                and datetime.now() - self._cache_timestamp < timedelta(minutes=5)
            ):
                return self._category_cache
        db = SessionLocal()
        try:
            if user_id:
                categories = db.query(Category).filter(
                    Category.is_active == True,
                    Category.user_id == user_id
                ).all()
                if not categories:
                    # fallback to default, active categories
                    categories = db.query(Category).filter(
                        Category.is_active == True,
                        Category.is_default == True
                    ).all()
            else:
                categories = db.query(Category).filter(
                    Category.is_active == True,
                    Category.is_default == True
                ).all()
            self._category_cache = [cat.name for cat in categories]
            self._cache_timestamp = datetime.now()
            logger.info(
                f"Updated category cache with {len(self._category_cache)} categories"
            )
            return self._category_cache
        except Exception as e:
            logger.error(f"Error getting valid categories: {e}")
            return ["other"]
        finally:
            db.close()


llm_service = LLMService()
