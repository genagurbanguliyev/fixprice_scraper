import os
import json
import subprocess

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from fixprice_scraper.spiders.product import ProductSpider
CATALOG_FILE = "catalog.json"
BASE_URL = "https://fix-price.com"


def full_url(url):
    if url.startswith("/"):
        return BASE_URL + url
    return url


def catalog_file_exists_and_valid():
    return os.path.exists(CATALOG_FILE) and os.path.getsize(CATALOG_FILE) > 0


def run_catalog_spider():
    print("Running catalog_spider to generate catalog.json...")
    subprocess.run(["scrapy", "crawl", "catalog_spider"], check=True)


def load_catalog():
    with open(CATALOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def display_catalog(catalog_data):
    index_map = {}
    print("\nAvailable Catalogs:\n")
    for i, item in enumerate(catalog_data, 1):
        print(f"{i}. {item['text']}")
        index_map[str(i)] = item
        if item.get("subcatalog"):
            for j, child in enumerate(item["subcatalog"], 1):
                key = f"{i}.{j}"
                print(f"  {key}. {child['text']}")
                index_map[key] = child
    return index_map


def prompt_user_for_selection():
    return input(
        "\nWrite catalog number that you want to scrape.\n"
        "If you want many catalogs, write numbers separated by ',' (example: 1,2,3).\n"
        "If you want the whole catalog, write just the integer number.\n"
        "If you want only subcatalog, insert it as a float like 2.2\n> "
    )


def parse_user_selection(selection_str, index_map):
    selected = []
    for part in selection_str.split(","):
        part = part.strip()
        if part in index_map:
            selected.append(index_map[part])
        else:
            print(f"⚠️ Invalid index: {part}")
    return selected


def main():
    if not catalog_file_exists_and_valid():
        run_catalog_spider()

    catalog_data = load_catalog()
    index_map = display_catalog(catalog_data)

    user_input = prompt_user_for_selection()
    selected_catalogs = parse_user_selection(user_input, index_map)

    print("\n✅ You selected:")
    for item in selected_catalogs:
        print(f"- {item['text']} (url: {item.get('link')})")

        # Run the ProductSpider
        process = CrawlerProcess(get_project_settings())
        process.crawl(ProductSpider, catalogs=selected_catalogs)
        process.start()


if __name__ == "__main__":
    main()
