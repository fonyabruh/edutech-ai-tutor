from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./app.db"
    jwt_secret: str = "dev-secret-change-me"
    jwt_expires_days: int = 30
    yandex_api_key: str = ""
    yandex_folder_id: str = ""
    yandex_model_uri: str = "gpt://{folder_id}/yandexgpt/latest"

    def model_post_init(self, __context):
        if "{folder_id}" in self.yandex_model_uri and self.yandex_folder_id:
            object.__setattr__(
                self,
                "yandex_model_uri",
                self.yandex_model_uri.format(folder_id=self.yandex_folder_id),
            )


settings = Settings()
