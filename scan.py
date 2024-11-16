import time
from threading import Thread

from bs4 import BeautifulSoup
import requests
import re
import threading
from tqdm import tqdm
import random

from imageutil import *
from item import Item

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


if __name__ == "__main__":
    random.seed(0)

    start_time = time.time()

    pages = random.sample(range(1915), 1000)

    total_uncompressed = 0
    total_compressed = 0

    i = 0
    for page in pages:
        item_urls = random.sample(get_item_urls(page), 2)

        for item_url in item_urls:
            item = Item(item_url)

            try:
                img_urls = []

                for chapter in random.sample(item.chapters, 1):
                    img_urls += random.sample(chapter.image_urls, 3)

                for img_url in img_urls:
                    ext = img_url.split(".")[-1]

                    uncompressed_path = f"./uncompressed/{i}.{ext}"
                    compressed_path = f"./compressed/{i}.heif"

                    download_image(img_url, uncompressed_path)
                    convert_to_heif(uncompressed_path, compressed_path, quality=20)

                    total_uncompressed += os.path.getsize(uncompressed_path)
                    total_compressed += os.path.getsize(compressed_path)

                    print(i, img_url)
                    print(total_compressed / total_uncompressed)
                    i += 1
            except:
                print(f"Something went wrong, skipping {item_url}")




    end_time = time.time()
    elapsed_time = end_time - start_time

    print("Took {:.2f} seconds".format(elapsed_time))
