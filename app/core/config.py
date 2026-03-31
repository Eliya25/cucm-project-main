from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus

# מחלקה לקריאת הגדרות מסביבת העבודה (ENV). Pydantic עושה את כל העבודה.
class Settings(BaseSettings):
    SECRET_KEY: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    POSTGRES_DB: str

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        password = quote_plus(self.POSTGRES_PASSWORD)  # הצפנת הסיסמה כדי שתתאים לכתובת URL
        #בניית כתובת חיבור ל-PostgreSQL בצורה דינמית מהפרמטרים השונים
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{password}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"   

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()