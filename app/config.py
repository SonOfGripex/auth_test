from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DEBUG: bool = True

    DATABASE_URL: str = 'postgres://postgres:postgres@localhost:5434/postgres'

    JWT_SECRET: str = "SOME_SECRET"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_SECONDS: int = 180

    @property
    def tortoise_orm(self) -> dict:
        return {
            "connections": {"default": self.DATABASE_URL},
            "apps": {
                "models": {
                    "models": [
                        "app.user.models.user",
                        "aerich.models",
                    ],
                    "default_connection": "default",
                }
            },
        }

settings = Settings()
TORTOISE_ORM = settings.tortoise_orm
