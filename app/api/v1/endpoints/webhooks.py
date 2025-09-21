from typing import Optional
from fastapi import APIRouter, Form, Request, Response

from app.services.whatsapp_service import whatsapp_service

router = APIRouter()

@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...),
    To: Optional[str] = Form(None),
    AccountSid: Optional[str] = Form(None)
):
    try:

        phone_number = From.replace("whatsapp:", "") if From.startswith("whatsapp:") else From

        if not Body or not Body.strip():
            return Response(content="Invalid request: Body is required", media_type="text/plain", status_code=400)

        result = await whatsapp_service.process_incoming_message(
            phone_number,
            message_body=Body.strip(),
            message_id=MessageSid
        )

        return Response(content="Message processed successfully", media_type="text/plain", status_code=200)
    except Exception as e:
        return Response(content="Error processed", media_type="text/plain", status_code=200)