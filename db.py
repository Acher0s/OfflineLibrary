from datetime import datetime

from models.chapter import Chapter
from models.item import Item
from models.metadata import Author, Genre
import sqlite3

DB_ADDRESS = 'data.db'

class DB:
    @staticmethod
    def create():
        with sqlite3.connect(DB_ADDRESS) as connection:
            cursor = connection.cursor()

            cursor.execute('''
                        CREATE TABLE IF NOT EXISTS authors (
                            id TEXT PRIMARY KEY,
                            name TEXT,
                            url TEXT
                        );
                    ''')

            cursor.execute('''
                        CREATE TABLE IF NOT EXISTS genres (
                            id INTEGER PRIMARY KEY,
                            name TEXT,
                            url TEXT
                        );
                    ''')

            cursor.execute('''
                        CREATE TABLE IF NOT EXISTS chapters (
                            url TEXT PRIMARY KEY,
                            name TEXT
                        )
                    ''')

            cursor.execute('''
                       CREATE TABLE IF NOT EXISTS chapter_images (
                           chapter_url TEXT,
                           image_url TEXT,
                           image_url_nr INTEGER,
                           PRIMARY KEY (chapter_url, image_url_nr),
                           FOREIGN KEY (chapter_url) REFERENCES chapters(url)
                       )
                   ''')

            cursor.execute('''
                        CREATE TABLE IF NOT EXISTS items (
                            url TEXT PRIMARY KEY,
                            last_updated TEXT,
                            name TEXT,
                            views INTEGER,
                            rating INTEGER,
                            votes INTEGER
                        )
                    ''')

            cursor.execute('''
                        CREATE TABLE IF NOT EXISTS item_authors (
                            item_url TEXT,
                            author_id TEXT,
                            PRIMARY KEY (item_url, author_id),
                            FOREIGN KEY (item_url) REFERENCES items(url),
                            FOREIGN KEY (author_id) REFERENCES authors(id)
                        )
                    ''')

            cursor.execute('''
                        CREATE TABLE IF NOT EXISTS item_genres (
                            item_url TEXT,
                            genre_id TEXT,
                            PRIMARY KEY (item_url, genre_id),
                            FOREIGN KEY (item_url) REFERENCES items(url),
                            FOREIGN KEY (genre_id) REFERENCES genres(id)
                        )
                    ''')

            cursor.execute('''
                        CREATE TABLE IF NOT EXISTS item_chapters (
                            item_url TEXT,
                            chapter_url TEXT,
                            chapter_nr INTEGER,
                            PRIMARY KEY (chapter_nr, item_url),
                            FOREIGN KEY (item_url) REFERENCES items(url),
                            FOREIGN KEY (chapter_url) REFERENCES chapters(url)
                        )
                    ''')

    @staticmethod
    def save_author(author: Author, connection):
        cursor = connection.cursor()

        cursor.execute('''
                    INSERT INTO authors (id, name, url)
                    VALUES (?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name = excluded.name,
                        url = excluded.url
                ''', (author.id, author.name, author.url))


    @staticmethod
    def save_genre(genre: Genre, connection):
        cursor = connection.cursor()

        cursor.execute('''
                        INSERT INTO genres (id, name, url)
                        VALUES (?, ?, ?)
                        ON CONFLICT(id) DO UPDATE SET
                            name = excluded.name,
                            url = excluded.url
                    ''', (genre.id, genre.name, genre.url))


    @staticmethod
    def save_chapter(chapter: Chapter, connection):
        cursor = connection.cursor()

        cursor.execute('''
                    INSERT OR IGNORE INTO chapters (url, name)
                    VALUES (?, ?)
                ''', (chapter.url, chapter.name))

        cursor.execute('DELETE FROM chapter_images WHERE chapter_url = ?', (chapter.url,))

        for i, image_url in enumerate(chapter.image_urls):
            cursor.execute('''
                        INSERT INTO chapter_images (chapter_url, image_url, image_url_nr)
                        VALUES (?, ?, ?)
                    ''', (chapter.url, image_url, i))

    @staticmethod
    def is_item_outdated(item: Item, connection):
        cursor = connection.cursor()

        cursor.execute('SELECT last_updated FROM items WHERE url = ?', (item.url,))
        row = cursor.fetchone()

        if row is None:
            return True

        db_last_updated = datetime.fromisoformat(row[0])

        return item.last_updated > db_last_updated

    @staticmethod
    def save_item(item: Item, connection):
        cursor = connection.cursor()

        outdated = DB.is_item_outdated(item, connection)

        cursor.execute('''
                    INSERT INTO items (url, last_updated, name, views, rating, votes)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(url) DO UPDATE SET
                        last_updated = excluded.last_updated,
                        name = excluded.name,
                        views = excluded.views,
                        rating = excluded.rating,
                        votes = excluded.votes
                ''', (item.url, item.last_updated.isoformat(), item.name, item.views, item.rating, item.votes))

        cursor.execute('DELETE FROM item_authors WHERE item_url = ?', (item.url,))
        for author in item.authors:
            DB.save_author(author, connection)
            cursor.execute('INSERT INTO item_authors (item_url, author_id) VALUES (?, ?)', (item.url, author.id))

        cursor.execute('DELETE FROM item_genres WHERE item_url = ?', (item.url,))
        for genre in item.genres:
            DB.save_genre(genre, connection)
            cursor.execute('INSERT INTO item_genres (item_url, genre_id) VALUES (?, ?)', (item.url, genre.id))

        if outdated:
            cursor.execute('SELECT chapter_nr, chapter_url FROM item_chapters WHERE item_url = ?', (item.url,))
            existing_chapters = {(row[0], row[1]) for row in cursor.fetchall()}

            for i, chapter_url in enumerate(item.chapter_urls):
                if (i, chapter_url) not in existing_chapters:
                    cursor.execute('DELETE FROM item_chapters WHERE chapter_nr=? AND item_url=?', (i, item.url))

                    chapter = Chapter(chapter_url)
                    DB.save_chapter(chapter, connection)
                    cursor.execute('INSERT INTO item_chapters (item_url, chapter_url, chapter_nr) VALUES (?, ?, ?)',
                                   (item.url, chapter_url, i))


if __name__ == "__main__":
    DB.create()
    it4 = Item("https://chapmanganato.to/manga-ah1003442")

    with sqlite3.connect(DB_ADDRESS) as conn:
        DB.save_item(it4, connection=conn)
