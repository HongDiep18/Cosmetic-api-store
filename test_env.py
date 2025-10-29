from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    MONGODB_URI: str
    MONGODB_DB: str

    class Config:
        env_file = ".env"

s = Settings()
print("SECRET_KEY =", s.SECRET_KEY)
print("MONGODB_URI =", s.MONGODB_URI)
print("MONGODB_DB =", s.MONGODB_DB)
