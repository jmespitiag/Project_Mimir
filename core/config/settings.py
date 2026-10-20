from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    env: str = 'local'
    log_level: str = 'INFO'
    llm_provider: str = 'mock'
    gemini_model: str = 'gemini-2.0-flash'
    google_api_key: str = ''
    google_oauth_client_id: str = ''
    google_oauth_client_secret: str = ''
    google_cloud_project: str = ''
    max_tool_steps: int = 3
    context_max_chars: int = 4000
    database_url: str = 'sqlite:///./mimir_v2.db'
    owner_id: str = 'owner'
    local_api_key: str = ''
    telegram_bot_token: str = ''

    @model_validator(mode='after')
    def auto_llm_provider(self):
        if self.google_api_key and self.llm_provider == 'mock':
            self.llm_provider = 'gemini'
        return self