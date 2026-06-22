import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# API Keys
# Default API key provided by the developer
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDPGIB1v9SSHGoYw5VT26ZEO8deG7XLVYA")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Database Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(BASE_DIR, "portfolio.db"))

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# Logs configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
