import os
from getpass import getpass
import warnings
warnings.filterwarnings('ignore')

from utils_llm import ChatOpenAI

#course_api_key= "Введите API-ключ полученный в боте"
course_api_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2N2M3NDNlM2U5OTI3Yjg1N2Q1YTYzYmQiLCJleHAiOjE3NTY1OTg0MDB9.TVFhrce-9A1jzdl5AlXmWzWCYxO-qpHMLHugevDXvZA'

# инициализируем языковую модель
llm = ChatOpenAI(temperature=0.0, course_api_key=course_api_key)

#from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import Dict

# Определяем Pydantic-модель
class ExpenseData(BaseModel):
    total_expense: float = Field(..., description="Общая сумма затрат")
    category_expenses: Dict[str, float] = Field(..., description="Затраты по категориям")

# Создаём парсер
parser = PydanticOutputParser(pydantic_object=ExpenseData)

# Промпт с инструкциями
prompt = PromptTemplate(
    template="""Извлеки общую сумму затрат и разбивку по категориям из следующего текста:

    {text}

    {format_instructions}
    """,
    input_variables=["text"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

# Функция для обработки текста
def extract_expense_info(text: str):
    formatted_prompt = prompt.format(text=text)
    response = llm.invoke(formatted_prompt)
    return parser.parse(response.content)

# Пример текста с затратами
text = """
I bought a bottle of water for 500 tenge, paint for repair for 600 tenge, I bought a galtel for 18 thousand tenge.
"""

# Получаем результат
result = extract_expense_info(text)
print(result)
