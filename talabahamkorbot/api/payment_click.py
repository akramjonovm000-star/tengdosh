import hashlib
from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
import os

from database.db_connect import get_db
from database.models import ClickTransaction

click_router = APIRouter(prefix="/payment/click", tags=["Payment Click"])

# In production, these should be loaded from ENV
CLICK_SECRET_KEY = os.getenv("CLICK_SECRET_KEY", "TEST_SECRET_KEY")

def generate_sign_string(trans_id, service_id, secret, merchant_trans_id, amount, action, sign_time, merchant_prepare_id=None):
    amount_str = f"{float(amount):.2f}".replace(".00", "") if float(amount).is_integer() else f"{float(amount):.2f}"
    if merchant_prepare_id is not None:
        raw = f"{trans_id}{service_id}{secret}{merchant_trans_id}{merchant_prepare_id}{amount_str}{action}{sign_time}"
    else:
        raw = f"{trans_id}{service_id}{secret}{merchant_trans_id}{amount_str}{action}{sign_time}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()

@click_router.post("/prepare")
async def prepare_payment(
    request: Request,
    click_trans_id: int = Form(...),
    service_id: int = Form(...),
    click_paydoc_id: int = Form(...),
    merchant_trans_id: str = Form(...),
    amount: float = Form(...),
    action: int = Form(...),
    error: int = Form(...),
    error_note: str = Form(""),
    sign_time: str = Form(...),
    sign_string: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        # 1. Signature check
        calculated_sign = generate_sign_string(
            click_trans_id, service_id, CLICK_SECRET_KEY, 
            merchant_trans_id, amount, action, sign_time
        )
        if calculated_sign != sign_string:
            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "merchant_prepare_id": None,
                "error": -1,
                "error_note": "SIGN CHECK FAILED"
            }
        
        # 2. Check if transaction already exists
        result = await db.execute(select(ClickTransaction).where(ClickTransaction.click_trans_id == click_trans_id))
        existing_tx = result.scalar_one_or_none()
        if existing_tx:
            if existing_tx.status == "completed":
                return {
                    "click_trans_id": click_trans_id,
                    "merchant_trans_id": merchant_trans_id,
                    "merchant_prepare_id": existing_tx.id,
                    "error": -4,
                    "error_note": "Already paid"
                }

        # 3. Create Prepare Record
        new_tx = ClickTransaction(
            click_trans_id=click_trans_id,
            click_paydoc_id=click_paydoc_id,
            merchant_trans_id=merchant_trans_id,
            amount=amount,
            action=action,
            error=0,
            sign_time=sign_time,
            sign_string=sign_string,
            status="preparing"
        )
        db.add(new_tx)
        await db.commit()
        await db.refresh(new_tx)

        return {
            "click_trans_id": click_trans_id,
            "merchant_trans_id": merchant_trans_id,
            "merchant_prepare_id": new_tx.id,
            "error": 0,
            "error_note": "Success"
        }

    except Exception as e:
        logger.error(f"Click Prepare Error: {e}")
        return {
            "click_trans_id": click_trans_id,
            "merchant_trans_id": merchant_trans_id,
            "merchant_prepare_id": None,
            "error": -8,
            "error_note": "Error in request from click"
        }

@click_router.post("/complete")
async def complete_payment(
    request: Request,
    click_trans_id: int = Form(...),
    service_id: int = Form(...),
    click_paydoc_id: int = Form(...),
    merchant_trans_id: str = Form(...),
    merchant_prepare_id: int = Form(...),
    amount: float = Form(...),
    action: int = Form(...),
    error: int = Form(...),
    error_note: str = Form(""),
    sign_time: str = Form(...),
    sign_string: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        # 1. Signature check
        calculated_sign = generate_sign_string(
            click_trans_id, service_id, CLICK_SECRET_KEY, 
            merchant_trans_id, amount, action, sign_time, merchant_prepare_id
        )
        if calculated_sign != sign_string:
            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "merchant_confirm_id": None,
                "error": -1,
                "error_note": "SIGN CHECK FAILED"
            }

        # 2. Find Transaction
        result = await db.execute(select(ClickTransaction).where(ClickTransaction.id == merchant_prepare_id))
        tx = result.scalar_one_or_none()
        
        if not tx:
            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "merchant_confirm_id": None,
                "error": -6,
                "error_note": "Transaction not found"
            }

        if tx.status == "completed":
            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "merchant_confirm_id": tx.id,
                "error": -4,
                "error_note": "Already paid"
            }

        if error < 0:
            tx.status = "cancelled"
            tx.error = error
            tx.error_note = error_note
            await db.commit()
            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "merchant_confirm_id": tx.id,
                "error": -9,
                "error_note": "Transaction cancelled"
            }

        # 3. Complete Transaction
        tx.status = "completed"
        await db.commit()

        # [TODO: Here we should handle actual business logic, e.g. marking contract as paid or storing payment history]

        return {
            "click_trans_id": click_trans_id,
            "merchant_trans_id": merchant_trans_id,
            "merchant_confirm_id": tx.id,
            "error": 0,
            "error_note": "Success"
        }

    except Exception as e:
        logger.error(f"Click Complete Error: {e}")
        return {
            "click_trans_id": click_trans_id,
            "merchant_trans_id": merchant_trans_id,
            "merchant_confirm_id": None,
            "error": -8,
            "error_note": "Error in request from click"
        }
