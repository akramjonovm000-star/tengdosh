import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

class PdfService:
    @staticmethod
    def generate_reference_pdf(student_name: str, hemis_id: str, faculty: str, level: str, courses: str = "3"):
        """
        Generates a PDF buffer for "O'qish joyidan ma'lumotnoma".
        """
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # NOTE: Fonts might need to be registered if using non-standard.
        # We'll use standard Helvetica for now.
        
        # Header
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2, height - 3 * cm, "O'ZBEKISTON RESPUBLIKASI")
        c.drawCentredString(width / 2, height - 4 * cm, "OLIY TA'LIM, FAN VA INNOVATSIYALAR VAZIRLIGI")
        
        c.setFont("Helvetica", 12)
        c.drawCentredString(width / 2, height - 6 * cm, "Jizzax Davlat Pedagogika Universiteti")
        
        # Title
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width / 2, height - 9 * cm, "MA'LUMOTNOMA")
        
        # Date
        today = datetime.now().strftime("%d.%m.%Y")
        c.setFont("Helvetica", 10)
        c.drawString(16 * cm, height - 10 * cm, f"Sana: {today}")
        
        # Content
        c.setFont("Helvetica", 12)
        text_y = height - 12 * cm
        line_height = 0.8 * cm
        
        c.drawString(3 * cm, text_y, f"Talaba: {student_name}")
        text_y -= line_height
        c.drawString(3 * cm, text_y, f"HEMIS ID: {hemis_id}")
        text_y -= line_height
        c.drawString(3 * cm, text_y, f"Fakultet: {faculty}")
        text_y -= line_height
        c.drawString(3 * cm, text_y, f"Bosqich: {courses}-kurs")
        text_y -= line_height * 2
        
        c.drawString(3 * cm, text_y, "Ushbu ma'lumotnoma talab qilingan joyga taqdim etish uchun berildi.")
        
        # Footer
        c.setFont("Helvetica-Oblique", 10)
        c.drawCentredString(width / 2, 3 * cm, "Ushbu hujjat HEMIS axborot tizimi ma'lumotlari asosida shakllantirildi.")
        c.drawCentredString(width / 2, 2.5 * cm, "TalabaHamkor Tizimi")
        
        c.showPage()
        c.save()
        
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_transcript_pdf(student_name: str, hemis_id: str, faculty: str, level: str, subjects: list):
        """
        Generates a PDF buffer for "Reyting Daftarchasi" (Transcript).
        subjects: list of dicts {"name": "Matematika", "grade": 5, "load": 4} # load is credits or hours
        """
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # --- Header ---
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(width / 2, height - 2.5 * cm, "O'ZBEKISTON RESPUBLIKASI")
        c.drawCentredString(width / 2, height - 3.2 * cm, "OLIY TA'LIM, FAN VA INNOVATSIYALAR VAZIRLIGI")
        
        c.setFont("Helvetica", 11)
        c.drawCentredString(width / 2, height - 4.5 * cm, "Jizzax Davlat Pedagogika Universiteti")
        
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2, height - 6 * cm, "AKADEMIK MA'LUMOTNOMA (TRANSKRIPT)")
        
        # --- Student Info ---
        c.setFont("Helvetica", 10)
        start_y = height - 7.5 * cm
        line_h = 0.6 * cm
        
        c.drawString(2 * cm, start_y, f"Talaba: {student_name}")
        c.drawString(12 * cm, start_y, f"ID: {hemis_id}")
        c.drawString(2 * cm, start_y - line_h, f"Fakultet: {faculty}")
        c.drawString(12 * cm, start_y - line_h, f"Ta'lim turi: {level}")
        
        # --- Table Header ---
        table_y = start_y - 2.5 * cm
        c.setFont("Helvetica-Bold", 10)
        c.rect(2 * cm, table_y, 17 * cm, 0.8 * cm, stroke=1, fill=0)
        
        # Cols: | # | Fan Nomi (10cm) | Kredit | Baho |
        c.drawString(2.3 * cm, table_y + 0.25 * cm, "#")
        c.drawString(3.5 * cm, table_y + 0.25 * cm, "Fan Nomi")
        c.drawString(14 * cm, table_y + 0.25 * cm, "Kredit")
        c.drawString(17 * cm, table_y + 0.25 * cm, "Baho")
        
        # --- Table Content ---
        c.setFont("Helvetica", 9)
        current_y = table_y
        row_h = 0.7 * cm
        
        index = 1
        for subj in subjects:
            current_y -= row_h
            if current_y < 3 * cm: # New Page Check
                c.showPage()
                current_y = height - 3 * cm
                c.setFont("Helvetica", 9)
            
            c.rect(2 * cm, current_y, 17 * cm, row_h, stroke=1, fill=0)
            
            c.drawString(2.3 * cm, current_y + 0.2 * cm, str(index))
            
            name = subj.get("name", "-")[:45] # Truncate
            c.drawString(3.5 * cm, current_y + 0.2 * cm, name)
            
            c.drawString(14.5 * cm, current_y + 0.2 * cm, str(subj.get("load", "-")))
            c.drawString(17.5 * cm, current_y + 0.2 * cm, str(subj.get("grade", "0")))
            
            index += 1
            
        # --- Footer ---
        c.setFont("Helvetica-Oblique", 8)
        c.drawCentredString(width / 2, 2 * cm, "Ushbu hujjat 'TalabaHamkor' tizimi orqali avtomatlashtirilgan holda shakllantirildi.")
        
        c.showPage()
        c.save()
        
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_study_sheet_pdf(student_name: str, hemis_id: str, faculty: str, level: str, subjects: list, semester: str):
        """
        Generates a PDF buffer for "O'quv varaqa" (Study Sheet).
        """
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # --- Header ---
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(width / 2, height - 2.5 * cm, "O'ZBEKISTON RESPUBLIKASI")
        c.drawCentredString(width / 2, height - 3.2 * cm, "OLIY TA'LIM, FAN VA INNOVATSIYALAR VAZIRLIGI")
        
        c.setFont("Helvetica", 11)
        c.drawCentredString(width / 2, height - 4.5 * cm, "Jizzax Davlat Pedagogika Universiteti")
        
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2, height - 6 * cm, "O'QUV VARAQA")
        
        # --- Student Info ---
        c.setFont("Helvetica", 10)
        start_y = height - 7.5 * cm
        line_h = 0.6 * cm
        
        c.drawString(2 * cm, start_y, f"Talaba: {student_name}")
        c.drawString(12 * cm, start_y, f"ID: {hemis_id}")
        c.drawString(2 * cm, start_y - line_h, f"Fakultet: {faculty}")
        c.drawString(12 * cm, start_y - line_h, f"Ta'lim turi: {level}")
        c.drawString(2 * cm, start_y - line_h * 2, f"Semestr: {semester}")
        
        # --- Table Header ---
        table_y = start_y - 3 * cm
        c.setFont("Helvetica-Bold", 10)
        c.rect(2 * cm, table_y, 17 * cm, 0.8 * cm, stroke=1, fill=0)
        
        # Cols: | # | Fan Nomi (10cm) | Kredit | Yuklama |
        c.drawString(2.3 * cm, table_y + 0.25 * cm, "#")
        c.drawString(3.5 * cm, table_y + 0.25 * cm, "Fan Nomi")
        c.drawString(14 * cm, table_y + 0.25 * cm, "Kredit")
        c.drawString(17 * cm, table_y + 0.25 * cm, "Yuklama")
        
        # --- Table Content ---
        c.setFont("Helvetica", 9)
        current_y = table_y
        row_h = 0.7 * cm
        
        index = 1
        for subj in subjects:
            current_y -= row_h
            if current_y < 3 * cm: # New Page Check
                c.showPage()
                current_y = height - 3 * cm
                c.setFont("Helvetica", 9)
            
            c.rect(2 * cm, current_y, 17 * cm, row_h, stroke=1, fill=0)
            
            c.drawString(2.3 * cm, current_y + 0.2 * cm, str(index))
            
            name = subj.get("name", "-")[:45] # Truncate
            c.drawString(3.5 * cm, current_y + 0.2 * cm, name)
            
            c.drawString(14.5 * cm, current_y + 0.2 * cm, str(subj.get("credit", "-")))
            c.drawString(17.5 * cm, current_y + 0.2 * cm, str(subj.get("load", "-")))
            
            index += 1
            
        # --- Footer ---
        c.setFont("Helvetica-Oblique", 8)
        c.drawCentredString(width / 2, 2 * cm, "Ushbu hujjat 'TalabaHamkor' tizimi orqali avtomatlashtirilgan holda shakllantirildi.")
        
        c.showPage()
        c.save()
        
        buffer.seek(0)
        return buffer
