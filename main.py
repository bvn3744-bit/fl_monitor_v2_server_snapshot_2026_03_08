"""Точка входа приложения FL Monitor v2."""

import logging
import re
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
    send_text(bot_token, chat_id, "🟢 FL Monitor запущен")

    parse_error_streak = 0
    hourly_count = 0
    last_heartbeat = time.time()

    while True:
        try:
            projects = fetch_projects(source_url)
            parse_error_streak = 0
        except Exception as exc:
            logger.error("Ошибка при получении проектов: %s", exc)
            parse_error_streak += 1
            if parse_error_streak >= 3:
                send_text(bot_token, chat_id, "🔴 Ошибка парсера 3 раза подряд. Проверьте сервер.")
                logger.error("Отправлено уведомление об ошибке парсера.")
                parse_error_streak = 0
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

            if ai_text and "🔴" in ai_text:
                save_processed(db_path, project)
                logger.info("Проект %s — вердикт 🔴, пропускаем.", project_id)
                continue

            if ai_text:
                match = re.search(r'(\d+)\s*%', ai_text)
                confidence = int(match.group(1)) if match else 0
                if confidence < 80:
                    save_processed(db_path, project)
                    logger.info("Проект %s — уверенность %d%%, пропускаем.", project_id, confidence)
                    continue

            if ai_text:
                sent = send_text(bot_token, chat_id, ai_text)
            else:
                sent = send_project(bot_token, chat_id, project)
            if sent:
                save_processed(db_path, project)
                hourly_count += 1
                logger.info("Проект %s отправлен и сохранён.", project_id)
            else:
                logger.error("Не удалось отправить проект %s.", project_id)

        if time.time() - last_heartbeat >= 3600:
            send_text(bot_token, chat_id, f"💓 Монитор работает. Обработано за час: {hourly_count} проектов")
            logger.info("Heartbeat отправлен. Обработано за час: %d", hourly_count)
            hourly_count = 0
            last_heartbeat = time.time()

        time.sleep(20)


if __name__ == "__main__":
    main()
