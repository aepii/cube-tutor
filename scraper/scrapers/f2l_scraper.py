import json
from .base_scraper import scrape_subset


# Scrape F2L algorithms and export to JSON
def run():
    url = "https://speedcubedb.com/a/3x3/F2L"
    cases = scrape_subset(url)

    with open("../shared/data/raw/f2l.json", "w", encoding="utf-8") as f:
        json.dump(
            {"subset": "F2L", "cases": list(cases.values())},
            f,
            ensure_ascii=False,
            indent=2,
        )
