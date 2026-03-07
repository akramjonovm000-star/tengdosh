import hashlib
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse, Response
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
logger = logging.getLogger(__name__)
import os

from database.db_connect import get_db
from database.models import ClickTransaction

click_router = APIRouter(tags=["Payment Click"])

# In production, these should be loaded from ENV
CLICK_SECRET_KEY = os.getenv("CLICK_SECRET_KEY", "TEST_SECRET_KEY")

def generate_sign_string(trans_id, service_id, secret, merchant_trans_id, amount, action, sign_time, merchant_prepare_id=None, click_paydoc_id=None):
    # Ensure amount matches exactly what Click expects (no .0 if it's an integer)
    try:
        f_amount = float(amount)
        amount_str = str(int(f_amount)) if f_amount.is_integer() else str(amount)
    except Exception:
        amount_str = str(amount)
        
    if merchant_prepare_id is not None:
        raw = f"{trans_id}{service_id}{secret}{merchant_trans_id}{merchant_prepare_id}{amount_str}{action}{sign_time}"
    else:
        raw = f"{trans_id}{service_id}{secret}{merchant_trans_id}{amount_str}{action}{sign_time}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()

@click_router.post("")
@click_router.post("/")
async def click_webhook_main(
    request: Request,
    click_trans_id: str = Form(...),
    service_id: str = Form(...),
    click_paydoc_id: str = Form(...),
    merchant_trans_id: str = Form(...),
    amount: str = Form(...),
    action: int = Form(...),
    error: int = Form(...),
    error_note: str = Form(""),
    sign_time: str = Form(...),
    sign_string: str = Form(...),
    merchant_prepare_id: int = Form(None),
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"CLICK WEBHOOK INCOMING [Action={action}]: trans_id={click_trans_id}, paydoc_id={click_paydoc_id}, merchant_trans_id={merchant_trans_id}, amount={amount}")
    
    if action == 0:
        # --- PREPARE ---
        try:
            # 1. Signature check
            calculated_sign = generate_sign_string(
                click_trans_id, service_id, CLICK_SECRET_KEY, 
                merchant_trans_id, amount, action, sign_time, None, click_paydoc_id
            )
            if calculated_sign != sign_string:
                res = {
                    "click_trans_id": str(click_trans_id),
                    "merchant_trans_id": merchant_trans_id,
                    "merchant_prepare_id": None,
                    "error": -1,
                    "error_note": "SIGN CHECK FAILED"
                }; logger.info(f"CLICK RESPONSE: {res}"); return res
            
            # 2. Check if transaction already exists
            try:
                c_trans_id = int(click_trans_id)
            except ValueError:
                logger.error(f"CLICK PREPARE ERROR: ValueError parsing click_trans_id='{click_trans_id}'")
                res = {
                    "click_trans_id": str(click_trans_id),
                    "merchant_trans_id": merchant_trans_id,
                    "merchant_prepare_id": None,
                    "error": -8,
                    "error_note": "Invalid click_trans_id format"
                }; logger.info(f"CLICK RESPONSE: {res}"); return res
            result = await db.execute(select(ClickTransaction).where(ClickTransaction.click_trans_id == c_trans_id))
            existing_tx = result.scalar_one_or_none()
            if existing_tx:
                if existing_tx.status == "completed":
                    res = {
                        "click_trans_id": str(click_trans_id),
                        "merchant_trans_id": merchant_trans_id,
                        "merchant_prepare_id": existing_tx.id,
                        "error": -4,
                        "error_note": "Already paid"
                    }; logger.info(f"CLICK RESPONSE: {res}"); return res
                elif existing_tx.status == "cancelled":
                    res = {
                        "click_trans_id": str(click_trans_id),
                        "merchant_trans_id": merchant_trans_id,
                        "merchant_prepare_id": existing_tx.id,
                        "error": -9,
                        "error_note": "Transaction cancelled"
                    }; logger.info(f"CLICK RESPONSE: {res}"); return res
                else:
                    res = {
                        "click_trans_id": str(click_trans_id),
                        "merchant_trans_id": merchant_trans_id,
                        "merchant_prepare_id": existing_tx.id,
                        "error": 0,
                        "error_note": "Success"
                    }; logger.info(f"CLICK RESPONSE: {res}"); return res

            # 2.5 Check User exists (like Getinfo)
            try:
                from database.models import Student, Staff
                is_staff = False
                user_obj = None
                if merchant_trans_id.startswith("80000"):
                    user_id = int(str(merchant_trans_id)[5:10])
                    user_result = await db.execute(select(Student).where(Student.id == user_id))
                    user_obj = user_result.scalar_one_or_none()
                    if not user_obj:
                        user_result = await db.execute(select(Staff).where(Staff.id == user_id))
                        user_obj = user_result.scalar_one_or_none()
                        if user_obj: is_staff = True
                else:
                    from sqlalchemy import or_
                    target_id = str(merchant_trans_id)
                    user_result = await db.execute(select(Student).where(
                        or_(
                            Student.hemis_id == target_id,
                            Student.hemis_login == target_id
                        )
                    ))
                    user_obj = user_result.scalar_one_or_none()
                    
                    if not user_obj:
                         staff_result = await db.execute(select(Staff).where(
                             or_(
                                 Staff.employee_id_number == target_id
                             )
                         ))
                         user_obj = staff_result.scalar_one_or_none()
                         
                if not user_obj:
                     res = {
                        "click_trans_id": str(click_trans_id),
                        "merchant_trans_id": merchant_trans_id,
                        "merchant_prepare_id": None,
                        "error": -5,
                        "error_note": "User does not exist by params"
                     }; logger.info(f"CLICK RESPONSE: {res}"); return res
            except ValueError:
                 res = {
                    "click_trans_id": str(click_trans_id),
                    "merchant_trans_id": merchant_trans_id,
                    "merchant_prepare_id": None,
                    "error": -5,
                    "error_note": "User does not exist by params"
                 }; logger.info(f"CLICK RESPONSE: {res}"); return res

            # 3. Create Prepare Record
            try:
                c_paydoc_id = int(click_paydoc_id)
            except ValueError:
                logger.error(f"CLICK PREPARE ERROR: ValueError parsing click_paydoc_id='{click_paydoc_id}'")
                c_paydoc_id = 0
                
            new_tx = ClickTransaction(
                click_trans_id=c_trans_id,
                amount=int(float(amount)),
                action=action,
                click_paydoc_id=c_paydoc_id,
                merchant_trans_id=merchant_trans_id,
                error=0,
                sign_time=sign_time,
                sign_string=sign_string,
                status="preparing"
            )
            db.add(new_tx)
            await db.commit()
            await db.refresh(new_tx)

            res = {
                "click_trans_id": str(click_trans_id),
                "merchant_trans_id": merchant_trans_id,
                "merchant_prepare_id": new_tx.id,
                "error": 0,
                "error_note": "Success"
            }; logger.info(f"CLICK RESPONSE: {res}"); return res

        except Exception as e:
            logger.error(f"Click Prepare Error: {e}")
            res = {
                "click_trans_id": str(click_trans_id),
                "merchant_trans_id": merchant_trans_id,
                "merchant_prepare_id": None,
                "error": -8,
                "error_note": "Error in request from click"
            }; logger.info(f"CLICK RESPONSE: {res}"); return res

    elif action == 1:
        # --- COMPLETE ---
        try:
            # 1. Signature check (Needs merchant_prepare_id)
            calculated_sign = generate_sign_string(
                click_trans_id, service_id, CLICK_SECRET_KEY, 
                merchant_trans_id, amount, action, sign_time, merchant_prepare_id, click_paydoc_id
            )
            
            if calculated_sign != sign_string:
                res = {
                    "click_trans_id": str(click_trans_id),
                    "merchant_trans_id": merchant_trans_id,
                    "merchant_confirm_id": None,
                    "error": -1,
                    "error_note": "SIGN CHECK FAILED"
                }; logger.info(f"CLICK RESPONSE: {res}"); return res
            
            # 2. Check Transaction Exists
            result = await db.execute(select(ClickTransaction).where(ClickTransaction.id == merchant_prepare_id))
            tx = result.scalar_one_or_none()
            if not tx:
                res = {
                    "click_trans_id": str(click_trans_id),
                    "merchant_trans_id": merchant_trans_id,
                    "merchant_confirm_id": None,
                    "error": -6,
                    "error_note": "Transaction does not exist"
                }; logger.info(f"CLICK RESPONSE: {res}"); return res
                
            if tx.status == "completed":
                res = {
                    "click_trans_id": str(click_trans_id),
                    "merchant_trans_id": merchant_trans_id,
                    "merchant_confirm_id": tx.id,
                    "error": -4,
                    "error_note": "Already paid"
                }; logger.info(f"CLICK RESPONSE: {res}"); return res
            elif tx.status == "cancelled":
                res = {
                    "click_trans_id": str(click_trans_id),
                    "merchant_trans_id": merchant_trans_id,
                    "merchant_confirm_id": tx.id,
                    "error": -9,
                    "error_note": "Transaction cancelled"
                }; logger.info(f"CLICK RESPONSE: {res}"); return res
                
            # Check amounts match
            if int(float(amount)) != tx.amount:
                 res = {
                    "click_trans_id": str(click_trans_id),
                    "merchant_trans_id": merchant_trans_id,
                    "merchant_confirm_id": None,
                    "error": -2,
                    "error_note": "Incorrect parameter amount"
                 }; logger.info(f"CLICK RESPONSE: {res}"); return res
                
            # 3. Complete Transaction
            tx.status = "completed"
            
            # 4. Top-up Student/Staff Balance
            # merchant_trans_id might be "click_{id}_{timestamp}" OR just "HEMIS/EMPLOYEE_ID" (Advanced Shop)
            try:
                from database.models import Student, Staff, TgAccount
                from bot import bot
                
                is_staff = False
                user_obj = None
                
                if merchant_trans_id.startswith("80000"):
                    user_id = int(str(merchant_trans_id)[5:10])
                    user_result = await db.execute(select(Student).where(Student.id == user_id))
                    user_obj = user_result.scalar_one_or_none()
                    if not user_obj:
                        user_result = await db.execute(select(Staff).where(Staff.id == user_id))
                        user_obj = user_result.scalar_one_or_none()
                        if user_obj: is_staff = True
                else:
                    from sqlalchemy import or_
                    target_id = str(merchant_trans_id)
                    user_result = await db.execute(select(Student).where(
                        or_(
                            Student.hemis_id == target_id,
                            Student.hemis_login == target_id
                        )
                    ))
                    user_obj = user_result.scalar_one_or_none()
                    
                    if not user_obj:
                         staff_result = await db.execute(select(Staff).where(
                             or_(
                                 Staff.employee_id_number == target_id
                             )
                         ))
                         user_obj = staff_result.scalar_one_or_none()
                         if user_obj:
                             is_staff = True
                             
                if user_obj:
                    user_obj.balance += int(float(amount))
                    logger.info(f"Topped up balance for {'Staff' if is_staff else 'Student'} ID {user_obj.id} by {amount} via Click.")
                    
                    # Try sending a Telegram receipt
                    try:
                        if is_staff:
                            tg_acc_result = await db.execute(select(TgAccount).where(TgAccount.staff_id == user_obj.id))
                        else:
                            tg_acc_result = await db.execute(select(TgAccount).where(TgAccount.student_id == user_obj.id))
                            
                        tg_acc = tg_acc_result.scalar_one_or_none()
                        if tg_acc:
                             receipt_msg = (
                                 f"🧾 <b>To'lov qabul qilindi!</b>\n\n"
                                 f"💳 <b>Tizim:</b> Click\n"
                                 f"💰 <b>Summa:</b> {int(float(amount)):,} so'm\n"
                                 f"🆔 <b>Tranzaksiya:</b> {click_trans_id}\n\n"
                                 f"✅ <i>Sizning balansingiz muvaffaqiyatli to'ldirildi.</i>"
                             )
                             await bot.send_message(tg_acc.telegram_id, receipt_msg, parse_mode="HTML")
                    except Exception as msg_err:
                         logger.error(f"Failed to send Click receipt to user {user_obj.id}: {msg_err}")
                    
                else:
                    logger.warning(f"User not found for Click payment {click_trans_id} via id/hemis_id/employee_id: {merchant_trans_id}")
            except Exception as parse_err:
                 logger.error(f"Failed to parse merchant_trans_id {merchant_trans_id} to credit balance: {parse_err}")

            await db.commit()
            
            res = {
                "click_trans_id": str(click_trans_id),
                "merchant_trans_id": merchant_trans_id,
                "merchant_confirm_id": tx.id,
                "error": 0,
                "error_note": "Success"
            }; logger.info(f"CLICK RESPONSE: {res}"); return res
            
        except Exception as e:
            logger.error(f"Click Complete Error: {e}")
            res = {
                "click_trans_id": str(click_trans_id),
                "merchant_trans_id": merchant_trans_id,
                "merchant_confirm_id": None,
                "error": -8,
                "error_note": "Error in request from click"
            }; logger.info(f"CLICK RESPONSE: {res}"); return res

    else:
        res = {
            "error": -3,
            "error_note": "Action not found"
        }; logger.info(f"CLICK RESPONSE: {res}"); return res

@click_router.post("/getinfo")
async def getinfo_payment(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Click Advanced Shop sending JSON for GetInfo
        data = await request.json()
        
        action = data.get("action")
        params = data.get("params", {})
        
        # Check if user exists based on params provided by Click
        # The key might be 'id', 'client_id', 'user_id' or 'merchant_trans_id'
        
        target_id = None
        for key in ["id", "client_id", "user_id", "merchant_trans_id"]:
            if key in params and params[key]:
                target_id = str(params[key]).strip()
                break
                
        if not target_id:
             res = {
                "error": -8,
                "error_note": "No valid ID provided in params"
            }; logger.info(f"CLICK RESPONSE: {res}"); return res

        try:
            from database.models import Student, Staff
            is_staff = False
            user_obj = None
            
            if target_id.startswith("80000"):
                user_id = int(str(target_id)[5:10])
                result = await db.execute(select(Student).where(Student.id == user_id))
                user_obj = result.scalar_one_or_none()
                if not user_obj:
                    result = await db.execute(select(Staff).where(Staff.id == user_id))
                    user_obj = result.scalar_one_or_none()
                    if user_obj: is_staff = True
            else:
                from sqlalchemy import or_
                # 1. Try finding Student by hemis_id, hemis_login or telegram_id
                stmt = select(Student).where(
                    or_(
                        Student.hemis_id == target_id,
                        Student.hemis_login == target_id
                    )
                )
                result = await db.execute(stmt)
                user_obj = result.scalar_one_or_none()
                
                # 2. Try finding Staff by employee_id_number or telegram_id if no student found
                if not user_obj:
                    stmt_staff = select(Staff).where(
                        or_(
                            Staff.employee_id_number == target_id
                        )
                    )
                    staff_result = await db.execute(stmt_staff)
                    staff_obj = staff_result.scalar_one_or_none()
                    if staff_obj:
                        user_obj = staff_obj
                        is_staff = True
                        
        except ValueError:
            res = {
                "error": -5,
                "error_note": "User does not exist"
            }; logger.info(f"CLICK RESPONSE: {res}"); return res

        if not user_obj:
            res = {
                "error": -5,
                "error_note": "User does not exist"
            }; logger.info(f"CLICK RESPONSE: {res}"); return res

        # 3. Return user info
        response_params = {
            "FIO": user_obj.full_name,
            "Balans(so'm)": str(user_obj.balance)
        }
        
        if is_staff:
            response_params["Xodim ID"] = user_obj.employee_id_number or "Kiritilmagan"
        else:
            response_params["Hemis ID"] = getattr(user_obj, 'hemis_id', "Kiritilmagan")
            
        res = {
            "error": 0,
            "error_note": "Success",
            "params": response_params
        }; logger.info(f"CLICK RESPONSE: {res}"); return res

    except Exception as e:
        logger.error(f"Click Getinfo Error (JSON parsing failed): {e}")
        return {
            "error": -8,
            "error_note": "Error in request from click"
        }
