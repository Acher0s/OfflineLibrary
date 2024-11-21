from dotenv import load_dotenv
import os
from minio import Minio
from minio.error import S3Error


def store_object(bucket_name: str, object_name: str, object_path: str):
    client = get_client()

    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)

    try:
        client.fput_object(bucket_name, object_name, object_path)
    except S3Error as e:
        print("Error occurred, couldn't save object:", e)

def get_object(bucket_name: str, object_name: str, destination: str):
    client = get_client()
    try:
        client.fget_object(bucket_name, object_name, destination)
    except S3Error as e:
        print("Error occurred:", e)

def get_client():
    load_dotenv()

    return Minio(f"{os.environ['MINIO_ADDR']}:{os.environ['MINIO_PORT']}",
                 access_key=os.environ['MINIO_ACCESS_KEY'],
                 secret_key=os.environ['MINIO_SECRET_KEY'],
                 secure=False
                 )

if __name__ == "__main__":
    store_object("mangalib.thumbnails", "test", "../thumbnail.heif")
    # get_object("mangalib.thumbnails", "thumbnail_manga-ah1003442.heif", "../retrieved.heif")