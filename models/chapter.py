from bs4 import BeautifulSoup
import requests


class Chapter:
    def __init__(self, chapter_url: str):
        self.url: str = chapter_url
        self.name: str = chapter_url.split('/')[-1].strip()
        self.image_urls: [str] = self.scrape_img_urls()


    def scrape_img_urls(self):
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, 'html.parser')
        img_urls = []

        container = soup.find('div', class_="container-chapter-reader")
        if container is not None:
            img_urls = [el['src'] for el in container.find_all('img')]
        else:
            exit(5)

        return img_urls

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

    def __str__(self):
        return ', '.join(f"{key}={value}" for key, value in self.__dict__.items())


if __name__ == "__main__":
    c = Chapter("https://chapmanganato.to/manga-wo999471/chapter-4")

    print(c)