from scrapers.f2l_scraper import run as run_f2l_scraper
from scrapers.oll_scraper import run as run_oll_scraper


# Scrapes subsets and exports to JSON files
def main():
    run_f2l_scraper()
    run_oll_scraper()


if __name__ == "__main__":
    main()
