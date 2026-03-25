from pydantic_settings import BaseSettings

# מחלקה לקריאת הגדרות מסביבת העבודה (ENV). Pydantic עושה את כל העבודה.
class Settings(BaseSettings):
    postgres_url: str  # כתובת החיבור ל-PostgreSQL (נלקח מ-.env או משתנה סביבה)
    secret_key: str  # המפתח להצפנת JWT

    class Config:
        env_file = ".env"#פה אני אומר בעצם איפה לחפש את הקבצים ואת המשתנים שיצרתי בקובץ ENV

settings = Settings()