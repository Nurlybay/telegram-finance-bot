from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import pytz
import os
from langchain_community.chat_models import ChatOpenAI
from bot.llm.promting import analyze_user_expenses, get_all_users

# Define the notification function
async def send_weekly_expense_notification(bot, db_engine):
    # Initialize LLM
    openai_api_key = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(temperature=0.0, openai_api_key=openai_api_key)
    
    # Get all users
    users = await get_all_users(db_engine)
    
    # Get the date range for this week
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Process each user
    for user in users:
        telegram_id = user["telegram_id"]
        
        try:
            # Get this week's expenses
            result = await analyze_user_expenses(telegram_id, db_engine, llm, 
                                              time_period={"start": start_of_week})
            
            if not result:
                continue
            
            # Format the message
            message = f"*Еженедельный отчет о расходах*\n\n"
            message += f"Привет, {user['first_name']}! Вот ваши расходы за эту неделю:\n\n"
            message += f"*Общая сумма расходов за неделю:* {result.total_expense}\n\n"
            message += "*Расходы по категориям:*\n"
            
            for category, amount in result.category_expenses.items():
                message += f"- *{category}:* {amount}\n"
            
            # Send to user
            await bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            print(f"Failed to send weekly notification to user {telegram_id}: {e}")

# Function to start the scheduler
def setup_scheduler(bot, db_engine):
    scheduler = AsyncIOScheduler()
    
    # Schedule the notification for every Friday at 19:00
    scheduler.add_job(
        send_weekly_expense_notification, 
        'cron', 
        day_of_week='fri',  # Changed from 'fri' to 'tue'
        hour=19, 
        minute=0,
        args=[bot, db_engine]
    )
    
    # Optionally add a test job that runs 1 minute after startup for debugging
    # scheduler.add_job(
    #    send_weekly_expense_notification,
    #    'date',
    #    run_date=datetime.now() + timedelta(minutes=1),
    #    args=[bot, db_engine]
    # )
    
    scheduler.start()
    return scheduler