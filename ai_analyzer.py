"""AI-анализ проектов через Claude API."""

from __future__ import annotations

from typing import Optional

import requests


CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_CLAUDE_MODEL = "claude-opus-4-6"
MAX_PROJECT_TEXT_LENGTH = 4000


def build_prompt(project: dict) -> str:
    """Формирует prompt для Claude на основе данных проекта."""
    project_id = project.get("project_id", "")
    title = project.get("title", "")
    url = project.get("url", "")
    description_full = (
        project.get("description_full")
        or project.get("description")
        or project.get("description_short")
        or ""
    )

    if len(description_full) > MAX_PROJECT_TEXT_LENGTH:
        description_full = description_full[:MAX_PROJECT_TEXT_LENGTH]

    return (
        "Ты — опытный разработчик и аналитик, который помогает отбирать заказы с FL.ru.\n"
        "Проанализируй следующий проект и верни ответ СТРОГО в указанной разметке.\n"
        "Отвечай по-русски.\n\n"
        "Вот данные проекта:\n"
        f"ID: {project_id}\n"
        f"Название: {title}\n"
        f"Ссылка: {url}\n"
        f"Краткое описание:\n{description_full}\n\n"
        "Верни ответ в следующей структуре (без лишних пояснений):\n\n"
        "📌 Проект\n"
        "Название + ссылка\n\n"
        "🧾 Краткая выжимка\n"
        "2–3 предложения о сути задачи\n\n"
        "📊 Вердикт\n"
        "🟢 брать / 🟡 можно смотреть / 🔴 пропустить\n"
        "уверенность %\n\n"
        "📌 Почему\n"
        "CORE: ключевая технология\n\n"
        "❓ Вопросы заказчику\n"
        "3–5 вопросов\n\n"
        "⏱ Оценка\n"
        "Можно ли сделать за 1–2 дня\n\n"
        "⚠ Риски\n"
        "если есть\n\n"
        "✉ Черновик отклика\n"
        "Короткий, но вежливый и конкретный черновик ответа заказчику.\n"
    )


def analyze_project(
    project: dict,
    api_key: str,
    model: Optional[str] = None,
    timeout: int = 20,
) -> Optional[str]:
    """Отправляет проект в Claude API и возвращает текст аналитической карточки.

    При любой ошибке или некорректном ответе возвращает None.
    Логирование ошибок делается на уровне вызывающего кода.
    """
    if not api_key:
        return None

    prompt = build_prompt(project)
    model_name = (model or DEFAULT_CLAUDE_MODEL).strip()

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    payload = {
        "model": model_name,
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
    }

    try:
        response = requests.post(
            CLAUDE_API_URL,
            json=payload,
            headers=headers,
            timeout=timeout,
        )
    except requests.RequestException:
        return None

    if response.status_code != 200:
        return None

    try:
        data = response.json()
    except ValueError:
        return None

    content = data.get("content")
    if isinstance(content, list) and content:
        texts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = (block.get("text") or "").strip()
                if text:
                    texts.append(text)

        if texts:
            return "\n\n".join(texts)

    return None

