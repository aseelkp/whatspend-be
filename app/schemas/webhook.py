from typing import Optional
from pydantic import BaseModel

class WhatsAppWebhook(BaseModel):
    From: str
    To: str
    Body: str
    MessageSid: Optional[str] = None
    AccountSid: Optional[str] = None
    NumMedia: Optional[str] = "0"

class WebhookResponse(BaseModel):
    status: str
    message: str
    transaction_created: Optional[bool] = False