"""Отправка уведомлений в Telegram."""

import time

import requests


def build_message(project: dict) -> str:
    """Формирует текст сообщения."""
    return (
        "Новый проект FL.ru\n\n"
        f"ID: {project['project_id']}\n"
        f"Заголовок: {project['title']}\n\n"
        "Описание:\n"
        f"{project.get('description_short', '')}\n\n"
        "Ссылка:\n"
        f"{project['url']}"
    )


def split_message(text: str, limit: int = 4000) -> list[str]:
    """Безопасно режет длинный текст на части по границам строк или по длине."""
    if not text:
        return []
    if len(text) <= limit:
        return [text]

    parts = []
    remaining = text

    while remaining:
        if len(remaining) <= limit:
            parts.append(remaining)
            break

        chunk = remaining[:limit]
        last_newline = chunk.rfind("\n")

        if last_newline != -1:
            parts.append(remaining[: last_newline + 1])
            remaining = remaining[last_newline + 1 :]
        else:
            parts.append(chunk)
            remaining = remaining[limit:]

    return parts


def _send_part(bot_token: str, chat_id: str, text: str) -> bool:
    """Отправляет одну часть сообщения с retry."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    delays = [2, 4, 6]

    for attempt in range(3):
        try:
            resp = requests.post(url, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    return True

            # Retry только при 429 или 5xx
            if resp.status_code == 429 or resp.status_code >= 500:
                if attempt < 2:
                    time.sleep(delays[attempt])
                    continue
            return False

        except (requests.ConnectionError, requests.Timeout):
            if attempt < 2:
                time.sleep(delays[attempt])
                continue
            return False

    return False


def send_project(bot_token: str, chat_id: str, project: dict) -> bool:
    """Отправляет проект в Telegram. Возвращает True если все части отправлены."""
    text = build_message(project)
    parts = split_message(text)

    for part in parts:
        if not _send_part(bot_token, chat_id, part):
            return False

    return True
