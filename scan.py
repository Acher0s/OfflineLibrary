import time
from threading import Thread

from bs4 import BeautifulSoup
import requests
import re
import threading
from tqdm import tqdm

from item import Item

MAIN_SEARCH_URL = "https://manganato.com/genre-all/"
LAST_PAGE_CLASS = "page-last"
COLLECTION_ITEM_LINK_CLASS = "genres-item-name"

def get_total_pages() -> int:
    response = requests.get(MAIN_SEARCH_URL)

    soup = BeautifulSoup(response.text, 'html.parser')

    text = soup.find(class_=LAST_PAGE_CLASS).text
    total_pages = int(re.sub("[^0-9]", "", text))

    return  3 # total_pages


def get_item_urls() -> [str]:
    item_urls = []

    for i in tqdm(range(1, get_total_pages() + 1), desc="Fetching item urls", unit="page"):
        response = requests.get(MAIN_SEARCH_URL + str(i))
        soup = BeautifulSoup(response.text, 'html.parser')

        links = soup.find_all(class_=COLLECTION_ITEM_LINK_CLASS)
        for link in links:
            url = link["href"]
            item_urls.append(url)

    return item_urls

def add_item_from_url(urls : [str], l : [Item]):
    for url in urls:
        l.append(Item(url))


if __name__ == "__main__":
    start_time = time.time()

    urls = get_item_urls()


    end_time = time.time()
    elapsed_time = end_time - start_time

    print("Took {:.2f} seconds".format(elapsed_time))

    start_time = time.time()

    items = []
    x = 25
    sublist_size = len(urls) // x
    tasks = [urls[i * sublist_size: (i + 1) * sublist_size] for i in range(x)]

    print(tasks)

    threads = []
    for task in tasks:
        t = Thread(target=add_item_from_url, args=[task, items])
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(items)

    print("Took {:.2f} seconds".format(elapsed_time))
    print("Number of URLs:", len(urls))