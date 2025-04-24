import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


CITIES_FILE = "cities.json"
CATALOGS_FILE = "catalogs.json"


def load_or_scrape_cities(driver):
    if os.path.exists(CITIES_FILE):
        with open(CITIES_FILE, "r", encoding="utf-8") as f:
            try:
                cities = json.load(f)
                if cities:
                    return cities
            except json.JSONDecodeError:
                pass

    driver.find_element(By.CLASS_NAME, "choice-city").click()
    time.sleep(2)

    city_buttons = driver.find_elements(By.CSS_SELECTOR, ".modal__cities button")
    cities = []
    for i, btn in enumerate(city_buttons):
        name = btn.text.strip()
        if name:
            cities.append({"id": i, "name": name})

    with open(CITIES_FILE, "w", encoding="utf-8") as f:
        json.dump(cities, f, indent=2, ensure_ascii=False)

    return cities


def load_or_scrape_catalogs(driver):
    if os.path.exists(CATALOGS_FILE):
        with open(CATALOGS_FILE, "r", encoding="utf-8") as f:
            try:
                catalogs = json.load(f)
                if catalogs:
                    return catalogs
            except json.JSONDecodeError:
                pass

    driver.find_element(By.CSS_SELECTOR, 'a.catalog-link').click()
    time.sleep(3)

    catalog_links = driver.find_elements(By.CSS_SELECTOR, 'a.catalog-menu__item')
    catalogs = []
    for i, link in enumerate(catalog_links):
        name = link.text.strip()
        href = link.get_attribute("href")
        if name and href:
            catalogs.append({"id": i, "name": name, "url": href})

    with open(CATALOGS_FILE, "w", encoding="utf-8") as f:
        json.dump(catalogs, f, indent=2, ensure_ascii=False)

    return catalogs


def select_city_and_get_catalog():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    driver.get("https://fix-price.com/")
    time.sleep(3)

    cities = load_or_scrape_cities(driver)
    print("\nAvailable cities:")
    for city in cities:
        print(f"{city['id']}: {city['name']}")
    city_id = int(input("\nEnter the ID of the city to select: "))

    driver.find_element(By.CLASS_NAME, "choice-city").click()
    time.sleep(2)
    city_buttons = driver.find_elements(By.CSS_SELECTOR, ".modal__cities button")
    city_buttons[city_id].click()
    time.sleep(1)

    driver.find_element(By.CSS_SELECTOR, 'button[data-test="save"]').click()
    time.sleep(3)

    catalogs = load_or_scrape_catalogs(driver)
    print("\nAvailable catalogs:")
    for cat in catalogs:
        print(f"{cat['id']}: {cat['name']}")
    catalog_id = int(input("\nEnter catalog ID to scrape: "))
    selected_catalog = catalogs[catalog_id]

    cookies = driver.get_cookies()
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    driver.quit()

    return {
        "url": selected_catalog["url"],
        "cookies": cookies,
        "headers": headers,
        "city": cities[city_id]["name"],
        "catalog": selected_catalog["name"]
    }

# locality:
# %7B%22city%22%3A%22%D0%95%D0%BA%D0%B0%D1%82%D0%B5%D1%80%D0%B8%D0%BD%D0%B1%D1%83%D1%80%D0%B3%22%2C%22cityId%22%3A55%2C%22longitude%22%3A60.597474%2C%22latitude%22%3A56.838011%2C%22prefix%22%3A%22%D0%B3%22%7D
#
# sync-address:
# 1745496138149