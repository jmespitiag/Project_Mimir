from pydantic_settings import BaseSettings, SettingsConfigDict
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
    database_url: str = 'sqlite:///./mimir.db'
    owner_id: str = 'owner'
    local_api_key: str = ''
    telegram_bot_token: str = ''
