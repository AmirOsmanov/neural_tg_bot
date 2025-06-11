# Neural TG Bot 🤖🧠🎓
Телеграм-бот, демонстрирующий интеграцию **OpenAI ChatGPT** с библиотекой `python-telegram-bot v20`.

| Команда | Возможность |
|---------|-------------|
| `/random` | Случайный факт + иллюстрация |
| `/gpt`    | Свободный диалог с ChatGPT |
| `/talk`   | Ролевое общение с персонами:<br>• Альберт Эйнштейн  • Дж. Опенгеймер  • И. Курчатов |
| `/quiz`   | Тематический квиз (История / Наука / Кино) с подсчётом баллов |

<p align="center">
  <img src="images/chatgpt.jpg" width="55%" alt="ChatGPT preview">
</p>

---

## 1. Быстрый старт

```bash
# 1. Клонируем проект
git clone https://github.com/AmirOsmanov/neural_tg_bot.git
cd neural_tg_bot

# 2. Создаём и активируем виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate          # Linux / macOS
# .venv\Scripts\activate           # Windows PowerShell

# 3. Ставим зависимости
pip install -r requirements.txt

# 4. Добавляем переменные окружения
cp .env.example .env               # скопируйте и заполните
# OPENAI_API_KEY=sk-...
# TG_BOT_TOKEN=7781...:AA...

# 5. Запуск бота (long-polling)
python main.py
```

⚠️ Без переменных OPENAI_API_KEY и TG_BOT_TOKEN бот не запустится.
Как получить токены:
OpenAI — https://platform.openai.com/account/api-keys
Telegram — у @BotFather (/newbot)

## 2. Структура проекта
```bash
│
├─ handlers/            # Логика команд
│   ├─ random.py
│   ├─ gpt.py
│   ├─ talk.py
│   └─ quiz.py
│   └─ cook.py
│
├─ services/            # Обёртки OpenAI, UI-утилиты
│   ├─ openai_client.py
│   └─ ui.py
│
├─ images/              # Картинки для отправки
│   ├─ bot.jpg
│   ├─ random.jpg
│   ├─ chatgpt.jpg
│   ├─ talk.jpg
│   └─ quiz.jpg
│   └─ cook.jpg
│
├─ .env.example         # Шаблон переменных окружения
├─ requirements.txt     # Все зависимости проекта
└─ main.py              # Точка входа
```

## 3. Как это работает
```bash
1. main.py создаёт Application (python-telegram-bot) и регистрирует ConversationHandler-ы.
2. Каждый хендлер:
- отправляет тематическую картинку (images/*.jpg);
- формирует клавиатуру (services/ui.py);
- взаимодействует с OpenAI через services/openai_client.py.
3.Ключевые данные диалогов хранятся в context.user_data:
- история общения для /gpt и /talk;
- выбранная тема, правильный ответ, счёт — для /quiz.
```