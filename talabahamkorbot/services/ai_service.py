import logging
import os
from openai import AsyncOpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL_TASKS, OPENAI_MODEL_CHAT, OPENAI_API_KEY_OWNER
from data.ai_prompts import AI_PROMPTS

logger = logging.getLogger(__name__)

# Configure APIs
# Configure APIs
client = None
if OPENAI_API_KEY:
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
else:
    logger.warning("OPENAI_API_KEY topilmadi! Student AI ishlamaydi.")

client_owner = None
if OPENAI_API_KEY_OWNER:
    client_owner = AsyncOpenAI(api_key=OPENAI_API_KEY_OWNER)
elif OPENAI_API_KEY:
    # Fallback to main key if owner key is not dedicated
    client_owner = AsyncOpenAI(api_key=OPENAI_API_KEY)
else:
    logger.warning("OPENAI_API_KEY topilmadi! AI xizmatlari ishlamaydi.")

async def generate_response(prompt_text: str, model: str = OPENAI_MODEL_CHAT, stream: bool = False, system_context: str = None, role: str = 'student', user_name: str = None) -> str:
    """
    Oddiy matnli so'rov yuborish va javob olish.
    Chat uchun default model: gpt-3.5-turbo (Nano)
    Aniq vazifalar uchun: gpt-4o-mini (Mini)
    
    stream=True -> returns AsyncGenerator
    system_context -> Additional system prompt context (e.g. analytics)
    role -> 'student', 'staff', 'owner', 'admin'
    user_name -> Personalized greeting
    """
    # Select Client based on Role
    active_client = client
    if role in ['owner', 'admin']:
        if client_owner:
            active_client = client_owner
        else:
            return "⚠️ Owner API kaliti sozlanmagan."
    
    if not active_client:
        return "⚠️ Tizimda API kalit sozlanmagan."

    # Personalized Name
    display_name = user_name if user_name else "talaba"

    # Dynamic System Prompt
    if role in ['owner', 'admin']:
        base_system = (
            "Sen Universitet tizimining boshqaruvchisi yordamchisisan. Sizning ismingiz 'Tengdosh AI yordamchi'. "
            "Sening vazifang - tizim ma'lumotlarini tahlil qilish va aniq hisobotlarni taqdim etish. "
            "Faqat o'zbek tilida, rasmiy va lo'nda javob ber. "
            f"Salomlashganda har doim 'Assalomu alaykum, janob {user_name if user_name else ''}!' deb murojaat qil. "
            "Suhbat davomida esa har doim o'zingni tanishtirishing shart emas."
        )
    elif role == 'staff':
         base_system = (
            "Sen Universitet xodimlari yordamchisisan. Sizning ismingiz 'Tengdosh AI yordamchi'. "
            "Talabalar murojaatlarini tahlil qilishda yordam berasan. "
            "Faqat o'zbek tilida javob ber. "
            "Suhbat boshida o'zingni tanishtir, lekin har bir xabarda shart emas."
         )
    else:
        base_system = (
            "Sen O'zbekistondagi talabalarga yordam beruvchi aqlli botsan. Sizning ismingiz 'Tengdosh AI yordamchi'. "
            "Faqat o'zbek tilida javob ber. Muloyim va aniq bo'l. "
            f"Salomlashganda har doim '{display_name}'ga ismi bilan murojaat qil. "
            "Suhbat boshida (birinchi marta) o'zingni 'Tengdosh AI yordamchisiman' deb tanishtir, lekin chat davomida har bir xabarda buni takrorlash shart emas."
        )
    
    if system_context:
        base_system += f"\n\nQO'SHIMCHA TIZIM MA'LUMOTLARI (Admin uchun):\n{system_context}"

    try:
        if stream:
            try:
                return await active_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": base_system},
                        {"role": "user", "content": prompt_text}
                    ],
                    stream=True
                )
            except Exception as e:
                logger.error(f"AI Stream Error with model {model}: {e}")
                # Fallback to gpt-4o if model is invalid/unavailable
                if model == "gpt-5.2" or "model" in str(e).lower():
                    logger.warning("Falling back to gpt-4o...")
                    return await active_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": base_system},
                            {"role": "user", "content": prompt_text}
                        ],
                        stream=True
                    )
                raise e
        else:
            try:
                completion = await active_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": base_system},
                        {"role": "user", "content": prompt_text}
                    ]
                )
                return completion.choices[0].message.content
            except Exception as e:
                logger.error(f"AI Error with model {model}: {e}")
                if model == "gpt-5.2" or "model" in str(e).lower():
                     logger.warning("Falling back to gpt-4o...")
                     completion = await active_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": base_system},
                            {"role": "user", "content": prompt_text}
                        ]
                    )
                     return completion.choices[0].message.content
                raise e
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
