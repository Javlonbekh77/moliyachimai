import os
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    telegram_bot_token: str = Field(..., alias="TELEGRAM_BOT_TOKEN")
    gemini_api_key: str = Field(..., alias="GEMINI_API_KEY")
    groq_api_key: str = Field(..., alias="GROQ_API_KEY")
    google_project_id: str = Field(default="890658793880", alias="GOOGLE_PROJECT_ID")
    firebase_service_account_path: str = Field(default="firebase-service-account.json", alias="FIREBASE_SERVICE_ACCOUNT_PATH")
    
    # Optional Webhook configs for Vercel
    webhook_url: str = Field(default="", alias="WEBHOOK_URL")
    webhook_secret: str = Field(default="moliyachim_secret_key_2026", alias="WEBHOOK_SECRET")
    
    # Models
    groq_model: str = Field(default="qwen/qwen3.8-27b", alias="GROQ_MODEL")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
