import os
import zipfile
from pathlib import Path
import requests
import concurrent.futures as futures
from urllib import parse
from rich.progress import Progress
import json
from wcdl.fetch import query_chapter_images, headers
from wcdl.tools import warn


def make_cbz(files: list[str], output: str, del_files=False) -> int:
    with zipfile.ZipFile(output, "w") as file:
        for f in files:
            if not Path(f).exists():
                raise FileNotFoundError(f"{f}")
            file.write(f)
            if del_files:
                os.remove(f)

    return 0


def chmkdir(p: str) -> int:
    pth = Path(p)
    if not pth.exists():
        os.mkdir(str(pth))
        os.chdir(str(pth))
        return 0
    else:
        if pth.is_file():
            raise NotADirectoryError(str(pth))
        os.chdir(str(pth))
        return 0


def download(url: str) -> int:
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        return res.status_code

    filename = os.path.basename(parse.urlparse(url).path)
    with open(filename, "wb") as file:
        for chunk in res.iter_content(10*1024):
            file.write(chunk)

    return 0


def download_chapter(manga_name: str, chapter_name: str, chapter_id: str) -> int:
    chmkdir(manga_name)
    if Path(chapter_name+".cbz").exists():
        os.chdir("..")
        return 3

    chapter_images = query_chapter_images(chapter_id)
    with futures.ThreadPoolExecutor(max_workers=10) as executor:
        threads = []
        threads_urls = {}
        for url in chapter_images:
            threads.append(
                executor.submit(download, url)
            )
            threads_urls[executor.submit(download, url)] = url

        for thread in futures.as_completed(threads):
            if thread.result() != 0:
                threads.append(
                    executor.submit(download, threads_urls[thread])
                )

    file_names = [
        os.path.basename(parse.urlparse(url).path) for url in chapter_images
    ]
    result = make_cbz(file_names, chapter_name+".cbz", True)
    os.chdir("..")
    return result


def download_chapter_progress(manga_name: str, chapter_name: str, chapter_id: str) -> int:
    chmkdir(manga_name)
    if Path(chapter_name+".cbz").exists():
        os.chdir("..")
        return 3
    chapter_images = query_chapter_images(chapter_id)
    with Progress() as prog:
        task = prog.add_task(
            f"[blue bold] Downloading {chapter_name}", total=len(chapter_images))
        with futures.ThreadPoolExecutor(max_workers=10) as executor:
            threads = []
            threads_urls = {}
            for url in chapter_images:
                threads.append(
                    executor.submit(download, url)
                )
                threads_urls[executor.submit(download, url)] = url

            for thread in futures.as_completed(threads):
                if thread.result() != 0:
                    threads.append(
                        executor.submit(download, threads_urls[thread])
                    )
                    warn(
                        f"connection error with code {thread.result()} while downloading images of chapter, retrying...")

                prog.update(task, refresh=True, advance=1)

    file_names = [
        os.path.basename(parse.urlparse(url).path) for url in chapter_images
    ]
    result = make_cbz(file_names, chapter_name+".cbz", True)
    os.chdir("..")
    return result


def download_chapters(manga_name: str, chapters: list[dict]) -> list:
    skipped = []
    for chapter in chapters:
        res = download_chapter(manga_name, chapter["name"], chapter["id"])
        if res != 0:
            skipped.append((res, chapter))

    return skipped


def download_chapters_progress(manga_name: str, chapters: list[dict]) -> list:
    skipped = []

    for chapter in chapters:
        res = download_chapter_progress(
            manga_name, chapter["name"], chapter["id"])
        if res == 3:
            warn(f"{chapter["name"]} was already downloaded, skipping...")
        if res != 0:
            skipped.append((res, chapter))

    return skipped


def save_data_to_json(manga_name: str, chapters: list[dict]):
    data = {}
    with Progress() as prog:
        task = prog.add_task(
            f"[blue bold] getting download links for {manga_name}", total=len(chapters))
        for chapter in chapters:
            data[chapter["name"]] = {
                "id": chapter["id"]
            }
            images = query_chapter_images(chapter["id"])

            data[chapter["name"]]["links"] = images
            prog.update(task, refresh=True, advance=1)

    with open(f"{manga_name}.json", "w") as file:
        json.dump(data, file)
