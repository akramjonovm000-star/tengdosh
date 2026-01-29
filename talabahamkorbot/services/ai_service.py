import logging
import os
from openai import AsyncOpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL_TASKS, OPENAI_MODEL_CHAT
from data.ai_prompts import AI_PROMPTS

logger = logging.getLogger(__name__)

# Configure API
client = None
if OPENAI_API_KEY:
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
else:
    logger.warning("OPENAI_API_KEY topilmadi! AI ishlamaydi.")

async def generate_response(prompt_text: str, model: str = OPENAI_MODEL_CHAT) -> str:
    """
    Oddiy matnli so'rov yuborish va javob olish.
    Chat uchun default model: gpt-3.5-turbo (Nano)
    Aniq vazifalar uchun: gpt-4o-mini (Mini)
    """
    if not client:
        return "⚠️ Tizimda API kalit sozlanmagan."

    try:
        completion = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Sen O'zbekistondagi talabalarga yordam beruvchi aqlli botsan. Isming 'TalabaHamkor AI'. Faqat o'zbek tilida javob ber. Muloyim va aniq bo'l. Latex formatidagi formulalarni tushunarli yoz."},
                {"role": "user", "content": prompt_text}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI API Error ({model}): {e}")
        return "⚠️ Kechirasiz, AI xizmatida xatolik yuz berdi."

async def generate_answer_by_key(topic_key: str, custom_prompt: str = None) -> str:
    """
    Kalit so'z (topic_key) bo'yicha tayyor promptni yuborish.
    Agar custom_prompt berilsa, o'shandan foydalanadi (dictionary o'rniga).
    Senariy asosida -> Mini (4o-mini)
    """
    if custom_prompt:
        prompt = custom_prompt
    else:
        prompt = AI_PROMPTS.get(topic_key)
        
    if not prompt:
        return "⚠️ Mavzu bo'yicha ma'lumot topilmadi."
    
    return await generate_response(prompt, model=OPENAI_MODEL_TASKS)

async def summarize_konspekt(text_content: str) -> str:
    """
    Berilgan matnni 'Konspekt' prompti asosida tahlil qilish.
    Konspekt (murakkab) -> Mini (4o-mini)
    """
    base_prompt = AI_PROMPTS.get("konspekt_prompt", "")
    full_prompt = f"{base_prompt}\n\nMATN:\n{text_content}"
    
    return await generate_response(full_prompt, model=OPENAI_MODEL_TASKS)

async def analyze_appeal(text_content: str) -> str:
    """
    Talaba murojaatini (appeal) tahlil qilish.
    Tahlil -> Mini (4o-mini)
    """
    base_prompt = (
        "Quyidagi talaba murojaatini tahlil qil va quyidagi tuzilmada javob ber:\n"
        "1. Murojaat turi (Ariza, Shikoyat, Taklif, Savol)\n"
        "2. Asosiy mazmuni (1-2 gapda)\n"
        "3. Murojaatdagi hissiyot (Ijobiy, Salbiy, Neytral)\n"
        "4. Mas'ul bo'lim (Dekanat, Buxgalteriya, IT, Tyutor, Rahbariyat)\n\n"
        "MUROJAAT:\n"
    )
    full_prompt = f"{base_prompt}{text_content}"
    return await generate_response(full_prompt, model=OPENAI_MODEL_TASKS)

async def generate_reply_suggestion(appeal_text: str) -> str:
    """
    Xodim uchun talaba murojaatiga javob (shablon) taklif qilish.
    Javob yozish -> Mini (4o-mini)
    """
    base_prompt = (
        "Quyidagi talaba murojaatiga rasmiy va muloyim javob xati tayyorlab ber.\n"
        "Javob OTM xodimi nomidan bo'lsin.\n"
        "Agar muammo hal qilinadigan bo'lsa, 'tez orada ko'rib chiqiladi' de.\n"
        "Agar noo'rin bo'lsa, tushuntir.\n\n"
        "MUROJAAT:\n"
    )
    full_prompt = f"{base_prompt}{appeal_text}"
    return await generate_response(full_prompt, model=OPENAI_MODEL_TASKS)
