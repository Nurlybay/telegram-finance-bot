from aiogram import Router, F
from aiogram.filters import Command,CommandStart
from aiogram.types import Message, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from openai import AsyncOpenAI
from aiogram.utils.keyboard import InlineKeyboardBuilder
from langchain_community.chat_models import ChatOpenAI
import os
from bot.llm.promting import analyze_user_expenses, get_all_users
router = Router(name="expense_commands router")


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    db_engine: AsyncEngine
):
    # Create a reply keyboard with the expense analysis button
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Сколько всего потратил")]
        ],
        resize_keyboard=True,  # Makes the keyboard smaller
        one_time_keyboard=False  # Keep the keyboard visible after use
    )
    
    # Send welcome message with the keyboard
    await message.answer(
        "Привет! Я бот для анализа твоих расходов. Нажми на кнопку ниже, чтобы увидеть анализ своих трат.",
        reply_markup=keyboard
    )

# Handle button press by checking the text content
@router.message(F.text == "Сколько всего потратил")
async def handle_expense_button(
    message: Message,
    db_engine: AsyncEngine
):
    # Initialize LLM
    openai_api_key = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(temperature=0.0, openai_api_key=openai_api_key)
    
    # Get the user's telegram_id
    telegram_id = message.from_user.id
    
    # Send processing message
    processing_msg = await message.answer("Анализирую ваши расходы... Это может занять некоторое время.")
    
    # Analyze expenses
    result = await analyze_user_expenses(telegram_id, db_engine, llm)
    
    if not result:
        await message.answer("К сожалению, не удалось найти сообщения с расходами для анализа.")
        return
    
    # Format the response
    response = f"*Анализ ваших расходов*\n\n"
    response += f"*Общая сумма расходов:* {result.total_expense}\n\n"
    response += "*Расходы по категориям:*\n"
    
    for category, amount in result.category_expenses.items():
        response += f"- *{category}:* {amount}\n"
    
    # Send the analysis result
    await message.answer(response, parse_mode="Markdown")
# Helper function to create the admin panel keyboard
def get_admin_keyboard(users):
    builder = InlineKeyboardBuilder()
    # Button to analyze all users
    builder.button(text="Analyze All Users", callback_data=f"analyze_all")
    
    # Add buttons for individual users
    for user in users:
        user_name = f"{user['first_name']} {user['last_name']}"
        builder.button(
            text=f"Analyze {user_name}",
            callback_data=f"analyze_user_{user['telegram_id']}"
        )
    
    # Add a send to all button
    builder.button(text="Send Analysis to All Users", callback_data="send_all")
    
    # Adjust grid layout (1 button per row)
    builder.adjust(1)
    return builder.as_markup()

@router.message(Command("analyze_expenses"))
async def cmd_analyze_expenses(
    message: Message,
    db_engine: AsyncEngine
):
    # Initialize LLM
    openai_api_key = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(temperature=0.0, openai_api_key=openai_api_key)
    
    # Get the user's telegram_id
    telegram_id = message.from_user.id
    
    # Send initial response
    await message.answer("Анализирую ваши расходы... Это может занять некоторое время.")
    
    # Analyze expenses
    result = await analyze_user_expenses(telegram_id, db_engine, llm)
    
    if not result:
        await message.answer("К сожалению, не удалось найти сообщения с расходами для анализа.")
        return
    
    # Format the response
    response = f"*Анализ ваших расходов*\n\n"
    response += f"*Общая сумма расходов:* {result.total_expense}\n\n"
    response += "*Расходы по категориям:*\n"
    
    for category, amount in result.category_expenses.items():
        response += f"- *{category}:* {amount}\n"
    
    # Send the analysis result
    await message.answer(response, parse_mode="Markdown")

@router.message(Command("admin_panel"))
async def cmd_admin_panel(
    message: Message,
    db_engine: AsyncEngine
):
    # Check if user is admin (you should implement proper admin check)
    admin_ids = [467460985, message.from_user.id]  # Replace with actual admin IDs
    if message.from_user.id not in admin_ids:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return
    
    # Get all users
    users = await get_all_users(db_engine)
    
    if not users:
        await message.answer("В базе данных нет пользователей.")
        return
    
    # Create keyboard with analysis options
    keyboard = get_admin_keyboard(users)
    
    # Send admin panel
    await message.answer(
        f"Панель администратора - Анализ расходов\n\n"
        f"Всего пользователей: {len(users)}\n"
        f"Выберите действие:",
        reply_markup=keyboard
    )

# Handle callback for analyzing all users
@router.callback_query(F.data == "analyze_all")
async def callback_analyze_all(
    callback: CallbackQuery,
    db_engine: AsyncEngine
):
    await callback.answer("Starting analysis for all users...")
    
    # Send initial message
    message = await callback.message.answer("Начинаю анализ расходов для всех пользователей...")
    
    # Initialize LLM
    openai_api_key = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(temperature=0.0, openai_api_key=openai_api_key)
    
    # Get all users
    users = await get_all_users(db_engine)
    
    # Analyze for each user
    results = {}
    for user in users:
        telegram_id = user["telegram_id"]
        result = await analyze_user_expenses(telegram_id, db_engine, llm)
        if result:
            results[telegram_id] = {
                "user": user,
                "result": result
            }
    
    # Update message with summary
    await message.edit_text(
        f"Анализ завершен для {len(results)}/{len(users)} пользователей.\n\n"
        f"Для отправки результатов всем пользователям, нажмите 'Send Analysis to All Users'."
    )

# Handle callback for analyzing a specific user
@router.callback_query(F.data.startswith("analyze_user_"))
async def callback_analyze_user(
    callback: CallbackQuery,
    db_engine: AsyncEngine
):
    # Extract user ID from callback data
    telegram_id = int(callback.data.split("_")[-1])
    
    await callback.answer(f"Analyzing user {telegram_id}...")
    
    # Initialize LLM
    openai_api_key = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(temperature=0.0, openai_api_key=openai_api_key)
    
    # Get user details
    users = await get_all_users(db_engine)
    user = next((u for u in users if u["telegram_id"] == telegram_id), None)
    
    if not user:
        await callback.message.answer(f"User with ID {telegram_id} not found.")
        return
    
    # Analyze expenses
    result = await analyze_user_expenses(telegram_id, db_engine, llm)
    
    if not result:
        await callback.message.answer(f"No expense data found for {user['first_name']} {user['last_name']}.")
        return
    
    # Format the response
    response = f"*Анализ расходов для {user['first_name']} {user['last_name']}*\n\n"
    response += f"*Общая сумма расходов:* {result.total_expense}\n\n"
    response += "*Расходы по категориям:*\n"
    
    for category, amount in result.category_expenses.items():
        response += f"- *{category}:* {amount}\n"
    
    # Add send button for this specific user
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"Send to {user['first_name']}",
        callback_data=f"send_user_{telegram_id}"
    )
    
    # Send the analysis result
    await callback.message.answer(
        response,
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )

# Handle callback for sending analysis to a specific user
@router.callback_query(F.data.startswith("send_user_"))
async def callback_send_user(
    callback: CallbackQuery,
    db_engine: AsyncEngine
):
    # Extract user ID from callback data
    telegram_id = int(callback.data.split("_")[-1])
    
    await callback.answer("Sending analysis...")
    
    # Initialize LLM
    openai_api_key = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(temperature=0.0, openai_api_key=openai_api_key)
    
    # Get user details
    users = await get_all_users(db_engine)
    user = next((u for u in users if u["telegram_id"] == telegram_id), None)
    
    if not user:
        await callback.message.answer(f"User with ID {telegram_id} not found.")
        return
    
    # Analyze expenses
    result = await analyze_user_expenses(telegram_id, db_engine, llm)
    
    if not result:
        await callback.message.answer(f"No expense data found for {user['first_name']} {user['last_name']}.")
        return
    
    # Format the message for the user
    user_message = f"*Анализ ваших расходов*\n\n"
    user_message += f"*Общая сумма расходов:* {result.total_expense}\n\n"
    user_message += "*Расходы по категориям:*\n"
    
    for category, amount in result.category_expenses.items():
        user_message += f"- *{category}:* {amount}\n"
    
    # Send to user
    try:
        bot = callback.bot
        await bot.send_message(
            chat_id=telegram_id,
            text=user_message,
            parse_mode="Markdown"
        )
        await callback.message.answer(f"Analysis successfully sent to {user['first_name']} {user['last_name']}.")
    except Exception as e:
        await callback.message.answer(f"Failed to send analysis: {e}")

# Handle callback for sending analysis to all users
@router.callback_query(F.data == "send_all")
async def callback_send_all(
    callback: CallbackQuery,
    db_engine: AsyncEngine
):
    await callback.answer("Preparing to send analysis to all users...")
    
    # Send initial status
    status_message = await callback.message.answer("Preparing to send analysis to all users...")
    
    # Initialize LLM
    openai_api_key = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(temperature=0.0, openai_api_key=openai_api_key)
    
    # Get all users
    users = await get_all_users(db_engine)
    
    if not users:
        await status_message.edit_text("No users found in the database.")
        return
    
    # Process each user
    success_count = 0
    failure_count = 0
    
    for i, user in enumerate(users):
        # Update status periodically
        if i % 5 == 0 or i == len(users) - 1:
            await status_message.edit_text(
                f"Processing users: {i+1}/{len(users)}\n"
                f"Success: {success_count}, Failed: {failure_count}"
            )
        
        telegram_id = user["telegram_id"]
        
        # Analyze expenses
        result = await analyze_user_expenses(telegram_id, db_engine, llm)
        
        if not result:
            failure_count += 1
            continue
        
        # Format the message
        user_message = f"*Анализ ваших расходов*\n\n"
        user_message += f"*Общая сумма расходов:* {result.total_expense}\n\n"
        user_message += "*Расходы по категориям:*\n"
        
        for category, amount in result.category_expenses.items():
            user_message += f"- *{category}:* {amount}\n"
        
        # Send to user
        try:
            bot = callback.bot
            await bot.send_message(
                chat_id=telegram_id,
                text=user_message,
                parse_mode="Markdown"
            )
            success_count += 1
        except Exception:
            failure_count += 1
    
    # Final status update
    await status_message.edit_text(
        f"Analysis sent to users.\n"
        f"Success: {success_count}, Failed: {failure_count}"
    )