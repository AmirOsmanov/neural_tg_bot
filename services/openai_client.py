# services/openai_client.py

import logging
from openai import AsyncOpenAI
from config import CHATGPT_TOKEN

logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=CHATGPT_TOKEN)


async def get_random_fact() -> str:
    """
    Получить случайный факт от ChatGPT.
    """
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты помощник, который рассказывает "
                        "интересные и познавательные факты. "
                        "Отвечай на русском языке."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        "Расскажи интересный случайный факт из "
                        "любой области знаний. Факт должен быть "
                        "познавательным, удивительным и не слишком "
                        "длинным (максимум 3–4 предложения)."
                    )
                }
            ],
            max_tokens=200,
            temperature=0.8
        )
        fact = response.choices[0].message.content.strip()
        logger.info("Факт успешно получен от OpenAI")
        return fact

    except Exception as e:
        logger.error(f"Ошибка при получении факта от OpenAI: {e}")
        return "🤔 К сожалению, не удалось получить факт в данный момент."


async def ask_chatgpt(messages) -> str:
    """
    Отправка произвольного списка сообщений (system + user) в ChatGPT и получение ответа.
    messages: List[{"role":..., "content":...}]
    """
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=400,
            temperature=0.7
        )
        reply = response.choices[0].message.content.strip()
        logger.info("Ответ успешно получен от OpenAI")
        return reply

    except Exception as e:
        logger.error(f"Ошибка при общении с ChatGPT: {e}")
        return "😔 К сожалению, не удалось получить ответ от ChatGPT."

async def get_quiz_question(theme: str) -> tuple[str, str]:
    """
    Возвращает кортеж (question, correct_answer) по заданной теме.
    """
    system = ("Ты помощник-викторина. Сформулируй ОДИН вопрос по теме «"
              f"{theme}» и дай правильный ответ в JSON:"
              r' {"question": "...", "answer": "..."} '
              "не добавляй ничего лишнего.")
    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=200,
        messages=[{"role": "system", "content": system}]
    )
    import json
    data = json.loads(response.choices[0].message.content)
    return data["question"], data["answer"]

async def check_quiz_answer(user_answer: str, correct_answer: str) -> bool:
    """
    Очень простая проверка: искать correct_answer в пользовательском вводе
    (некейс-сенситив). При желании можно сделать запрос к GPT для гибкой
    проверки, но это увеличит задержку и расход токенов.
    """
    return correct_answer.lower() in user_answer.lower()
