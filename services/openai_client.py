"""
services.openai_client
======================

Асинхронный «тонкий» клиент к OpenAI Chat Completion API, который
скрывает все детали сетевого обращения и отдаёт готовые строки для
Telegram-бота.

Содержит четыре утилиты высокого уровня:

* **ask_chatgpt** — универсальный запрос/ответ к ChatGPT;
* **get_random_fact** — короткий «эмодзи + научный факт»;
* **get_week_menu** — недельное меню на N ккал с готовым списком покупок;
* **get_quiz_question** — один JSON-вопрос викторины.

Все функции ничего не знают о Telegram, поэтому легко тестируются.
"""

from __future__ import annotations
import os, json, logging
from typing import Any, Dict, List, Tuple
from dotenv import load_dotenv
import openai

load_dotenv()
_API_KEY = os.getenv("CHATGPT_TOKEN", "")
if not _API_KEY:
    raise RuntimeError("CHATGPT_TOKEN не найден в .env")

client = openai.AsyncOpenAI(api_key=_API_KEY)
_MODEL = "gpt-3.5-turbo"

logger = logging.getLogger(__name__)


async def ask_chatgpt(
    user_text: str,
    *,
    system_prompt: str | None = None,
    temperature: float = 0.8,
    model: str = _MODEL,
) -> str:
    """Отправить запрос в ChatGPT и вернуть сырой ответ.

    Parameters
    ----------
    user_text:
        Текст пользователя (основное сообщение в диалоге).
    system_prompt:
        Необязательный «системный промпт» — контекст или роль модели.
        Если `None`, контекст не устанавливается.
    temperature:
        Степень стохастичности (0 = максимально детерминированный
        ответ, 1 и выше — более креативный).
    model:
        Идентификатор модели OpenAI; по умолчанию *gpt-3.5-turbo*.

    Returns
    -------
    str
        Содержимое первого choices[].message.content без
        начальных/конечных пробелов.

    Raises
    ------
    RuntimeError
        Оборачивает оригинальное исключение SDK, чтобы
        вызывающий код мог единообразно обработать ошибку.
    """
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

async def get_random_fact() -> str:
    """Вернуть одну научную «факт-строку» с эмодзи в начале.

        Использует `ask_chatgpt()` с слегка увеличенной temperature,
        чтобы получать более разнообразные результаты.
    """
    return await ask_chatgpt(
        "Приведи один интересный научный факт одной строкой, "
        "начав с подходящего emoji.",
        temperature=0.95,
    )


async def get_week_menu(kcal: int) -> str:
    """Сгенерировать полное 7-дневное меню с лимитом калорий.

        Parameters
        ----------
        kcal:
            Целевой суточный лимит (± небольшая погрешность).

        Returns
        -------
        str
            Готовый Markdown-текст: название, 7 дней × 5 приёмов пищи
            и сводный список покупок.

        Notes
        -----
        * Формат ответа строго задаётся промптом, поэтому парсинг
          не понадобится — можно сразу отправлять в Telegram.
        * Температура снижена до 0.65, чтобы меню было реалистичным.
    """
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


async def get_quiz_question(topic_ru: str) -> Tuple[str, List[str], int]:
    """Сгенерировать один вопрос викторины по заданной теме.

        Parameters
        ----------
        topic_ru:
            Тема на русском («История», «Наука», …).

        Returns
        -------
        tuple[str, list[str], int]
            (`question_text`, `options[3]`, `right_index`)

            * `question_text` — строка-вопрос;
            * `options` — список из трёх вариантов ответа;
            * `right_index` — номер правильного варианта (0-2).

            При ошибке JSON-парсинга возвращается заглушка
            «Ошибка генерации вопроса» + три тривиальных варианта, 0.
    """
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
