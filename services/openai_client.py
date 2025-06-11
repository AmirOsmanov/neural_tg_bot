from __future__ import annotations
import os, json, logging
from typing import Any, Dict, List, Tuple
from dotenv import load_dotenv
import openai

# токен
load_dotenv()
_API_KEY = os.getenv("CHATGPT_TOKEN", "")
if not _API_KEY:
    raise RuntimeError("CHATGPT_TOKEN не найден в .env")

client = openai.AsyncOpenAI(api_key=_API_KEY)
_MODEL = "gpt-3.5-turbo"

logger = logging.getLogger(__name__)


# функция обращения к chatgpt
async def ask_chatgpt(
    user_text: str,
    *,
    system_prompt: str | None = None,
    temperature: float = 0.8,
    model: str = _MODEL,
) -> str:
    messages: List[Dict[str, Any]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_text})

    try:
        resp = await client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=messages,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:                         # noqa: BLE001
        logger.exception("OpenAI request failed: %s", exc)
        raise RuntimeError("Не удалось получить ответ от ChatGPT") from exc

# Random fact
async def get_random_fact() -> str:
    return await ask_chatgpt(
        "Приведи один интересный научный факт одной строкой, "
        "начав с подходящего emoji.",
        temperature=0.95,
    )


# Подготовка меню на неделю
async def get_week_menu(kcal: int) -> str:
    prompt = (
        f"Составь ПОЛНОЕ меню на 7 дней (обозначения дней: Пн, Вт, Ср, Чт, Пт, Сб, Вс) "
        f"около {kcal} ккал/день.\n"
        "На каждый день пять приёмов пищи: Завтрак, Перекус, Обед, Полдник, Ужин.\n"
        "Формат вывода строго такой:\n"
        "*Меню* (~ XXXX ккал/день)\n\n"
        "Пн\n• Завтрак: блюдо – 250 г ≈ XXX ккал\n"
        "… (и т.д. для Перекуса, Обеда, Полдника, Ужина)\n\n"
        "Вт\n• …\n…\n\n"
        "(и так далее до Вс)\n\n"
        "*Список покупок*\n— продукт: количество (шт/кг)\n\n"
        "Без пояснений и лишних символов. Включи все 7 дней."
    )
    return await ask_chatgpt(prompt, temperature=0.65)


# Квиз
async def get_quiz_question(topic_ru: str) -> Tuple[str, List[str], int]:
    prompt = (
        "Сгенерируй ОДИН вопрос викторины по теме "
        f"«{topic_ru}».\n"
        "Верни строго JSON:\n"
        '{ "q": "вопрос", "options": ["A","B","C"], "answer": N }\n'
        "где N — индекс правильного варианта (0-2). Без комментариев."
    )
    raw = await ask_chatgpt(prompt, temperature=0.85)
    try:
        data = json.loads(raw)
        return data["q"], data["options"], int(data["answer"])
    except Exception as exc:                          # noqa: BLE001
        logger.warning("Bad quiz JSON: %s / %s", raw, exc)
        return "Ошибка генерации вопроса.", ["1", "2", "3"], 0
