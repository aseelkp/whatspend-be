from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException


from app.api.v1.endpoints import categories
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
            message_clean = message_body.lower().strip()

            if await self._handle_command(message_clean, phone_number, user):
                return {
                    "success": True,
                    "user_id": str(user.id),
                    "response_sent": True,
                    "command_handled": True,
                }
            
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

            if parsed_data and parsed_data["confidence"] >= self.confidence_threshold:
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
                if parsed_data:
                    clarification_msg = self._formate_clarification_message(parsed_data)
                    await self._send_whatsapp_message(phone_number, clarification_msg)

                    return {
                        "success": False,
                        "error": "Low confidence parsing",
                        "confidence": parsed_data["confidence"],
                        "parsed_data": parsed_data,
                        "response_sent": True,
                    }
                else:
                    error_msg = f"❌ Sorry, I couldn't understand your message. \n\nTry: 'Spend ₹600 on groceries'"
                    await self._send_whatsapp_message(phone_number, error_msg)
                    
                    return {
                        "success": False,
                        "error": "Could not parse message",
                        "user_id": str(user.id),
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

    async def _handle_command(
        self, message: str, phone_number: str, user: User
    ) -> bool:
        if message in ["help", "h", "?", "start" , "hi" , "hello"]:
            await self._send_help_message(phone_number)
            return True       

        elif message in ["categories", "cat", "c"]:
            await self._send_category_list(phone_number)
            return True

        elif message in ["summary", "stats", "s"]:
            await self._send_summary(phone_number, user)
            return True

        elif message in ["last", "recent", "l"]:
            await self._send_recent_transactions(phone_number, user)
            return True

        elif message.startswith("delete last"):
            await self._handle_delete_last(phone_number, user)
            return True

        return False

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

    async def _send_help_message(self, to_number: str) -> bool:
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

    async def _send_category_list(self, to_number: str) -> bool:
        db = SessionLocal()

        try:
            categories = (
                db.query(Category)
                .filter(Category.is_active == True)
                .order_by(Category.name)
                .all()
            )

            if not categories:
                return await self._send_whatsapp_message(
                    to_number, "No categories found"
                )

            message = "Here are the available categories:\n\n"

            # formate categories into rows

            for i in range(0, len(categories), 3):
                row_categories = categories[i : i + 3]

                category_text = []
                for category in row_categories:
                    icon = category.icon if category.icon is not None else "📝"
                    display_name = (
                        category.display_name
                        if category.display_name is not None
                        else category.name.title()
                    )
                    category_text.append(f"{icon} {display_name}")

                message += "     ".join(category_text) + "\n"

            message += "\n Just mention any category in your expense message to categorize it automatically"
            message += "\n\n Example: 'Spent ₹500 on groceries'"
            return await self._send_whatsapp_message(to_number, message)

        except Exception as e:
            print(f"Error sending category list: {e}")
            return False
        finally:
            db.close()

    async def _send_summary(self, to_number: str, user: User) -> bool:
        db = SessionLocal()
        try:
            from datetime import datetime, timedelta

            week_start = datetime.now() - timedelta(days=7)

            transactions = (
                db.query(Transaction)
                .filter(
                    Transaction.user_id == user.id, Transaction.created_at >= week_start
                )
                .all()
            )

            if not transactions:
                message = "*Weekly Summary* \n\n No transactions found this week"
                return await self._send_whatsapp_message(to_number, message)

            expenses = [
                t
                for t in transactions
                if getattr(t, "transaction_type", None) == "EXPENSE"
            ]
            income = [
                t
                for t in transactions
                if getattr(t, "transaction_type", None) == "INCOME"
            ]

            total_expenses = sum(float(getattr(t, "amount", 0)) for t in expenses)
            total_income = sum(float(getattr(t, "amount", 0)) for t in income)

            from collections import defaultdict

            category_total = defaultdict(float)
            for t in expenses:
                category = (
                    db.query(Category).filter(Category.id == t.category_id).first()
                )
                if category:
                    category_total[
                        category.display_name or category.name.title()
                    ] += float(getattr(t, "amount", 0))

            top_categories = sorted(
                category_total.items(), key=lambda x: x[1], reverse=True
            )[:3]

            message = f""" *This Week's  Summary* 

                *Expenses:* ₹{total_expenses:,.0f}
                *Income:* ₹{total_income:,.0f}
                *Net:* ₹{total_income - total_expenses:,.0f}

                *Top Expense Categories:*"""

            for category, amount in top_categories:
                message += f"\n• {category}: ₹{amount:,.0f}"

            if len(transactions) > 0:
                message += f"\n\n*Total Transactions:* {len(transactions)}"

            return await self._send_whatsapp_message(to_number, message)
        except Exception as e:
            print(f"Error sending summary: {e}")
            return False
        finally:
            db.close()

    async def _send_recent_transactions(self, to_number: str, user: User):
        db = SessionLocal()
        try:
            recent_transactions = (
                db.query(Transaction)
                .filter(Transaction.user_id == user.id)
                .order_by(Transaction.created_at.desc())
                .limit(5)
                .all()
            )

            if not recent_transactions:
                message = "*Recent Transactions* \n\n No transactions found"
                return await self._send_whatsapp_message(to_number, message)

            message = "*Last 5 Transactions* \n\n"
            for i, t in enumerate(recent_transactions):
                category = (
                    db.query(Category).filter(Category.id == t.category_id).first()
                )
                category_name = category.display_name if category else "Other"
                category_icon = category.icon if category else "📝"

                type_icon = (
                    "💸" if getattr(t, "transaction_type", None) == "EXPENSE" else "💰"
                )
                date_str = t.created_at.strftime("%m/%d")

                message += f"{i+1}. {type_icon} {date_str} - {category_name} {category_icon} - ₹{getattr(t, "amount", 0):,.0f}\n"
                message += f"\n {t.description} ({date_str}) \n"

            await self._send_whatsapp_message(to_number, message)
        except Exception as e:
            print(f"Error sending recent transactions: {e}")
            return False
        finally:
            db.close()

    async def _handle_delete_last(self, to_number: str, user: User):
        db = SessionLocal()
        try:
            last_transaction = (
                db.query(Transaction)
                .filter(Transaction.user_id == user.id)
                .order_by(Transaction.created_at.desc())
                .first()
            )

            if not last_transaction:
                message = "No transactions found to delete"
                return await self._send_whatsapp_message(to_number, message)

            category = (
                db.query(Category)
                .filter(Category.id == last_transaction.category_id)
                .first()
            )
            category_name = category.display_name if category else "Other"

            db.delete(last_transaction)
            db.commit()

            message = f"Deleted last transaction: \n₹{float(getattr(last_transaction, "amount", 0)):,.0f} - {category_name}\n\n✅ Transaction removed successfully!"
            return await self._send_whatsapp_message(to_number, message)
        except Exception as e:
            print(f"Error deleting last transaction: {e}")
            return False
        finally:
            db.close()


whatsapp_service = WhatsappService()
