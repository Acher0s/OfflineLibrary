import shutil

from bs4 import BeautifulSoup
import requests

import imageutil
import util


class Chapter:
    def __init__(self, chapter_url: str, initialize: bool = True):
        self.url: str = chapter_url
        self.image_urls: [str] = []

        if initialize:
            self.initialize()

    def initialize(self):
        self.image_urls = self.scrape_img_urls()

    def scrape_img_urls(self):
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, 'html.parser')

        imgs_urls = [el['src'] for el in soup.find('div', class_="container-chapter-reader").find_all('img')]

        return imgs_urls

    def get_size(self):
        headers = {
            "Referer": "https://manganato.com/"
        }

        total = 0

        for i, url in enumerate(self.image_urls):
            response = requests.head(url, headers=headers)

            if response.status_code == 200 and 'Content-Length' in response.headers:
                size = int(response.headers['Content-Length'])
                total += size

        return total


if __name__ == "__main__":
    c = Chapter("https://chapmanganato.to/manga-wo999471/chapter-4")

    url = c.image_urls[7]
    ext = url.split('.')[-1]
    imageutil.download_image(url, f"./test/a.{ext}")