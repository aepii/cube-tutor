import requests
from bs4 import BeautifulSoup

TIMEOUT_SECONDS = 5


# Scrapes subset from speedcubedb for algorithms
def scrape_subset(url: str) -> dict:
    # URL for OLL algorithms

    # Gets the HTML content
    try:
        # Send a GET request to speedcubedb
        response = requests.get(url, timeout=TIMEOUT_SECONDS)

        # Raise an exception for bad status codes
        response.raise_for_status()

        # Store the HTML content
        html_doc = response.text
    except requests.exceptions.RequestException as e:
        print(f"An error has occured: {e}")

    soup = BeautifulSoup(html_doc, "html.parser")

    # Holds algorithm data
    cases = {}

    # Select all elements with class singlealgorithm
    algorithms = soup.select(".singlealgorithm")

    # Retrieve data per element and store in cases
    for algorithm in algorithms:
        subgroup = algorithm.get("data-subgroup")
        alg_name = algorithm.get("data-alg")
        setup_case = (
            algorithm.select_one(".setup-case").get_text().replace("setup:", "").strip()
        )

        data_ori_divs = algorithm.select("div[data-ori]")

        key = (alg_name, subgroup)
        # Add broad case to cases
        if key not in cases:
            cases[key] = {
                "name": alg_name,
                "subgroup": subgroup,
                "setup": setup_case,
                "solutions": [],
            }

        # Add specific solutions to broad case
        for orientation in data_ori_divs:
            ori_value = orientation.get("data-ori")
            formatted_algs = orientation.select(".formatted-alg")
            for alg in formatted_algs:
                alg_text = alg.get_text(strip=True)

                cases[key]["solutions"].append(
                    {"orientation": ori_value, "alg": alg_text}
                )

    return cases
