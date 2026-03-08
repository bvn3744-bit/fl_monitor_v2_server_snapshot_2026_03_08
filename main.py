"""Точка входа приложения FL Monitor v2."""

from config import load_config
from db import init_db, is_processed, save_processed
from parser import fetch_projects
from telegram_sender import send_project


def main() -> None:
    """Запуск приложения."""
    config = load_config()
    print("Конфигурация успешно загружена.")

    db_path = config["DATABASE_PATH"]
    source_url = config["SOURCE_URL"]
    bot_token = config["TELEGRAM_BOT_TOKEN"]
    chat_id = config["TELEGRAM_CHAT_ID"]

    init_db(db_path)

    try:
        projects = fetch_projects(source_url)
    except Exception as exc:
        print(f"Ошибка при получении проектов: {exc}")
        return

    print(f"Получено проектов: {len(projects)}")

    for project in projects:
        project_id = project.get("project_id")
        if not project_id:
            print("Пропуск проекта без project_id.")
            continue

        if is_processed(db_path, project_id):
            print(f"Проект {project_id} уже обработан, пропускаем.")
            continue

        sent = send_project(bot_token, chat_id, project)
        if sent:
            save_processed(db_path, project)
            print(f"Проект {project_id} отправлен и сохранён.")
        else:
            print(f"Не удалось отправить проект {project_id}.")


if __name__ == "__main__":
    main()
