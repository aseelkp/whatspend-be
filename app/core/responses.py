from typing import Any, List, Optional
from math import ceil

from app.schemas.responses import StandardResponse, ErrorDetail, PaginationInfo


def success(
    message: str, data: Any = None, pagination: Optional[PaginationInfo] = None
) -> StandardResponse:
    return StandardResponse(
        success=True, message=message, data=data, pagination=pagination, errors=None
    )


def error(message: str, errors: List[ErrorDetail]) -> StandardResponse:
    return StandardResponse(
        success=False, message=message, data=None, pagination=None, errors=errors
    )


def validation_error(validation_errors: List[dict]) -> StandardResponse:
    errors = []
    for err in validation_errors:
        field_name = ".".join(str(loc) for loc in err["loc"][1:])
        errors.append(
            ErrorDetail(
                field=field_name or None, code="validation_error", message=err["msg"]
            )
        )
    return error("Validation failed", errors)


def create_pagination_info(page: int, per_page: int, total: int) -> PaginationInfo:
    return PaginationInfo(
        page=page,
        per_page=per_page,
        total=total,
        total_pages=ceil(total / per_page) if per_page > 0 else 1,
    )
