import re

import requests
from bs4 import BeautifulSoup
from cachetools import TTLCache
from datetime import datetime

from chapter import Chapter
from metadata import *

LAST_UPDATE_DATE_FORMAT = "%b %d,%Y - %H:%M"

CACHE_SIZE = 100 # max cached items
CACHE_TTL = 120 # max TTL in seconds
soup_cache = TTLCache(maxsize=CACHE_SIZE, ttl=CACHE_TTL)


class Item:
    def __init__(self, item_url: str):
        self.url : str = item_url
        self.last_updated : datetime = datetime.min
        self.chapters : [Chapter] = []
        self.authors : [Author] = []
        self.genres : [Genre] = []
        self.views : int = 0
        self.rating : int = 0
        self.votes : int = 0

        self.update_metadata()
        self.update_chapters()


    def get_soup(self) -> BeautifulSoup:
        if self.url in soup_cache:
            return soup_cache[self.url]

        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, 'html.parser')
        soup_cache[self.url] = soup

        return soup

    def is_outdated(self) -> bool:
        return self.last_updated < self.scrape_last_updated()

    def update_metadata(self):
        soup = self.get_soup()

        links = (soup
         .find('div', class_='panel-story-info')
         .find('div', class_='story-info-right')
         .find_all('a',class_='a-h'))

        for el in links:
            url = el['href']
            if  re.search("/author/", url):
                author = Author(name=el.text, url=url, id=url.split('/')[-1])
                self.authors.append(author)

            if re.search("/genre-[0-9]+$", url):
                genre = Genre(name=el.text, url=url, id= int(re.findall("[0-9]+$",url)[-1]))
                self.genres.append(genre)

        self.views = (soup
         .find('div', class_='panel-story-info')
         .find('div', class_='story-info-right-extent')
         .find_all('span',class_='stre-value'))[1].text

        self.rating = soup.find("em", {"property": "v:average"}).text
        self.votes = soup.find("em", {"property": "v:votes"}).text

    def update_chapters(self):
        if self.is_outdated():
            chapter_urls = self.scrape_chapter_urls()



    def scrape_last_updated(self) -> datetime:
        soup = self.get_soup()

        date_string = soup.find('div', class_='panel-story-info').find('div', class_='story-info-right-extent').find('span',class_='stre-value').text
        date_string = re.sub("[AP]M","", date_string).strip()

        parsed_date = datetime.strptime(date_string, LAST_UPDATE_DATE_FORMAT)

        return parsed_date

    def scrape_chapter_urls(self) -> [str]:
        soup = self.get_soup()

        chapters_div = soup.find('div', class_="panel-story-chapter-list")

        if chapters_div is not None:
            chapter_links =  chapters_div.find_all('a', class_="chapter-name")
            chapter_urls = [link['href'] for link in chapter_links]
            return chapter_urls
        else:
            return []

    def __str__(self):
        return ', '.join(f"{key}={value}" for key, value in self.__dict__.items())



if __name__ == "__main__":
    url = "https://manganato.com/manga-sj995918"

    item = Item(url)

    print(item)
    print([str(g) for g in item.genres])
    print([str(g) for g in item.authors])
