from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List

class Settings(BaseSettings):
    MONGODB_URI: str = Field(default="mongodb://localhost:27017/?retryWrites=true&w=majority")
    DB_NAME: str = Field(default="collabai")
    JWT_SECRET: str = Field(default="change-me-to-a-long-random-string-at-least-32-chars-long-for-security")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRE_DAYS: int = Field(default=7)

    GROQ_API_KEY: str = Field(default="gsk_your_groq_api_key_here")
    MISTRAL_API_KEY: str = Field(default="your_mistral_api_key_here")
    PRIMARY_PROVIDER: str = Field(default="groq")

    EMBED_MODEL: str = Field(default="BAAI/bge-small-en-v1.5")
    EMBED_DIM: int = Field(default=384)
    VECTOR_INDEX_NAME: str = Field(default="chunks_vec_index")

    STORAGE_PATH: str = Field(default="./storage")
    MAX_UPLOAD_MB: int = Field(default=20)
    CORS_ORIGINS: str = Field(default="http://localhost:5173")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()
