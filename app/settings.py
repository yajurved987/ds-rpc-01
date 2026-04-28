import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "DS RPC 01"
    PROJECT_VERSION: str = "0.1.0"

    #DATABASE_URL: str = os.getenv("DATABASE_URL")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME","text-embedding-3-small")
    CHAT_MODEL_NAME: str = os.getenv("CHAT_MODEL_NAME","qwen/qwen3-32b")
    CHAT_MODEL_TEMPERATURE: float = float(os.getenv("CHAT_MODEL_TEMPERATURE",1.0))
    CHAT_MODEL_MAX_TOKENS: int = int(os.getenv("CHAT_MODEL_MAX_TOKENS",1000))
    CHAT_MODEL_TOP_P: float = float(os.getenv("CHAT_MODEL_TOP_P",1.0))

    VECTORSTORE_DIR: str = os.getenv("VECTORSTORE_DIR","vector_store/chromadb")
    #CHAT_MODEL_FREQUENCY_PENALTY: float = float(os.getenv("CHAT_MODEL_FREQUENCY_PENALTY"))

settings = Settings()