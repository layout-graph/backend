# Application configurations
import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    app_name: str = "Backend API"
    gemini_api_key: str = os.getenv("GOOGLE_GEMINI_API_KEY", "")

settings = Settings()
