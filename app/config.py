import os

class Settings:
    PROJECT_NAME: str = "STB Admin Payment Backend"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:////workspace/scratch/stb_admin.db")
    DEFAULT_HMAC_SECRET: str = "stb_secret_key_2026_super_secure"

settings = Settings()
