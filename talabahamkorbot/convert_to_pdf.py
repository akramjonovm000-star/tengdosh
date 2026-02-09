from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import re

def create_pdf(input_file, output_file):
    doc = SimpleDocTemplate(output_file, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TitleStyle', parent=styles['Heading1'], fontSize=18, spaceAfter=20, alignment=1))
    styles.add(ParagraphStyle(name='Heading2Style', parent=styles['Heading2'], fontSize=14, spaceBefore=15, spaceAfter=10, textColor=colors.darkblue))
    styles.add(ParagraphStyle(name='Heading3Style', parent=styles['Heading3'], fontSize=12, spaceBefore=10, spaceAfter=5, textColor=colors.black))
    styles.add(ParagraphStyle(name='NormalStyle', parent=styles['Normal'], fontSize=10, leading=14))
    
    # Try to register a font that supports Uzbek/Cyrillic if needed, but standard usually works for Latin-Uzbek.
    # reportlab's standard fonts (Helvetica) don't support all UTF-8 chars well if they are special.
    # But let's try standard first.
    
    story = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    # Simple parser for the specific MD format I generated earlier
    buffer_table = []
    in_table = False
    
    for line in lines:
        line = line.strip()
        
        if not line:
            if in_table and buffer_table:
                # Flush table
                t = Table(buffer_table)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0,0), (-1,0), 12),
                    ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                    ('GRID', (0,0), (-1,-1), 1, colors.black),
                ]))
                story.append(t)
                story.append(Spacer(1, 12))
                buffer_table = []
                in_table = False
            continue
            
        if line.startswith("# 📊"):
            story.append(Paragraph(line.replace("# 📊", "").strip(), styles['TitleStyle']))
            story.append(Spacer(1, 12))
            
        elif line.startswith("## 🏫"):
            story.append(Paragraph(line.replace("## 🏫", "").strip(), styles['Heading2Style']))
            
        elif line.startswith("### 🎓"):
            story.append(Paragraph(line.replace("### 🎓", "").strip(), styles['Heading3Style']))
            
        elif line.startswith("|") and "---" not in line:
            # Table row
            in_table = True
            row_data = [cell.strip() for cell in line.split("|") if cell.strip()]
            buffer_table.append(row_data)
            
        elif line.startswith("**"):
             # Bold text stats
             clean_text = line.replace("**", "<b>", 1).replace("**", "</b>", 1)
             story.append(Paragraph(clean_text, styles['NormalStyle']))
             story.append(Spacer(1, 6))

    doc.build(story)
    print(f"PDF generated: {output_file}")

if __name__ == "__main__":
    create_pdf("/home/user/talabahamkor/talabahamkorbot/jmcu_analytics_report.md", "/home/user/talabahamkor/JMCU_Analytics_Hisobot.pdf")
