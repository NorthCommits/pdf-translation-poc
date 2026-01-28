import os
from dotenv import load_dotenv

# Load .env from project root (go up two levels from backend/core/)
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(env_path)

class Settings:
    DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
    TEMP_DIR = os.path.join(os.path.dirname(__file__), '..', 'temp')

    def __init__(self):
        # Create temp directory if it doesn't exist
        os.makedirs(self.TEMP_DIR, exist_ok=True)

        # Validate DeepL API key is present
        if not self.DEEPL_API_KEY:
            raise ValueError("DEEPL_API_KEY not found in .env file")

        print(f"✓ Configuration loaded successfully")
        print(f"✓ DeepL API Key configured")
        print(f"✓ Temp directory: {self.TEMP_DIR}")

settings = Settings()
