import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from cachetools import TTLCache

from util import util
from models.metadata import *

LAST_UPDATE_DATE_FORMAT = "%b %d,%Y - %H:%M"

CACHE_SIZE = 100  # max cached items
CACHE_TTL = 120  # max TTL in seconds
soup_cache = TTLCache(maxsize=CACHE_SIZE, ttl=CACHE_TTL)


class Item:
    def __init__(self, item_url: str):
        self.url: str = item_url
        self.last_updated: datetime = datetime.min
        self.thumbnail_url: str = ""
        self.name = ""
        self.alternative = ""
        self.description = ""
        self.status: str = ""

        self.views: int = 0
        self.rating: float = 0
        self.votes: int = 0

        self.chapter_urls: [str] = []
        self.authors: [Author] = []
        self.genres: [Genre] = []

        self.update_metadata()
        self.update_chapters()

    def get_soup(self) -> BeautifulSoup:
        if self.url in soup_cache:
            return soup_cache[self.url]

        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, 'html.parser')
        soup_cache[self.url] = soup

        return soup

    def update_metadata(self):
        soup = self.get_soup()

        self.name = soup.find('div', class_="story-info-right").find('h1').text

        links = (soup
                 .find('div', class_='panel-story-info')
                 .find('div', class_='story-info-right')
                 .find_all('a', class_='a-h'))

        for el in links:
            url = el['href']
            if re.search("/author/", url):
                author = Author(name=el.text, url=url, id=url.split('/')[-1])
                if author.id == '':
                    author.id = author.name

                self.authors.append(author)

            if re.search("/genre-[0-9]+$", url):
                genre = Genre(name=el.text, url=url, id=int(re.findall("[0-9]+$", url)[-1]))
                self.genres.append(genre)

        self.description = self.scrape_description()
        self.views = self.scrape_views()

        self.rating = float(soup.find("em", {"property": "v:average"}).text)
        self.votes = int(soup.find("em", {"property": "v:votes"}).text)

        self.last_updated = self.scrape_last_updated()

        self.thumbnail_url = self.scrape_thumbnail_url()

        table = self.scrape_table()

        self.status = table.get('status').lower()
        self.alternative = table.get('alternative')

    def update_chapters(self):
        self.chapter_urls = self.scrape_chapter_urls()

    def scrape_last_updated(self) -> datetime:
        soup = self.get_soup()

        date_string = soup.find('div', class_='panel-story-info').find('div', class_='story-info-right-extent').find(
            'span', class_='stre-value').text
        date_string = re.sub("[AP]M", "", date_string).strip()

        parsed_date = datetime.strptime(date_string, LAST_UPDATE_DATE_FORMAT)

        return parsed_date



    def scrape_views(self) -> int:
        views = util.parse_to_integer((self.get_soup()
                                       .find('div', class_='panel-story-info')
                                       .find('div', class_='story-info-right-extent')
                                       .find_all('span', class_='stre-value'))[1].text)
        return views

    def scrape_thumbnail_url(self):
        return (
            self.get_soup().find('div', class_="panel-story-info")
            .find('span', class_="info-image")
            .find('img')['src']
        )

    def scrape_description(self):
        div = (self.get_soup().find('div', class_="panel-story-info")
               .find('div', class_="panel-story-info-description"))

        return ''.join(div.find_all(string=True, recursive=False)).strip()

    def scrape_chapter_urls(self) -> [str]:
        soup = self.get_soup()

        chapters_div = soup.find('div', class_="panel-story-chapter-list")

        if chapters_div is not None:
            chapter_links = chapters_div.find_all('a', class_="chapter-name")
            chapter_urls = [link['href'] for link in chapter_links]
            return list(chapter_urls.__reversed__())
        else:
            return []

    def scrape_table(self) -> {str: str}:
        soup = self.get_soup()

        table = soup.find('table', class_='variations-tableInfo')

        data = {}

        for row in table.find_all('tr'):
            label = row.find('td', class_='table-label').get_text(strip=True).replace(':', '').lower().strip()
            value_tag = row.find('td', class_='table-value')

            if value_tag.find('h2'):
                value = value_tag.find('h2').get_text(strip=True)
            elif value_tag.find_all('a'):  # Check if the value contains multiple links.
                value = ' - '.join(link.get_text(strip=True) for link in value_tag.find_all('a'))
            else:
                value = value_tag.get_text(strip=True)

            # Add to the dictionary.
            data[label] = value

        return data

    def __str__(self):
        return ', '.join(f"{key}={value}" for key, value in self.__dict__.items())


if __name__ == "__main__":
    url = "https://chapmanganato.to/manga-ay1003481"

    item = Item(url)

    print(item)
    print([str(g) for g in item.genres])
    print([str(g) for g in item.authors])
    print(item.status)
