from datetime import datetime

from models.chapter import Chapter
from models.item import Item
from models.metadata import Author, Genre

import psycopg2

DB_ADDRESS = 'data.db'


class DB:
    @staticmethod
    def create():
        with DB.get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute('''
                        CREATE TABLE IF NOT EXISTS authors (
                            author_id TEXT PRIMARY KEY,
                            name TEXT,
                            url TEXT
                        );
                    ''')

            cursor.execute('''
                        CREATE TABLE IF NOT EXISTS genres (
                            genre_id INTEGER PRIMARY KEY,
                            name TEXT,
                            url TEXT
                        );
                    ''')

            cursor.execute('''
                        CREATE TABLE IF NOT EXISTS chapters (
                            chapter_url TEXT PRIMARY KEY,
                            name TEXT
                        )
                    ''')

            cursor.execute('''
                       CREATE TABLE IF NOT EXISTS chapter_images (
                           chapter_url TEXT,
                           image_url TEXT,
                           image_url_nr INTEGER,
                           PRIMARY KEY (chapter_url, image_url_nr),
                           FOREIGN KEY (chapter_url) REFERENCES chapters(chapter_url)
                       )
                   ''')

            cursor.execute('''
                        CREATE TABLE IF NOT EXISTS items (
                            item_url TEXT PRIMARY KEY,
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
                            FOREIGN KEY (item_url) REFERENCES items(item_url),
                            FOREIGN KEY (author_id) REFERENCES authors(author_id)
                        )
                    ''')

            cursor.execute('''
                        CREATE TABLE IF NOT EXISTS item_genres (
                            item_url TEXT,
                            genre_id INTEGER,
                            PRIMARY KEY (item_url, genre_id),
                            FOREIGN KEY (item_url) REFERENCES items(item_url),
                            FOREIGN KEY (genre_id) REFERENCES genres(genre_id)
                        )
                    ''')

            cursor.execute('''
                        CREATE TABLE IF NOT EXISTS item_chapters (
                            item_url TEXT,
                            chapter_url TEXT,
                            chapter_nr INTEGER,
                            PRIMARY KEY (chapter_nr, item_url),
                            FOREIGN KEY (item_url) REFERENCES items(item_url),
                            FOREIGN KEY (chapter_url) REFERENCES chapters(chapter_url)
                        )
                    ''')

    @staticmethod
    def save_author(author: Author, connection):
        cursor = connection.cursor()

        cursor.execute('''
                    INSERT INTO authors (author_id, name, url)
                    VALUES (%s, %s, %s)
                    ON CONFLICT(author_id) DO UPDATE SET
                        name = excluded.name,
                        url = excluded.url
                ''', (author.id, author.name, author.url))

    @staticmethod
    def save_genre(genre: Genre, connection):
        cursor = connection.cursor()

        cursor.execute('''
                        INSERT INTO genres (genre_id, name, url)
                        VALUES (%s, %s, %s)
                        ON CONFLICT(genre_id) DO UPDATE SET
                            name = excluded.name,
                            url = excluded.url
                    ''', (genre.id, genre.name, genre.url))

    @staticmethod
    def save_chapter(chapter: Chapter, connection):
        cursor = connection.cursor()

        cursor.execute('''
            INSERT INTO chapters (chapter_url, name)
            VALUES (%s, %s)
            ON CONFLICT (chapter_url) DO NOTHING
        ''', (chapter.url, chapter.name))

        cursor.execute('DELETE FROM chapter_images WHERE chapter_url = %s', (chapter.url,))

        for i, image_url in enumerate(chapter.image_urls):
            cursor.execute('''
                        INSERT INTO chapter_images (chapter_url, image_url, image_url_nr)
                        VALUES (%s, %s, %s)
                    ''', (chapter.url, image_url, i))

    @staticmethod
    def is_item_outdated(item: Item, connection):
        cursor = connection.cursor()

        cursor.execute('SELECT last_updated FROM items WHERE item_url = %s', (item.url,))
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
                    INSERT INTO items (item_url, last_updated, name, views, rating, votes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT(item_url) DO UPDATE SET
                        last_updated = excluded.last_updated,
                        name = excluded.name,
                        views = excluded.views,
                        rating = excluded.rating,
                        votes = excluded.votes
                ''', (item.url, item.last_updated.isoformat(), item.name, item.views, item.rating, item.votes))

        cursor.execute('DELETE FROM item_authors WHERE item_url = %s', (item.url,))
        for author in item.authors:
            DB.save_author(author, connection)
            cursor.execute('INSERT INTO item_authors (item_url, author_id) VALUES (%s, %s)', (item.url, author.id))

        cursor.execute('DELETE FROM item_genres WHERE item_url = %s', (item.url,))
        for genre in item.genres:
            DB.save_genre(genre, connection)
            cursor.execute('INSERT INTO item_genres (item_url, genre_id) VALUES (%s, %s)', (item.url, genre.id))

        if outdated:
            cursor.execute('SELECT chapter_nr, chapter_url FROM item_chapters WHERE item_url = %s', (item.url,))
            existing_chapters = {(row[0], row[1]) for row in cursor.fetchall()}

            for i, chapter_url in enumerate(item.chapter_urls):
                if (i, chapter_url) not in existing_chapters:
                    cursor.execute('DELETE FROM item_chapters WHERE chapter_nr=%s AND item_url=%s', (i, item.url))

                    chapter = Chapter(chapter_url)
                    DB.save_chapter(chapter, connection)
                    cursor.execute('INSERT INTO item_chapters (item_url, chapter_url, chapter_nr) VALUES (%s, %s, %s)',
                                   (item.url, chapter_url, i))

    @staticmethod
    def get_connection():

        try:
            conn = psycopg2.connect(
                dbname="mangalib",
                user="server",
                password="Server1806",
                host="192.168.100.125",
                port="5432"
            )
            return conn

        except psycopg2.OperationalError as e:
            raise RuntimeError("Couldn't connect to database: " + str(e))


if __name__ == "__main__":
    with DB.get_connection() as conn:
        DB.create()
        it4 = Item("https://chapmanganato.to/manga-ah1003442")
        DB.save_item(it4, connection=conn)

    # DB.create()
    # it4 = Item("https://chapmanganato.to/manga-ah1003442")
    #
    # with sqlite3.connect(DB_ADDRESS) as conn:
    #     DB.save_item(it4, connection=conn)
