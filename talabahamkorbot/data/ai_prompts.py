
# AI uchun oldindan tayyorlangan prompt so'rovlari
# Rol va mavzu bo'yicha ajratilgan

AI_PROMPTS = {
    # 🎓 TALABA
    "scholarship": (
        "O'zbekiston OTMlarida amaldagi stipendiya turlari va miqdorlari haqida batafsil ma'lumot ber."
        "3, 4, 5 baho olganda qancha stipendiya beriladi?"
        "Prezident stipendiyasi va nomdor stipendiyalar haqida ham qisqacha aytib o't."
    ),
    "hemis_reset": (
        "Hemis axborot tizimida talaba parolini unutganda uni qayta tiklash bo'yicha qadamma-qadam yo'riqnoma ber."
        "Agar telefon raqam o'zgargan bo'lsa nima qilish kerakligini ham tushuntir."
    ),
    "credit_system": (
        "Kredit-modul tizimi nima ekanligini sodda tilda tushuntir."
        "GPA nima? O'tish ballari qanday hisoblanadi? Bir semestrda necha kredit yig'ish kerak?"
        "Qayta o'qish (retake) qoidalari haqida ham ma'lumot ber."
    ),
    "schedule_info": (
        "Dars jadvali va xonalar qanday taqsimlanishini tushuntir."
        "Hemis tizimidan dars jadvalini qanday ko'rish mumkin?"
    ),

    # 👨‍🏫 TYUTOR
    "student_psychology": (
        "Talabalar bilan ishlashda psixologik yondashuv bo'yicha maslahatlar ber."
        "O'qishga qiziqishi past talabalarni qanday motivatsiya qilish mumkin?"
        "Konfliktli vaziyatlarda tyutor o'zini qanday tutishi kerak?"
    ),
    "activity_grading": (
        "Talabalarning jamoat ishlaridagi faolligini baholash mezonlari qanday bo'lishi kerak?"
        "Qanday faolliklar uchun rag'batlantirish (tashakkurnoma, stipendiya qo'shimchasi) berilishi mumkin?"
    ),

    # 🏛 XODIM (Rahbariyat / Dekanat)
    "labor_laws": (
        "O'zbekiston Mehnat kodeksi bo'yicha OTM xodimlariga mehnat ta'tili berish tartibini tushuntir."
        "Ta'til muddatlari va ta'til puli (otpusknoy) hisoblash qoidalari haqida ma'lumot ber."
    ),
    "kpi_system": (
        "Zamonaviy OTMlarda xodimlar faoliyatini baholash (KPI) tizimi haqida ma'lumot ber."
        "KPI ko'rsatkichlari nimalardan iborat bo'lishi mumkin va u ish haqiga qanday ta'sir qiladi?"
    ),

    # 📝 KONSPEKT (Umumiy prompt)
    "konspekt_prompt": (
        "You are a professional academic assistant specialized in philosophy and Uzbek language.\n\n"
        "TASK:\n"
        "Convert the given philosophy presentation into a MINIMAL and CLEAR student conspectus.\n\n"
        "LANGUAGE RULES:\n"
        "- Output must be ONLY in Uzbek Latin\n"
        "- Input may be in Cyrillic or Latin\n"
        "- Do NOT output Cyrillic under any condition\n\n"
        "CONTENT RULES:\n"
        "- Keep ONLY:\n"
        "  • core definitions\n"
        "  • main concepts\n"
        "  • key classifications\n"
        "  • main philosophical directions\n"
        "- Remove:\n"
        "  • repetitions\n"
        "  • examples\n"
        "  • decorative or secondary text\n"
        "- Do NOT invent facts\n"
        "- Do NOT distort meanings\n"
        "- Prefer generalization over detailing\n"
        "- Preserve academic accuracy\n\n"
        "STYLE & QUALITY RULES:\n"
        "- No spelling mistakes\n"
        "- No stylistic or grammatical errors\n"
        "- Use standard Uzbek academic terminology\n"
        "- Avoid colloquial or mixed-language forms\n"
        "- No Russianisms, no transliteration mistakes\n\n"
        "FORMAT RULES:\n"
        "- Bullet points only\n"
        "- Each bullet max 1 short sentence\n"
        "- No paragraphs\n"
        "- No emojis\n"
        "- No markdown decoration\n"
        "- No more than 15–18 bullets\n\n"
        "IMPORTANT:\n"
        "- Always normalize all terms into correct Uzbek Latin\n"
        "- Replace incorrect or mixed terms with correct academic ones\n"
        "- If a term is ambiguous, choose the academically accepted variant\n"
    )
}
