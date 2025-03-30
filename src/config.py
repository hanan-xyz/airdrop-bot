import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class Config:
    BOT_TOKEN: str = os.getenv('BOT_TOKEN') or ''
    SPREADSHEET_ID: str = os.getenv('SPREADSHEET_ID') or ''
    SHEET_NAME: str = 'airdropbot'
    CREDENTIALS_PATH: str = os.getenv('CREDENTIALS_PATH', 'credentials.json')
    RATE_LIMIT_SECONDS: int = 5
    CONVERSATION_TIMEOUT: int = 600  # 10 menit

    @classmethod
    def validate(cls) -> None:
        """Validasi konfigurasi penting"""
        missing = []
        if not cls.BOT_TOKEN:
            missing.append('BOT_TOKEN')
        if not cls.SPREADSHEET_ID:
            missing.append('SPREADSHEET_ID')
        if missing:
            raise ValueError(f"Variabel lingkungan berikut hilang: {', '.join(missing)}")
