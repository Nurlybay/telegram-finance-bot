from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram import F
from aiogram.types import Message
from sqlalchemy import insert, delete, select, column
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from openai import AsyncOpenAI
from langchain_community.chat_models import ChatOpenAI
import io
from bot.db.tables import users as users_table
from bot.db.tables import messages_table
from dotenv import load_dotenv
import os 

load_dotenv()
router = Router(name="commands router")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
async def get_transcript(audio_file: io.BytesIO) -> str:
    transcript = await openai_client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="en"
    )
    print(transcript.text)
    return transcript.text

async def voice_chat(message: Message, audio_or_text: io.BytesIO | str, is_hints: bool = False,
                    model_type: str = 'openai'):
    if model_type == 'openai':
        model = ChatOpenAI(temperature=1, openai_api_key=OPENAI_API_KEY)
    else:
        raise ValueError(f"Unknown model type {model_type}, please choose from ['gigachat', 'openai']")
    
    if isinstance(audio_or_text, str):
        text = audio_or_text
    else:
        text = await get_transcript(audio_or_text) or 'empty message'
    
    return text, "response here"

@router.message(F.voice | F.audio)
async def handle_audio(
    message: Message,
    db_engine: AsyncEngine
):
    # Download the voice file
    voice_file = await message.bot.get_file(message.voice.file_id if message.voice else message.audio.file_id)
    voice_data = await message.bot.download_file(voice_file.file_path)
    
    # Convert to BytesIO for processing
    voice_bytes = io.BytesIO(voice_data.read())
    voice_bytes.name = "audio.ogg"
    
    text, _ = await voice_chat(message, voice_bytes)
    timestamp = message.date
    
    async with db_engine.connect() as conn:
        # First, ensure the user exists
        user_stmt = insert(users_table).values(
            telegram_id=message.from_user.id,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        user_stmt = user_stmt.on_conflict_do_nothing(index_elements=['telegram_id'])
        await conn.execute(user_stmt)
        
        # Now insert the message - directly using telegram_id
        message_stmt = insert(messages_table).values(
            telegram_id=message.from_user.id,
            content=text,
            timestamp=timestamp
        )
        await conn.execute(message_stmt)
        await conn.commit()
    
    await message.answer(f"Transcription saved: {text}")

@router.message(Command("select"))
async def cmd_select(
    message: Message,
    db_engine: AsyncEngine
):
    stmts = [
        select(column("telegram_id"), column("first_name")).select_from(users_table),
        select("*").select_from(users_table),
        select("*").select_from(users_table).where(users_table.c.first_name == "Groosha"),
        select(users_table.c.telegram_id, users_table.c.first_name).select_from(users_table),
        select(users_table.c.telegram_id).where(users_table.c.telegram_id < 1_000_000)
    ]

    async with db_engine.connect() as conn:
        for stmt in stmts:
            result = await conn.execute(stmt)
            for row in result:
                print(row)
        print("==========")
    await message.answer("Проверьте терминал, чтобы увидеть данные.")


@router.message(Command("deleteme"))
async def cmd_deleteme(
    message: Message,
    db_engine: AsyncEngine
):
    stmt = (
        delete(users_table)
        .where(users_table.c.telegram_id == message.from_user.id)
    )
    async with db_engine.connect() as conn:
        await conn.execute(stmt)
        await conn.commit()
    await message.answer("Ваши данные удалены.")