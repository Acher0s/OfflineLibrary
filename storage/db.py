from datetime import datetime

from models.chapter import Chapter
from models.item import Item
from models.metadata import Author, Genre

import psycopg2
import tempfile

from dotenv import load_dotenv
import os

from storage.media import store_object
from util.imageutil import download_image, convert_to_heif


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
                            status TEXT,
                            description TEXT,
                            thumbnail_object_name TEXT,
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
        print(chapter.name)

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
    def upload_thumbnail(item: Item, object_name: str):
        with tempfile.TemporaryDirectory() as temp_dir:
            ext = item.thumbnail_url.split('.')[-1]

            original_dest = f"{temp_dir}/original.{ext}"
            compressed_dest = f"{temp_dir}/compressed.heif"

            download_image(item.thumbnail_url, original_dest)
            convert_to_heif(original_dest, compressed_dest, quality=40)

            store_object("mangalib.thumbnail", object_name, compressed_dest)


    @staticmethod
    def is_thumbnail_in_db(item: Item, connection):
        cursor = connection.cursor()

        query = '''
                        SELECT thumbnail_object_name
                        FROM items
                        WHERE item_url = %s
                    '''

        cursor.execute(query, (item.url,))
        result = cursor.fetchone()

        return result is not None


    @staticmethod
    def save_item(item: Item, connection):
        cursor = connection.cursor()

        outdated = DB.is_item_outdated(item, connection)
        thumbnail_in_db = DB.is_thumbnail_in_db(item, connection)
        thumbnail_object_name = f"thumbnail_{item.url.split('/')[-1]}.heif"

        cursor.execute('''
            INSERT INTO items (item_url, last_updated, name, status, description, thumbnail_object_name, views, rating, votes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT(item_url) DO UPDATE SET
                last_updated = excluded.last_updated,
                name = excluded.name,
                status = excluded.status,
                description = excluded.description,
                thumbnail_object_name = excluded.thumbnail_object_name,
                views = excluded.views,
                rating = excluded.rating,
                votes = excluded.votes
                ''', (item.url, item.last_updated.isoformat(), item.name, item.status, item.description,
                      thumbnail_object_name, item.views, item.rating, item.votes))

        cursor.execute('DELETE FROM item_authors WHERE item_url = %s', (item.url,))
        for author in item.authors:
            DB.save_author(author, connection)
            cursor.execute('INSERT INTO item_authors (item_url, author_id) VALUES (%s, %s)', (item.url, author.id))

        cursor.execute('DELETE FROM item_genres WHERE item_url = %s', (item.url,))
        for genre in item.genres:
            DB.save_genre(genre, connection)
            cursor.execute('INSERT INTO item_genres (item_url, genre_id) VALUES (%s, %s)', (item.url, genre.id))

        if not thumbnail_in_db:
            DB.upload_thumbnail(item, thumbnail_object_name)

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
        load_dotenv()

        try:
            return psycopg2.connect(
                dbname=os.environ['DB_NAME'],
                user=os.environ['DB_USER'],
                password=os.environ['DB_PASSWORD'],
                host=os.environ['DB_ADDR'],
                port=os.environ['DB_PORT']
            )

        except psycopg2.OperationalError as e:
            raise RuntimeError("Couldn't connect to database: " + str(e))


if __name__ == "__main__":
    with DB.get_connection() as conn:
        it = Item("https://chapmanganato.to/manga-xu1001055")
        print(DB.is_thumbnail_in_db(it, conn))

        DB.create()

        DB.save_item(it, connection=conn)

