import asyncio
from aiogram import Bot, Dispatcher
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from bot.config_reader import get_config, BotConfig, DbConfig
from bot.db.tables import metadata
from bot.handlers import get_routers
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os 
# Import your voice handling router
from bot.handlers.commands import router as audio_router  # Adjust the import path
load_dotenv()

async def main():
    # В get_config передаются два аргумента:
    # 1. Модель Pydantic, в которую будет преобразована часть конфига
    # 2. Корневой "ключ", из которого данные читаются и накладываются на модель
    db_config = get_config(DbConfig, "db")
    engine = create_async_engine(
        url=str(db_config.dsn),  # здесь требуется приведение к строке
        echo=db_config.is_echo
    )
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    # async with engine.begin() as conn:
    #     await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS timestamp TIMESTAMP WITH TIME ZONE"))
    
        # Execute this as a one-time operation
    # async with engine.begin() as conn:
    #     await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS other TEXT"))
    # Проверка соединения с СУБД
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
    
    # Создание таблиц
    async with engine.begin() as conn:
        # Если ловите ошибку "таблица уже существует",
        # раскомментируйте следующую строку:
        # await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)

    # Initialize the OpenAI client
    bot_config = get_config(BotConfig, "bot")
    # You might want to add OPENAI_API_KEY to your config
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_client = AsyncOpenAI(api_key=openai_api_key)
    
    dp = Dispatcher(db_engine=engine, openai_client=openai_client)
    
    # Include all routers from get_routers() function
    dp.include_routers(*get_routers())
    
    # Make sure to include your audio router if it's not already in get_routers()
    # dp.include_router(audio_router)
    
    bot = Bot(token=bot_config.token.get_secret_value())
    
    print("Starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())