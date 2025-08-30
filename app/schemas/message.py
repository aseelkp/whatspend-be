from pydantic import BaseModel , ConfigDict
from typing import Optional


class ParseMessageRequest ( BaseModel) : 
    message : str

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "message": "I spent $50 on groceries"
            }
        }
    )

class ParsedMessageData ( BaseModel) :

    amount : Optional[float] = None
    transaction_type : Optional[str] = None
    category : Optional[str] = None
    description : Optional[str] = None
    confidence : Optional[float] = None
    raw_message : Optional[str] = None

    class Config :
        json_schema_extra = {
            "example": {

                "amount": 50.0,
                "transaction_type": "expense",
                "category": "groceries",
                "description": "Grocery shopping",
                "confidence": 0.95,
                "raw_message": "I spent $50 on groceries"
            }
        }

class ParseMessageResponse(BaseModel):
    parsed_data: ParsedMessageData
    raw_message: str
    processing_time_ms: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)