from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    database_url:str
    access_token_algorithm:str
    access_token_secret:SecretStr
    access_token_expires:int=30



setting = settings() #type:ignore