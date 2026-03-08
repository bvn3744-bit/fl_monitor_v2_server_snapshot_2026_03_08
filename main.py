"""Точка входа приложения FL Monitor v2."""

import logging
import time

from config import load_config
from db import init_db, is_processed, save_processed
from parser import fetch_projects
from telegram_sender import send_project, send_text
from ai_analyzer import analyze_project


logger = logging.getLogger(__name__)


def main() -> None:
    """Запуск приложения."""
    config = load_config()
    logger.info("Конфигурация успешно загружена.")

    db_path = config["DATABASE_PATH"]
    source_url = config["SOURCE_URL"]
    bot_token = config["TELEGRAM_BOT_TOKEN"]
    chat_id = config["TELEGRAM_CHAT_ID"]
    claude_api_key = config.get("CLAUDE_API_KEY", "")
    claude_model = config.get("CLAUDE_MODEL", "")

    init_db(db_path)

    while True:
        try:
            projects = fetch_projects(source_url)
        except Exception as exc:
            logger.error("Ошибка при получении проектов: %s", exc)
            time.sleep(20)
            continue

        logger.info("Получено проектов: %d", len(projects))

        for project in projects:
            project_id = project.get("project_id")
            if not project_id:
                logger.warning("Пропуск проекта без project_id.")
                continue

            if is_processed(db_path, project_id):
                logger.info("Проект %s уже обработан, пропускаем.", project_id)
                continue

            ai_text = None
            if claude_api_key:
                logger.info("AI analysis started for project %s", project_id)
                try:
                    ai_text = analyze_project(
                        project=project,
                        api_key=claude_api_key,
                        model=claude_model or None,
                    )
                    if ai_text:
                        logger.info("AI analysis finished for project %s", project_id)
                    else:
                        logger.warning("AI analysis failed for project %s", project_id)
                except Exception as exc:
                    logger.exception("AI analysis failed for project %s: %s", project_id, exc)
                    ai_text = None

            if ai_text:
                sent = send_text(bot_token, chat_id, ai_text)
            else:
                sent = send_project(bot_token, chat_id, project)

            if sent:
                save_processed(db_path, project)
                logger.info("Проект %s отправлен и сохранён.", project_id)
            else:
                logger.error("Не удалось отправить проект %s.", project_id)

        time.sleep(20)


if __name__ == "__main__":
    main()
