from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime

router = APIRouter(prefix="/support", tags=["Support"])
logger = logging.getLogger(__name__)

class SupportMessage(BaseModel):
    name: str
    email: str
    message: str

def send_email_task(msg_data: SupportMessage):
    # Log to file (Fallback)
    try:
        with open("support_requests.txt", "a") as f:
            f.write(f"[{datetime.now()}] From: {msg_data.name} ({msg_data.email})\nMessage: {msg_data.message}\n{'-'*50}\n")
    except Exception as e:
        logger.error(f"Failed to log support message: {e}")

    # Try Email
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT", "587")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    recipient = "akramjonov.m.000@gmail.com"

    if not (smtp_host and smtp_user and smtp_pass):
        logger.warning("SMTP credentials missing. Support message only logged to file.")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = recipient
        msg['Subject'] = f"Support Request from {msg_data.name}"

        body = f"""
        Yangi murojaat keldi!
        
        Ism: {msg_data.name}
        Email: {msg_data.email}
        
        Xabar:
        {msg_data.message}
        """
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_host, int(smtp_port))
        server.starttls()
        server.login(smtp_user, smtp_pass)
        text = msg.as_string()
        server.sendmail(smtp_user, recipient, text)
        server.quit()
        logger.info(f"Support email sent to {recipient}")
    except Exception as e:
        logger.error(f"Failed to send support email: {e}")

@router.post("/send")
async def send_support_message(msg: SupportMessage, background_tasks: BackgroundTasks):
    # We accept the message immediately and process in background
    background_tasks.add_task(send_email_task, msg)
    return {"success": True, "message": "Message received"}
