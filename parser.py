"""Парсинг проектов с FL.ru."""

import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


def fetch_projects(source_url: str) -> list[dict]:
    """
    Получает список проектов со страницы source_url.
    Возвращает список словарей с полями: project_id, url, title, description_short.
    Выбрасывает исключение при ошибке загрузки страницы.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    response = requests.get(source_url, headers=headers, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    base_url = f"{urlparse(source_url).scheme}://{urlparse(source_url).netloc}"
    projects = []

    cards = soup.find_all(class_="b-post__grid")

    project_id_re = re.compile(r"/projects/(\d+)(?:/|$)")

    for card in cards:
        link = card.find("a", href=project_id_re)
        if not link:
            continue

        href = link.get("href", "")
        match = project_id_re.search(href)
        project_id = match.group(1) if match else ""

        url = urljoin(base_url, href)

        title_el = card.find(class_="b-post__title")
        title = title_el.get_text(strip=True) if title_el else ""

        desc_el = card.find(class_="b-post__body") or card.find(class_="b-post__txt")
        description_short = desc_el.get_text(strip=True) if desc_el else ""

        projects.append(
            {
                "project_id": project_id,
                "url": url,
                "title": title,
                "description_short": description_short,
            }
        )

    return projects
