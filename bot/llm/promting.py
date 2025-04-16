from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio.engine import AsyncEngine

class CategorizedExpenses(BaseModel):
    total_expense: float = Field(..., description="Общая сумма затрат")
    category_expenses: Dict[str, float] = Field(..., description="Затраты по категориям, суммированные")

# Create parser
parser = PydanticOutputParser(pydantic_object=CategorizedExpenses)

# Template for expense categorization
EXPENSE_PROMPT = PromptTemplate(
    template="""
    Извлеки общую сумму затрат и рассортируй их по категориям.
    Используй следующие категории:
    - Еда: всё, что связано с покупкой еды (продукты, рестораны, кафе)
    - Транспорт: всё, что связано с передвижением (такси, метро, автобус, бензин, парковка)
    - Развлечения: кино, концерты, клубы, подписки на сервисы
    - Другое: если трата не подходит ни под одну категорию
    Текст:
    {text}
    {format_instructions}
    """,
    input_variables=["text"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

# Function to extract expenses
async def extract_expense_info(text: str, llm):
    formatted_prompt = EXPENSE_PROMPT.format(text=text)
    response = llm.invoke(formatted_prompt)
    return parser.parse(response.content)

# Function to get all users
async def get_all_users(db_engine: AsyncEngine):
    async with db_engine.connect() as conn:
        query = text("""
            SELECT telegram_id, first_name, last_name
            FROM users
            ORDER BY telegram_id
        """)
        
        result = await conn.execute(query)
        users = result.fetchall()
        
        return [{"telegram_id": user.telegram_id, 
                 "first_name": user.first_name, 
                 "last_name": user.last_name} for user in users]

# Modified get_user_messages function to support time filtering
async def get_user_messages(telegram_id, db_engine: AsyncEngine, time_period=None):
    async with db_engine.connect() as conn:
        # Base query with digit check
        query_text = """
            SELECT content, timestamp
            FROM messages
            WHERE telegram_id = :telegram_id
            AND content ~ '[0-9]'  -- PostgreSQL regex to find content with digits
        """
        
        # Add time filter if provided
        params = {"telegram_id": telegram_id}
        if time_period and "start" in time_period:
            query_text += " AND timestamp >= :start_time"
            params["start_time"] = time_period["start"]
            
        if time_period and "end" in time_period:
            query_text += " AND timestamp <= :end_time"
            params["end_time"] = time_period["end"]
            
        # Add order by
        query_text += " ORDER BY timestamp"
        
        # Execute query
        query = text(query_text)
        result = await conn.execute(query, params)
        messages = result.fetchall()
        
        return [{"content": msg.content, "timestamp": msg.timestamp} for msg in messages]

async def analyze_user_expenses(telegram_id, db_engine: AsyncEngine, llm, time_period=None):
    # Get all messages for the user, with optional time filtering
    messages = await get_user_messages(telegram_id, db_engine, time_period)
    
    if not messages:
        return None
    
    # Combine all message content
    all_content = "\n".join([msg["content"] for msg in messages])
    
    # Extract expense information
    try:
        result = await extract_expense_info(all_content, llm)
        return result
    except Exception as e:
        print(f"Error processing expenses for user {telegram_id}: {e}")
        return None