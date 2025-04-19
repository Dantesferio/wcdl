import requests
from bs4 import BeautifulSoup
from rich.progress import Progress
import sqlite3
from pathlib import Path
import os
from wcdl.tools import error
from pyfzf.pyfzf import FzfPrompt
from wcdl.fetch import headers

host = "weebcentral.com"


def search_online(offset: str) -> list[dict] | int:
    """
    output scheme:
        list( --> list of all results
            {
                name: "manga name"
                url: "url for manga's page"
                id: "id of the manga, used in other functions"
            },
            .
            ..
            ...
        )
    """
    page = requests.get(
        f"https://{host}/search/data?offset={offset}&sort=Alphabet&order=Ascending&official=Any&anime=Any&adult=Any&display_mode=Full Display",
        headers=headers
    )
    if page.status_code != 200:
        error(f"connection error, code:{page.status_code}")
        exit(1)

    soup = BeautifulSoup(page.text, "html.parser")

    results = []

    for article in soup.find_all("article", {"class": "bg-base-300"}):
        sections = article.find_all("section")

        link = sections[0].find("a").get("href")
        name = sections[1].find("div").find("a").string
        image_url = sections[0].find("a").find(
            "article").find("picture").find("img").get("src")
        manga_id = link.split("/")[4]
        year = sections[1].find_all("div")[1].find("span").string
        status = sections[1].find_all("div")[2].find("span").string
        type_ = sections[1].find_all("div")[3].find("span").string
        author = sections[1].find_all("div")[4].find("span").string
        tags = []
        for tag in sections[1].find_all("div")[5].find_all("span"):
            tags.append(tag.string.replace(",", ""))

        results.append({
            "name": name,
            "url": link,
            "image": image_url,
            "year": year,
            "status": status,
            "type": type_,
            "author": author,
            "tags": tags,
            "id": manga_id,
        })

    return results


def dump_database_from_servers():
    results = []
    with Progress() as prog:
        task = task = prog.add_task(
            "[blue bold] fetching database", total=8672)
        for i in list(range(0, 8700, 32)):
            results.extend(search_online(i))
            prog.update(task, refresh=True, advance=32)

    return results


def update_database():
    if Path("data.db").exists():
        os.remove("data.db")
    con = sqlite3.connect("data.db")
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE manga(name, url, image, year, status, type, author, id, tags)")
    data = dump_database_from_servers()
    for item in data:
        cur.execute("INSERT INTO manga VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", (
            item["name"],
            item["url"],
            item["image"],
            item["year"],
            item["status"],
            item["type"],
            item["author"],
            item["id"],
            ",".join(item["tags"])
        ))

    con.commit()
    con.close()


def fetch_local_database(fields: list[str]):
    for i in fields:
        if not i in ["name", "url", "image", "year", "status", "type", "author", "id", "tags"]:
            error(f"{i} is not a valid field of data")
            exit(1)

    if not Path("data.db").exists():
        error("data.db not found, please dump a database from online source first")
        exit(1)

    con = sqlite3.connect("data.db")
    cur = con.cursor()
    result = cur.execute(f"SELECT {','.join(fields)} from manga")
    return list(result)


def search_local(prompt=""):
    names = []
    names_ids = {}

    for i in fetch_local_database(["name", "id"]):
        names.append(i[0])
        names_ids[i[0]] = i[1]

    fzf = FzfPrompt()
    result = fzf.prompt(names, f"--query '{prompt}' --layout=reverse")
    return {
        "name": result[0],
        "id": names_ids[result[0]]
    }
