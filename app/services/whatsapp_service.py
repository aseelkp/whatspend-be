from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException


from app.core.database import SessionLocal
from app.core.config import settings
from app.models.user import User
from app.models.transaction import Transaction
from app.models.category import Category
from app.services.message_parser import message_parser
from app.schemas.transaction import TransactionCreate


class WhatsappService:

    def __init__(self):
        self.confidence_threshold = 0.6

        try:
            self.twilio_client = Client(
                settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN
            )
            self.twilio_whatsapp_number = settings.TWILIO_WHATSAPP_NUMBER

        except Exception as e:
            # Handle exceptions related to Twilio or database
            print(f"Error initializing WhatsappService: {e}")
            self.twilio_client = None

    async def process_incoming_message(
        self, phone_number: str, message_body: str, message_id: str
    ):
        db = SessionLocal()

        try:
            user = self._get_or_create_user(db, phone_number)

            try:
                parsed_data = message_parser.parse_message(message_body)
            except ValueError as e:
                error_msg = f"❌ Sorry , I coudn't find an amount in your message . \n\nTry : 'Spend ₹600 on groceries' "
                await self._send_whatsapp_message(phone_number, error_msg)

                return {
                    "success": False,
                    "error": str(e),
                    "user_id": str(user.id),
                    "response_sent": True,
                }

            if parsed_data["confidence"] >= self.confidence_threshold:
                transaction = self._create_transaction(
                    db, user, parsed_data, raw_message=message_body
                )

                success_msg = self._formate_success_message(parsed_data, transaction)

                await self._send_whatsapp_message(phone_number, success_msg)

                return {
                    "success": True,
                    "user_id": str(user.id),
                    "transaction_id": str(transaction.id),
                    "parsed_data": parsed_data,
                    "confidence": parsed_data["confidence"],
                    "response_sent": True,
                }
            else:
                clarification_msg = self._formate_clarification_message(parsed_data)
                await self._send_whatsapp_message(phone_number, clarification_msg)

                return {
                    "success": False,
                    "error": "Low confidence parsing",
                    "confidence": parsed_data["confidence"],
                    "parsed_data": parsed_data,
                    "response_sent": True,
                }
        except SQLAlchemyError as e:
            db.rollback()
            print(f"SQLAlchemyError occurred: {e}")
            error_msg = "❌ Sorry, something went wrong while processing your request."

            await self._send_whatsapp_message(phone_number, error_msg)

            raise

        except Exception as e:
            print(f"Error occurred: {e}")
            error_msg = "❌ Sorry, something went wrong while processing your request."
            await self._send_whatsapp_message(phone_number, error_msg)

            raise
        finally:
            db.close()

    def _get_or_create_user(self, db: Session, phone_number: str) -> User:

        clean_phone = (
            phone_number.replace("whatsapp:", "")
            if phone_number.startswith("whatsapp:")
            else phone_number.replace(" ", "").replace("-", "")
        )

        if not clean_phone.startswith("+"):
            clean_phone = "+91" + clean_phone

        user = db.query(User).filter(User.phone_number == clean_phone).first()

        if not user:
            new_user = User(phone_number=clean_phone, name=None, is_active=True)

            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            return new_user

        return user

    def _create_transaction(
        self, db: Session, user: User, parsed_data: Dict, raw_message: str
    ) -> Transaction:

        category = (
            db.query(Category).filter(Category.name == parsed_data["category"]).first()
        )

        if not category:
            category = db.query(Category).filter(Category.name == "other").first()

        if not category:
            raise ValueError("No valid category found in database")

        new_transaction = Transaction(
            user_id=user.id,
            category_id=category.id,
            amount=parsed_data["amount"],
            transaction_type=parsed_data["transaction_type"],
            description=parsed_data["description"],
            raw_message=raw_message,
        )

        db.add(new_transaction)
        db.commit()
        db.refresh(new_transaction)

        new_transaction.category = category

        return new_transaction

    def _formate_success_message(
        self, parsed_data: Dict, transaction: Transaction
    ) -> str:

        amount = parsed_data["amount"]
        transaction_type = parsed_data["transaction_type"]

        category_name = (
            transaction.category.name
            if hasattr(transaction, "category") and transaction.category
            else parsed_data["category"]
        )
        category_icon = (
            transaction.category.icon
            if hasattr(transaction, "category") and transaction.category
            else "📝"
        )
        category_display = (
            transaction.category.display_name
            if hasattr(transaction, "category") and transaction.category
            else category_name.title()
        )

        type_word = "income" if transaction_type == "INCOME" else "expense"

        msg = f"✅ Recorded ₹{amount:,.0f} {type_word} for {category_display} {category_icon}\n\n"
        msg += f"Description: {parsed_data['description']}\n"

        return msg

    def _formate_clarification_message(self, parsed_data: Dict) -> str:

        confidence = parsed_data.get("confidence", 0)

        message = f"🤔 I think I understood, but I'm not completely sure (confidence: {confidence:.0%}):\n\n"

        if parsed_data.get("amount"):
            message += f"💰 Amount: ₹{parsed_data['amount']:,.0f}\n"
        if parsed_data.get("category"):
            message += f"📂 Category: {parsed_data['category'].title()}\n"
        if parsed_data.get("transaction_type"):
            message += f"📊 Type: {parsed_data['transaction_type'].title()}\n"

        message += "\n💡 Try being more specific:\n"
        message += "• 'Spent ₹500 on groceries'\n"
        message += "• 'Uber ride cost ₹120'\n"
        message += "• 'Got salary ₹50000'"

        return message

    async def _send_whatsapp_message(self, to_number: str, message: str) -> bool:

        if not self.twilio_client:
            print("Twilio client not initialized")
            return False

        try:
            to_number = (
                f"whatsapp:{to_number}"
                if not to_number.startswith("whatsapp:")
                else to_number
            )

            twilio_message = self.twilio_client.messages.create(
                body=message, from_=self.twilio_whatsapp_number, to=to_number
            )
            print(f"WhatsApp message sent to {to_number}: {twilio_message.sid}")
            return True

        except Exception as e:
            print(f"Error sending WhatsApp message: {e}")
            return False

    async def send_help_message(self, to_number: str) -> bool:
        help_text = """🤖 *WhatsApp Finance Tracker Help*

                I can track your expenses and income! Just send me messages like:

                💸 *Expenses:*
                • "Spent ₹500 on groceries"
                • "Coffee cost 80 rupees"  
                • "Uber ride ₹120"
                • "Electricity bill paid 2000"

                💰 *Income:*
                • "Got salary ₹50000"
                • "Received bonus ₹10000"

                📊 *Commands:*
                • Send "categories" to see all available categories
                • Send "help" to see this message again

                Just describe what you spent money on, and I'll categorize it automatically! 🎯"""
        return await self._send_whatsapp_message(to_number, help_text)


whatsapp_service = WhatsappService()