import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_bot_token: str = ""
    public_site_url: str = "http://localhost:3001"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(
        "Arvexo Study: бот для ежедневных заданий и краткой статистики. "
        f"Открой платформу: {settings.public_site_url}"
    )


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    if not settings.telegram_bot_token:
        logging.warning("TELEGRAM_BOT_TOKEN is empty. Bot is idle.")
        while True:
            await asyncio.sleep(3600)

    bot = Bot(token=settings.telegram_bot_token)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
