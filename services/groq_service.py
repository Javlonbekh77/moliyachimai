import json
import logging
from typing import List, Dict, Any, Optional
from groq import Groq
from config import settings
from models.schema import ExtractionResult, TransactionItem

logger = logging.getLogger(__name__)

TEXT_PARSING_SYSTEM_PROMPT = """
Siz foydalanuvchining shaxsiy moliya hisobchisisiz.
Foydalanuvchi yuborgan matnli xabarni tahlil qiling va O'zbekiston moliyaviy kontekstini hisobga olgan holda xarajatlar va daromadlarni ajrating.

Qoidalar:
1. Bir nechta xarajat: Bir qatorda yoki vergul bilan ajratilgan barcha xarajatlarni alohida transaction qiling.
2. Qiymatlar (amount):
   - "45 ming" -> 45000
   - "1.5 mln" -> 1500000
   - "100 dollar", "$100" -> amount: 100, currency: "USD"
   - Default valyuta: "UZS"
3. Turlar:
   - "expense" (xarajat: berdim, ketdi, sotib oldim, to'ladim, ishlatdim yoki oddiygina "non 5000")
   - "income" (daromad: tushdi, oldim, maosh, oylik, qarz qaytdi)
4. Toifalar: Oziq-ovqat, Transport, Kommunal, Salomatlik, Kiyim, Ta'lim, O'yin-kulgi, Maosh, Biznes, Boshqa
5. Agar matnda xarajat yoki daromad yozilmagan bo'lsa, balki savol, tahlil so'rovi yoki oddiy gap bo'lsa:
   is_query = true, transactions = [] qilib bering.

Faqat va faqat JSON obyekt qaytaring.
Format:
{
  "transactions": [
    {
      "type": "expense",
      "amount": 45000,
      "currency": "UZS",
      "category": "Oziq-ovqat",
      "description": "Tushlik"
    }
  ],
  "is_query": false,
  "query_intent": null
}
"""

def get_groq_client():
    return Groq(api_key=settings.groq_api_key)


async def parse_text_transactions(text: str) -> ExtractionResult:
    """
    Parses user text message using Groq ultra-low latency LLM.
    Returns ExtractionResult.
    """
    client = get_groq_client()
    try:
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": TEXT_PARSING_SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=350
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        return ExtractionResult(**data)
    except Exception as e:
        logger.warning(f"Groq parsing error: {e}. Trying fallback...")
        # Fallback to Gemini if Groq fails
        from services.gemini_service import get_gemini_client
        from google.genai import types
        gemini_client = get_gemini_client()
        cfg = types.GenerateContentConfig(
            system_instruction=TEXT_PARSING_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=ExtractionResult,
            temperature=0.1
        )
        resp = gemini_client.models.generate_content(
            model=settings.gemini_model,
            contents=text,
            config=cfg
        )
        return ExtractionResult(**json.loads(resp.text))


async def generate_financial_analysis(
    user_name: str,
    stats: Dict[str, Any],
    recent_transactions: List[Dict[str, Any]],
    user_query: Optional[str] = None
) -> str:
    """
    Generates a personalized, actionable, engaging financial analysis and advice in Uzbek.
    """
    client = get_groq_client()
    
    total_expense = stats.get("total_expense", 0)
    total_income = stats.get("total_income", 0)
    balance = stats.get("balance", 0)
    categories = stats.get("categories", [])
    
    categories_str = "\n".join([f"- {cat}: {amt:,.0f} UZS" for cat, amt in categories]) or "Ma'lumot yo'q"
    
    recent_summary = "\n".join([
        f"- {tx.get('type')}: {tx.get('amount'):,.0f} {tx.get('currency')} | {tx.get('category')} ({tx.get('description')})"
        for tx in recent_transactions[:15]
    ]) or "Hozircha xarajatlar yo'q"
    
    system_prompt = f"""
Siz "Moliyachim" — eng tajribali, do'stona va o'tkir tahlilchi shaxsiy moliyaviy maslahatchisiz.
Foydalanuvchi: {user_name}

Moliya holati:
- Jami daromad: {total_income:,.0f} UZS
- Jami xarajat: {total_expense:,.0f} UZS
- Sof qoldiq (balans): {balance:,.0f} UZS
- Toifalar bo'yicha:
{categories_str}

So'nggi operatsiyalar:
{recent_summary}

Vazifangiz:
Foydalanuvchining so'roviga yoki umumiy holatiga qarab, o'zbek tilida juda tushunarli, motivatsion, aniq raqamlarga asoslangan va chiroyli formatlangan moliyaviy tahlil / maslahat bering.

Tavsiyalar:
1. Raqamlar va foizlarga tayaning (masalan: "Xarajatlaringizning 40% oziq-ovqatga ketmoqda...").
2. Kamchiliklar va "teshik cho'ntak" xarajatlarni muloyim, ammo aniq ko'rsating.
3. 2-3 ta amaliy va bajarish oson bo'lgan maslahat bering (50/30/20 qoidasi yoki kundalik tejash usullari).
4. O'zbekona samimiy, do'stona va ruhlantiruvchi tilda yozing. Telegram emoji belgilaridan chiroyli foydalaning.
"""

    user_prompt = user_query if user_query else "Mening so'nggi xarajatlarimni tahlil qilib, amaliy tavsiyalar va xulosa ber."

    try:
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating analysis: {e}")
        # Fallback to Gemini
        from services.gemini_service import get_gemini_client
        gemini_client = get_gemini_client()
        resp = gemini_client.models.generate_content(
            model=settings.gemini_model,
            contents=f"{system_prompt}\n\nFoydalanuvchi savoli: {user_prompt}"
        )
        return resp.text
