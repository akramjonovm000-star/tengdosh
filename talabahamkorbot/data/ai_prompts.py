
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
        "You are a professional academic assistant specialized in philosophy.\n\n"
        "TASK:\n"
        "Transform the given presentation text into a MINIMAL but COMPLETE student conspectus.\n\n"
        "IMPORTANT:\n"
        "The output must be SHORT and COMPACT, but must NOT lose core meaning.\n\n"
        "CONTENT RULES:\n"
        "- Keep ONLY:\n"
        "  • core definitions\n"
        "  • main concepts\n"
        "  • key classifications\n"
        "  • main schools and philosophers\n"
        "- Remove:\n"
        "  • repetitions\n"
        "  • examples\n"
        "  • long explanations\n"
        "  • decorative text\n"
        "- Do NOT translate word-by-word\n"
        "- Analyze and restructure the content logically\n"
        "- Do NOT invent or distort facts\n"
        "- Prefer generalization over detailing\n"
        "- Preserve academic accuracy\n\n"
        "FORMAT RULES:\n"
        "- Produce TWO versions:\n"
        "  1) Uzbek Latin\n"
        "  2) Uzbek Cyrillic\n"
        "- Use bullet points only\n"
        "- Each bullet: max 1 short line\n"
        "- No paragraphs\n"
        "- No more than 15–18 bullets total\n"
        "- No emojis, no markdown decoration\n\n"
        "STYLE:\n"
        "- Neutral academic\n"
        "- Clear\n"
        "- Exam-ready\n"
        "- No unnecessary words\n"
    )
}
