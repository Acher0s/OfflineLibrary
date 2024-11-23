from bs4 import BeautifulSoup
from tqdm import tqdm

from storage.db import DB
from util.imageutil import *
from models.item import Item
import logging

logging.basicConfig(
    filename='scan.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)

MAIN_SEARCH_URL = "https://manganato.com/genre-all/"
LAST_PAGE_CLASS = "page-last"
COLLECTION_ITEM_LINK_CLASS = "genres-item-name"


def get_total_pages() -> int:
    response = requests.get(MAIN_SEARCH_URL)

    soup = BeautifulSoup(response.text, 'html.parser')

    text = soup.find(class_=LAST_PAGE_CLASS).text
    total_pages = int(re.sub("[^0-9]", "", text))

    return total_pages


def get_all_item_urls(limit: int = 99999999) -> [str]:
    res = []

    for i in tqdm(range(1, min(get_total_pages() + 1, limit)), desc="Fetching item urls", unit="page"):
        res += get_item_urls(i)

    return res


def get_item_urls(page: int):
    item_urls = []

    response = requests.get(MAIN_SEARCH_URL + str(page))
    soup = BeautifulSoup(response.text, 'html.parser')

    links = soup.find_all(class_=COLLECTION_ITEM_LINK_CLASS)
    for link in links:
        url = link["href"]
        item_urls.append(url)

    return item_urls


def add_item_from_url(urls: [str], l: [Item]):
    for url in urls:
        l.append(Item(url))

def add_all_to_db():
    item_urls = get_all_item_urls()

    for url in item_urls:
        print(url)
        try:
            item = Item(url)
        except Exception as e:
            logging.error(f"Couldn't scrape {url}, {e}", exc_info=True)
            print(f"Couldn't scrape {url}, {e}")
            pass

        try:
            with DB.get_connection() as conn:
                DB.save_item(item, conn)
        except Exception as e:
            logging.error(f"Couldn't save {url}, {e}, item: {Item}", exc_info=True)
            print(f"Couldn't save {url}, {e}, item: {Item}")
            pass


if __name__ == "__main__":
    DB.create()

    add_all_to_db()


