"""Чтение и валидация конфигурации из .env."""

import os

from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()


def load_config() -> dict:
    """Загружает конфигурацию из .env и выполняет минимальную валидацию."""
    config = {
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID", ""),
        "CHECK_INTERVAL_SECONDS": int(os.getenv("CHECK_INTERVAL_SECONDS", "60")),
        "DATABASE_PATH": os.getenv("DATABASE_PATH", "fl_monitor.db"),
        "SOURCE_URL": os.getenv("SOURCE_URL", "https://www.fl.ru/projects/"),
        "CLAUDE_API_KEY": os.getenv("CLAUDE_API_KEY", ""),
        "CLAUDE_MODEL": os.getenv("CLAUDE_MODEL", ""),
    }

    # Минимальная валидация
    if config["CHECK_INTERVAL_SECONDS"] <= 0:
        raise ValueError("CHECK_INTERVAL_SECONDS должен быть больше 0")

    if not config["SOURCE_URL"].startswith(("http://", "https://")):
        raise ValueError("SOURCE_URL должен начинаться с http:// или https://")

    return config
