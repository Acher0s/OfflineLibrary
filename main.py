import scan
import util
from item import Item
from tqdm import tqdm

if __name__ == "__main__":
    total_bytes = 0
    chapters = 0
    images = 0

    results = []

    item_urls = list(scan.get_all_item_urls(10))
    with tqdm(total=len(item_urls), desc="Processing Items") as pbar_items:
        for item_url in item_urls:
            try:
                item = Item(item_url)
                item_chapters = len(item.chapters)
                chapters += item_chapters

                with tqdm(total=item_chapters, desc=f"Processing Chapters of {item_url}") as pbar_chapters:
                    for chapter in item.chapters:
                        try:
                            total_bytes += chapter.get_size()
                            images += len(chapter.image_urls)

                            results.append(
                                f"Processed {chapter.url}: Bytes={total_bytes}, Images={images}"
                            )
                        except Exception as e:
                            results.append(f"Error processing chapter {chapter.url}: {e}")
                            print(f"Something went wrong, skipping {chapter.url}")
                        finally:
                            pbar_chapters.update(1)
            except Exception as e:
                results.append(f"Error processing item {item_url}: {e}")
                print(f"Something went wrong, skipping {item_url}")
            finally:
                pbar_items.update(1)

    with open("results.txt", "w") as file:
        file.write("\n".join(results))

    print(f"Total bytes: {util.format_size(total_bytes)}")
    print(f"Total chapters: {chapters}")
    print(f"Total images: {images}")