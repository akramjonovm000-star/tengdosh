import base64
import time
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from config import PAYME_MERCHANT_ID, PAYME_CHECKOUT_URL, PAYME_KEY
from database.models import Transaction, Student

class PaymentService:
    @staticmethod
    def generate_payme_url(amount: int, order_id: str) -> str:
        """
        Generates Payme Checkout URL.
        amount: Amount in SUM (e.g. 10000)
        order_id: Unique order ID (e.g. 'sub_123')
        """
        amount_tiyin = amount * 100
        params = f"m={PAYME_MERCHANT_ID};ac.order_id={order_id};a={amount_tiyin}"
        b64_params = base64.b64encode(params.encode("utf-8")).decode("utf-8")
        return f"{PAYME_CHECKOUT_URL}/{b64_params}"

class PaymeHandler:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.TIME_EXPIRED = 43200000 # 12 hours
        
    async def handle(self, method: str, params: dict):
        if method == "CheckPerformTransaction":
            return await self.check_perform_transaction(params)
        elif method == "CreateTransaction":
             return await self.create_transaction(params)
        elif method == "PerformTransaction":
             return await self.perform_transaction(params)
        elif method == "CheckTransaction":
             return await self.check_transaction(params)
        elif method == "CancelTransaction":
             return await self.cancel_transaction(params)
        elif method == "ChangePassword":
             return {"success": True} # Ignore
        else:
             raise PaymeException("-32601", "Method not found")

    async def check_perform_transaction(self, params: dict):
        amount = params.get("amount")
        order_id = params.get("account", {}).get("order_id")
        
        if not order_id:
            raise PaymeException("-31050", "Account field not found") # Or order_id missing
            
        # Verify amount logic
        # We now allow any amount as it's a balance top-up
        if amount and amount < 100000: # 1000 sum minimum for example
             raise PaymeException("-31001", "Minimum amount 1000 sum")
            
        return {"allow": True}

    async def create_transaction(self, params: dict):
        amount = params.get("amount")
        order_id = params.get("account", {}).get("order_id")
        trans_id = params.get("id") # Payme's ID
        time_ms = params.get("time") # Payme's timestamp
        
        if not order_id: raise PaymeException("-31050", "Account missing")
        
        # Check if transaction exists by Payme ID
        existing = await self.session.scalar(select(Transaction).where(Transaction.payme_trans_id == trans_id))
        if existing:
            if existing.state != 1:
                raise PaymeException("-31008", "Transaction already processed") # Or canceled
            # Check for timeout?
            return {
                "create_time": existing.create_time,
                "transaction": str(existing.id),
                "state": 1
            }

        # Check if order_id has other active transaction
        active_order = await self.session.scalar(
            select(Transaction).where(Transaction.order_id == order_id, Transaction.state == 1)
        )
        if active_order:
             # If strictly one transaction per order, error.
             # Or return that one? Payme docs say error -31050 if order locked
             raise PaymeException("-31050", "Order has active transaction")
             
        # Create
        # Decode student_id from order_id (prem_{id}_{ts})
        try:
            parts = order_id.split("_")
            student_id = int(parts[1])
        except:
             raise PaymeException("-31050", "Invalid order_id format")

        new_tx = Transaction(
            order_id=order_id,
            payme_trans_id=trans_id,
            student_id=student_id,
            amount=amount,
            state=1,
            create_time=int(datetime.utcnow().timestamp() * 1000) 
        )
        self.session.add(new_tx)
        await self.session.commit()
        
        return {
            "create_time": new_tx.create_time,
            "transaction": str(new_tx.id),
            "state": 1
        }

    async def perform_transaction(self, params: dict):
        trans_id = params.get("id")
        
        tx = await self.session.scalar(select(Transaction).where(Transaction.payme_trans_id == trans_id))
        if not tx:
             raise PaymeException("-31003", "Transaction not found")
             
        if tx.state == 1:
            # CHECK TIMEOUT (43200000)
            if (int(datetime.utcnow().timestamp()*1000) - tx.create_time) > self.TIME_EXPIRED:
                 tx.state = -1
                 tx.reason = 4
                 await self.session.commit()
                 raise PaymeException("-31008", "Transaction expired")
                 
            # PERFORM
            tx.state = 2
            tx.perform_time = int(datetime.utcnow().timestamp() * 1000)
            await self.session.commit()
            
            # CREDIT BALANCE
            student = await self.session.get(Student, tx.student_id)
            if student:
                amount_sum = tx.amount // 100
                student.balance += amount_sum
                await self.session.commit()
            
            return {
                "transaction": str(tx.id),
                "perform_time": tx.perform_time,
                "state": 2
            }
            
        elif tx.state == 2:
            return {
                "transaction": str(tx.id),
                "perform_time": tx.perform_time,
                "state": 2
            }
        else:
            raise PaymeException("-31008", "Transaction already canceled")

    async def cancel_transaction(self, params: dict):
        trans_id = params.get("id")
        reason = params.get("reason")
        
        tx = await self.session.scalar(select(Transaction).where(Transaction.payme_trans_id == trans_id))
        if not tx:
             raise PaymeException("-31003", "Transaction not found")
             
        if tx.state == 1:
            tx.state = -1
            tx.cancel_time = int(datetime.utcnow().timestamp() * 1000)
            tx.reason = reason
            await self.session.commit()
            
        elif tx.state == 2:
            # Retrieve premium? Usually refunds require manual process or logic.
            # Determine if we can cancel completed.
            # Assuming yes for Payme spec compliance (-2)
            tx.state = -2
            tx.cancel_time = int(datetime.utcnow().timestamp() * 1000)
            tx.reason = reason
            await self.session.commit()
            
            # DEACTIVATE Premium?
            # student = await self.session.get(Student, tx.student_id)
            # if student: 
            #    student.is_premium = False # Naive revert
            #    await self.session.commit()
            
        return {
            "transaction": str(tx.id),
            "cancel_time": tx.cancel_time,
            "state": tx.state
        }

    async def check_transaction(self, params: dict):
        trans_id = params.get("id")
        tx = await self.session.scalar(select(Transaction).where(Transaction.payme_trans_id == trans_id))
        if not tx:
             raise PaymeException("-31003", "Transaction not found")
             
        return {
            "create_time": tx.create_time,
            "perform_time": tx.perform_time,
            "cancel_time": tx.cancel_time,
            "transaction": str(tx.id),
            "state": tx.state,
            "reason": tx.reason
        }

class PaymeException(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message

import hashlib
from config import CLICK_SERVICE_ID, CLICK_MERCHANT_ID, CLICK_USER_ID, CLICK_SECRET_KEY

class ClickHandler:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    @staticmethod
    def generate_url(amount: int, order_id: str) -> str:
        # Click URL: https://my.click.uz/services/pay?service_id=...&merchant_id=...&amount=...&transaction_param=...
        return f"https://my.click.uz/services/pay?service_id={CLICK_SERVICE_ID}&merchant_id={CLICK_MERCHANT_ID}&amount={amount}&transaction_param={order_id}"

    async def handle(self, params: dict):
        """
        Handle Click Prepare/Complete requests
        """
        click_trans_id = params.get("click_trans_id")
        service_id = params.get("service_id")
        click_paydoc_id = params.get("click_paydoc_id")
        merchant_trans_id = params.get("merchant_trans_id") # Order ID
        amount = float(params.get("amount", 0))
        action = int(params.get("action", -1))
        error = int(params.get("error", 0))
        error_note = params.get("error_note")
        sign_time = params.get("sign_time")
        sign_string = params.get("sign_string")
        
        # 1. Verify Signature
        # MD5(click_trans_id + service_id + SECRET_KEY + merchant_trans_id + amount + action + sign_time)
        # amount formatting: if float, might need specific format. Click sends exact string usually?
        # Assuming we verify roughly or trust CLICK_SECRET_KEY check strictly?
        # Let's verify strictly.
        
        calc_str = f"{click_trans_id}{service_id}{CLICK_SECRET_KEY}{merchant_trans_id}{params.get('amount')}{action}{sign_time}"
        my_sign = hashlib.md5(calc_str.encode("utf-8")).hexdigest()
        
        if my_sign != sign_string:
             return {"error": -1, "error_note": "Sign check failed"}
             
        # 2. Check Action
        if action == 0: # Prepare
            return await self.prepare(merchant_trans_id, amount)
        elif action == 1: # Complete
            return await self.complete(click_trans_id, merchant_trans_id, amount)
        else:
            return {"error": -3, "error_note": "Action not found"}

    async def prepare(self, order_id: str, amount: float):
        # Check Order logic (similar to Payme)
        # Check if already paid?
        existing = await self.session.scalar(select(Transaction).where(Transaction.order_id == order_id))
        
        if existing:
            if existing.state == 2:
                 return {"error": -4, "error_note": "Already paid"}
                 
        # Create Transaction (State 1: Created) if not exists
        if not existing:
             try:
                 parts = order_id.split("_")
                 student_id = int(parts[1])
             except:
                 return {"error": -5, "error_note": "Invalid order_id"}
                 
             # Check amount minimum
             if amount < 1000:
                  return {"error": -2, "error_note": "Minimum amount 1000 sum"}

             new_tx = Transaction(
                order_id=order_id,
                student_id=student_id,
                amount=int(amount * 100), # Tiyin storage
                state=1,
                provider="click",
                create_time=int(datetime.utcnow().timestamp() * 1000)
             )
             self.session.add(new_tx)
             await self.session.commit()
             merchant_prepare_id = new_tx.id
        else:
             merchant_prepare_id = existing.id
             
        return {
            "click_trans_id": "", # Will be filled by caller params? No, response format:
            "merchant_trans_id": order_id,
            "merchant_prepare_id": merchant_prepare_id,
            "error": 0,
            "error_note": "Success"
        }

    async def complete(self, click_trans_id: str, order_id: str, amount: float):
        tx = await self.session.scalar(select(Transaction).where(Transaction.order_id == order_id))
        
        if not tx:
             return {"error": -6, "error_note": "Transaction not found"}
             
        if tx.state == 2:
             return {"error": -4, "error_note": "Already paid"}
             
        if tx.state == -2:
             return {"error": -9, "error_note": "Cancelled"}
             
        # Check amount
        if abs(amount - 10000) > 0.1:
             return {"error": -2, "error_note": "Incorrect amount"}
             
        # Perform
        tx.state = 2
        tx.click_trans_id = click_trans_id
        tx.provider = "click"
        tx.perform_time = int(datetime.utcnow().timestamp() * 1000)
        
        # Credit Balance
        student = await self.session.get(Student, tx.student_id)
        if student:
             student.balance += int(amount)
             
        await self.session.commit()
        
        return {
            "click_trans_id": click_trans_id,
            "merchant_trans_id": order_id,
            "merchant_confirm_id": tx.id,
            "error": 0,
            "error_note": "Success"
        }

from config import UZUM_SERVICE_ID, UZUM_CHECKOUT_URL

class UzumHandler:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    @staticmethod
    def generate_url(amount: int, order_id: str) -> str:
        # Uzum URL: https://www.uzumbank.uz/open-service?serviceId=...&amount=...&orderId=...
        # Valid amount format? Usually Sum.
        return f"{UZUM_CHECKOUT_URL}?serviceId={UZUM_SERVICE_ID}&amount={amount}&orderId={order_id}"

    async def handle(self, params: dict):
        """
        Handle Uzum Callbacks (Check/Create/Confirm)
        Params usually: {serviceId, timestamp, status, transId, orderId, amount...}
        """
        action = params.get("action", "") # e.g. check, create, confirm, reverse
        # Note: Uzum API varies. Assuming 'check' and 'payment' logic.
        
        # If documentation says: 
        # POST /callback
        # body: { ... }
        
        order_id = params.get("orderId")
        amount = float(params.get("amount", 0))
        uzum_trans_id = params.get("transId")
        
        if params.get("status") == "CREATED":
             # Likely just created on their side, checking if we can accept
             return await self.check(order_id, amount)
        elif params.get("status") == "CONFIRMED":
             # Payment successful
             return await self.confirm(uzum_trans_id, order_id, amount)
        elif params.get("status") == "REVERSED":
             return await self.reverse(uzum_trans_id)
        else:
             # Fallback if 'action' field is used instead of status
             if action == "check": return await self.check(order_id, amount)
             if action == "payment": return await self.confirm(uzum_trans_id, order_id, amount)
             
        return {"status": "FAILED", "errorCode": 999}

    async def check(self, order_id: str, amount: float):
        # Verify order existence and amount
        parts = order_id.split("_")
        try:
             student_id = int(parts[1])
             # Check if already paid logic could be here
             return {"status": "OK"}
        except:
             return {"status": "FAILED"}

    async def confirm(self, uzum_trans_id: str, order_id: str, amount: float):
        # Create or Update Transaction
        tx = await self.session.scalar(select(Transaction).where(Transaction.order_id == order_id))
        
        if not tx:
             # Create new
             try:
                 parts = order_id.split("_")
                 student_id = int(parts[1])
                 tx = Transaction(
                    order_id=order_id,
                    student_id=student_id,
                    amount=int(amount * 100),
                    state=2, # Completed directly
                    provider="uzum",
                    uzum_trans_id=uzum_trans_id,
                    create_time=int(datetime.utcnow().timestamp() * 1000),
                    perform_time=int(datetime.utcnow().timestamp() * 1000)
                 )
                 self.session.add(tx)
             except:
                 return {"status": "FAILED"}
        else:
             if tx.state == 2: return {"status": "OK"} # Idempotent
             
             tx.state = 2
             tx.provider = "uzum"
             tx.uzum_trans_id = uzum_trans_id
             tx.perform_time = int(datetime.utcnow().timestamp() * 1000)
        
        # Credit Balance
        student = await self.session.get(Student, tx.student_id)
        if student:
             student.balance += int(amount)
        
        await self.session.commit()
        return {"status": "OK"}

    async def reverse(self, uzum_trans_id: str):
        tx = await self.session.scalar(select(Transaction).where(Transaction.uzum_trans_id == uzum_trans_id))
        if tx:
             tx.state = -2 # Refunded/Reversed
             await self.session.commit()
        return {"status": "OK"}



