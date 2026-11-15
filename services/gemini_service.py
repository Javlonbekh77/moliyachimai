import json
import logging
from typing import Optional
from google import genai
from google.genai import types
from config import settings
from models.schema import ExtractionResult

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """
Siz foydalanuvchining shaxsiy moliya hisobchisi va tahlilchisisiz.
Foydalanuvchi yuborgan audio (ovozli xabar) yoki matnli xabarni tahlil qiling va O'zbekiston moliyaviy kontekstini to'liq hisobga olgan holda barcha xarajatlar va daromadlarni ajratib oling.

Muhim qoidalar:
1. Bir nechta xarajat/daromad: Agar foydalanuvchi bir ovozda bir nechta narsani aytgan bo'lsa (masalan: "tushlikka 45 ming ketdi, taksiga 15 ming berdim, oylikdan 2 million oldim"), har birini alohida transaction sifatida ajrating.
2. Qiymatlar (amount):
   - "45 ming" -> 45000
   - "1.5 mln", "bir yarim million" -> 1500000
   - "100 dollar", "$100" -> amount: 100, currency: "USD"
   - Default valyuta: "UZS"
3. Turlar (type):
   - "expense": xarajatlar (berdim, ketdi, sarfladim, sotib oldim, to'ladim, ishlatdim)
   - "income": daromadlar (tushdi, oldim, maosh, oylik berishdi, qarzimni qaytarishdi, sovg'a qilishdi)
4. Toifalar (category):
   - Oziq-ovqat (tushlik, bozor, go'sht, non, choyxona, kofe...)
   - Transport (taksi, benzin, metro, avtobus, yo'l kira...)
   - Kommunal (svet, gaz, suv, internet, axlat...)
   - Salomatlik (dori, apteka, doktor, analiz...)
   - Kiyim (oyoq kiyim, shim, ko'ylak, kiyim...)
   - Ta'lim (kurs, repetitor, kitob...)
   - O'yin-kulgi (kino, teatr, konsert, o'yin...)
   - Maosh (oylik, avans, mukofot...)
   - Biznes (savdo, foyda, daromad...)
   - Boshqa (kutilmagan, ehson, sovg'a...)
5. Savol yoki tahlil so'rovi (is_query):
   - Agar foydalanuvchi tranzaksiya kiritmasdan, savol bersa (masalan: "bu oy qancha pul ishlatdim?", "moliya bo'yicha maslahat ber", "eng ko'p nimaga pul ketdi?"), is_query = true deb belgilang va transactions bo'sh qoldiring.
"""

def get_gemini_client():
    return genai.Client(
        api_key=settings.gemini_api_key,
        http_options={"api_version": "v1beta"}
    )


async def process_voice_audio(audio_bytes: bytes, mime_type: str = "audio/ogg") -> ExtractionResult:
    """
    Directly sends audio bytes to Google Gemini API (no disk writing).
    Extracts all transactions and returns structured ExtractionResult.
    """
    client = get_gemini_client()
    audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
    
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=ExtractionResult,
        temperature=0.1
    )
    
    models_to_try = [settings.gemini_model, "gemini-2.5-flash-lite", "gemini-1.5-flash"]
    
    last_err = None
    for m in models_to_try:
        try:
            logger.info(f"Sending audio to Gemini model {m}...")
            resp = client.models.generate_content(
                model=m,
                contents=[
                    audio_part,
                    "Ushbu audio xabarni eshitib, barcha xarajat va daromadlarni ajratib ol va JSON sxemada qaytar."
                ],
                config=config
            )
            if resp.text:
                result_data = json.loads(resp.text)
                return ExtractionResult(**result_data)
        except Exception as e:
            logger.warning(f"Gemini model {m} failed: {e}")
            last_err = e
            continue
            
    raise RuntimeError(f"All Gemini models failed to process audio: {last_err}")
