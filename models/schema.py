from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class TransactionItem(BaseModel):
    type: Literal["expense", "income"] = Field(
        ...,
        description="Type of transaction: strictly 'expense' (xarajat) or 'income' (daromad/kirim)"
    )
    amount: float = Field(
        ...,
        description="Numeric value in currency. Convert words: '45 ming' -> 45000, '1.5 mln' -> 1500000"
    )
    currency: str = Field(
        default="UZS",
        description="Currency code: default 'UZS', or 'USD' if dollar or $ is mentioned"
    )
    category: str = Field(
        ...,
        description="Standard category: e.g. Oziq-ovqat, Transport, Kommunal, Salomatlik, Kiyim, Ta'lim, O'yin-kulgi, Maosh, Biznes, Boshqa"
    )
    description: str = Field(
        ...,
        description="Brief clean description in Uzbek (e.g. Tushlik, Benzin, Oylik)"
    )

class ExtractionResult(BaseModel):
    transactions: List[TransactionItem] = Field(
        default_factory=list,
        description="List of extracted transactions from the audio or text message"
    )
    is_query: bool = Field(
        default=False,
        description="True if the user is asking a financial question, requesting analysis, or seeking advice rather than logging a transaction"
    )
    query_intent: Optional[str] = Field(
        default=None,
        description="If is_query is true: 'analysis', 'today', 'month', 'advice', 'general_question', etc."
    )
