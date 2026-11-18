
import os
from pathlib import Path
from dotenv import load_dotenv

# Find the project folder and load its .env file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Local AI settings
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434"
)

OLLAMA_CHAT_MODEL = os.getenv(
    "OLLAMA_CHAT_MODEL",
    "llama3.2"
)

OLLAMA_EMBED_MODEL = os.getenv(
    "OLLAMA_EMBED_MODEL",
    "nomic-embed-text"
)

# Gemini settings
GEMINI_MODEL_FAST = os.getenv(
    "GEMINI_MODEL_FAST",
    "gemini-2.5-flash"
)

GEMINI_MODEL_PRO = os.getenv(
    "GEMINI_MODEL_PRO",
    "gemini-2.5-pro"
)

# Risk review threshold
RISK_REVIEW_THRESHOLD = float(
    os.getenv("RISK_REVIEW_THRESHOLD", "0.70")
)

if __name__ == "__main__":
    print("Configuration loaded successfully!")
    print("Ollama URL:", OLLAMA_BASE_URL)
    print("Chat model:", OLLAMA_CHAT_MODEL)
    print("Embedding model:", OLLAMA_EMBED_MODEL)
    print("Gemini fast model:", GEMINI_MODEL_FAST)
    print("Gemini pro model:", GEMINI_MODEL_PRO)
    print("Risk review threshold:", RISK_REVIEW_THRESHOLD)
