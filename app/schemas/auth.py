

from pydantic import BaseModel, Field


class RequestMagicLinkRequest(BaseModel):
    phone_number : str = Field(..., description="The phone number to request a magic link for")


class VerifyMagicLinkRequest(BaseModel):
    token : str = Field(... , description = "The token to verify the magic link")

class AuthResponse(BaseModel):
    access_token : str 
    token_type : str = "Bearer"
    user_id : str


