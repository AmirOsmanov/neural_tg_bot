"""Клиент для запроса к OpenAI."""

import logging
from openai import AsyncOpenAI
from config import CHATGPT_TOKEN

logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=CHATGPT_TOKEN)


async def get_random_fact():
    """Получить случайный факт от ChatGPT."""
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Ты помощник, который рассказывает интересные и познавательные факты. Отвечай на русском языке.",
                },
                {
                    "role": "user",
                    "content": "Расскажи интересный случайный факт из любой области знаний. Факт должен быть познавательным, удивительным и не слишком длинным (максимум 3-4 предложения).",
                },
            ],
            max_tokens=200,
            temperature=0.8,
        )

        fact = response.choices[0].message.content.strip()
        logger.info("Факт успешно получен от OpenAI")
        return fact

    except Exception as e:
        logger.error(f"Ошибка при получении факта от OpenAI: {e}")
        return "🤔 К сожалению, не удалось получить факт в данный момент. Попробуйте позже!"


async def ask_chatgpt(message: str) -> str:
    """Отправка произвольного сообщения в ChatGPT и получение ответа."""
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты умный и вежливый помощник. Отвечай на русском языке."},
                {"role": "user", "content": message},
            ],
            max_tokens=400,
            temperature=0.7,
        )
        reply = response.choices[0].message.content.strip()
        logger.info("Ответ успешно получен от OpenAI")
        return reply
    except Exception as e:
        logger.error(f"Ошибка при общении с ChatGPT: {e}")
        return "😔 К сожалению, не удалось получить ответ от ChatGPT. Попробуйте позже."
