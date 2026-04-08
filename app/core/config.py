from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "INFO"
    server_domain: str = "localhost"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Database (Neon PostgreSQL)
    neon_database_url: str = ""

    # OpenAI
    openai_api_key: str = ""

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""

    # Firebase
    firebase_project_id: str = ""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
