from bs4 import BeautifulSoup
import requests

import util


class Chapter:
    def __init__(self, chapter_url : str):
        self.url = chapter_url
        self.image_urls = self.scrape_img_urls()

    def scrape_img_urls(self):
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, 'html.parser')

        imgs_urls = [el['src'] for el in soup.find('div', class_="container-chapter-reader").find_all('img')]

        return imgs_urls

    def get_size(self):
        headers = {
            "Referer": "https://manganato.com/"  # Set the Referer header to the specified domain
        }

        total = 0

        for url in self.image_urls:
            response = requests.head(url, headers=headers)
            print(response)

            if response.status_code == 200 and 'Content-Length' in response.headers:
                size = int(response.headers['Content-Length'])
                total += size

            break

        return total


if __name__ == "__main__":
    c = Chapter("https://chapmanganato.to/manga-ay1003907/chapter-1")

    print(util.format_size(c.get_size()))