from re import M
import secrets
import json
import logging
import jwt

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.config import settings
from app.models.magic_link import MagicLink
from app.models.user import User
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class AuthService:

    def __init__(self):
        self.magin_link_expiry_minutes = 15

    def generate_magic_link(self, db: Session, phone_number: str):

        clean_phone_number = phone_number.replace(" ", "").replace("-", "")
        if not clean_phone_number.startswith("+"):
            clean_phone_number = "+91" + clean_phone_number

        user = db.query(User).filter(User.phone_number == clean_phone_number).first()
        if not user:
            user = User(phone_number=clean_phone_number, is_active=True)
            db.add(user)
            db.commit()
            db.refresh(user)

        magic_token = secrets.token_urlsafe(32)

        magic_link = MagicLink(
            user_id=user.id,
            token=magic_token,
            expires_at=datetime.utcnow()
            + timedelta(minutes=self.magin_link_expiry_minutes),
        )
        db.add(magic_link)
        db.commit()

        logger.info(f"Generated magic token: {magic_token}")
        return magic_token, str(user.id)

    def create_jwt_token(self, user_id: str) -> str:

        payload = {
            "sub": str(user_id),
            "exp": datetime.utcnow() + timedelta(days=30),
            "iat": datetime.utcnow(),
        }

        token = jwt.encode(
            payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

        return token

    def verify_jwt_token(self, token: str):
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            return payload.get("sub")
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
        except Exception as e:
            raise ValueError(f"Error verifying token: {str(e)}")

    def verify_magic_link(self, db: Session, token: str):

        try:
            magic_link = (
                db.query(MagicLink)
                .filter(
                    MagicLink.token == token,
                    MagicLink.expires_at > datetime.utcnow(),
                    MagicLink.used == False,
                )
                .first()
            )

            if not magic_link:
                raise ValueError("Invalid or expired token")

            magic_link.used = True  # type: ignore
            db.commit()

            logger.info(f"Magic link verified for user: {magic_link.user_id}")
            return str(magic_link.user_id)

        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")


auth_service = AuthService()
