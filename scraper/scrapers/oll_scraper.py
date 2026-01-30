import json
from .base_scraper import scrape_subset


# Scrape OLL algorithms and export to JSON
def run():
    url = "https://speedcubedb.com/a/3x3/OLL"
    cases = scrape_subset(url)

    with open("../shared/data/raw/oll.json", "w", encoding="utf-8") as f:
        json.dump(
            {"subset": "OLL", "cases": list(cases.values())},
            f,
            ensure_ascii=False,
            indent=2,
        )
