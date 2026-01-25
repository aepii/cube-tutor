import json
from .base_scraper import scrape_subset


# Scrape PLL algorithms and export to JSON
def run():
    url = "https://speedcubedb.com/a/3x3/PLL"
    cases = scrape_subset(url)

    with open("data/raw/pll.json", "w", encoding="utf-8") as f:
        json.dump(
            {"subset": "PLL", "cases": list(cases.values())},
            f,
            ensure_ascii=False,
            indent=2,
        )
