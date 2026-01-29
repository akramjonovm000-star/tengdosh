import logging
# Placeholder for Google Sheets Service
# In production, use gspread or google-api-python-client

logger = logging.getLogger(__name__)

async def append_student_to_club_sheet(spreadsheet_url: str, student_data: dict):
    """
    Appends student info to the provided Google Spreadsheet URL.
    student_data: {full_name, faculty, group, phone, ...}
    """
    # TODO: Implement real API call.
    # Requires service_account.json and enabling Sheets API.
    logger.info(f"MOCK: Writing to sheet {spreadsheet_url}: {student_data}")
    return True
