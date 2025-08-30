# app/api/v1/endpoints/messages.py
from fastapi import APIRouter
from app.services.message_parser import message_parser
from app.core.responses import success, error
from app.schemas.message import (
    ParseMessageRequest,
    ParsedMessageData,
)  # ← Import from schema file
from app.schemas.responses import StandardResponse, ErrorDetail

router = APIRouter()


@router.post("/parse", response_model=StandardResponse)
def parse_message(request: ParseMessageRequest):  # ← Use schema
    """Parse a message to extract transaction details"""

    try:
        if not request.message or not request.message.strip():
            return error(
                message="Message parsing failed",
                errors=[
                    ErrorDetail(
                        field="message",
                        code="required",
                        message="Message cannot be empty",
                    )
                ],
            )

        # Parse the message
        result = message_parser.parse_message(request.message)

        parsed_data = ParsedMessageData(
            amount=result["amount"],
            transaction_type=result["transaction_type"],
            category=result["category"],
            description=result["description"],
            confidence=result["confidence"],
            raw_message=request.message,
        )

        return success(
            message=("Message parsed successfully"),
            data=parsed_data,
        )
    except ValueError as e:
        return error(
            message="Message parsing failed",
            errors=[ErrorDetail(field="message", code="PARSE_ERROR", message=str(e))],
        )
    except Exception as e:
        return error(
            message="Message parsing failed",
            errors=[
                ErrorDetail(
                    field="message",
                    code="INTERNAL_ERROR",
                    message="An unexpected error occurred",
                )
            ],
        )
