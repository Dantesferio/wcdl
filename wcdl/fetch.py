import requests
from bs4 import BeautifulSoup
from wcdl.tools import error

host = "weebcentral.com"

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    # 'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Sec-GPC': '1',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
}


def search(query: str) -> list[dict]:
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

    params = {
        'author': '',
        'text': query,
        'sort': 'Best Match',
        'order': 'Ascending',
        'official': 'Any',
        'display_mode': 'Full Display',
    }

    page = requests.get(f'https://{host}/search/data',
                        params=params, headers=headers)

    if page.status_code != 200:
        error(f"Connection error: {page.status_code}")
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


def query_chapters(manga_id: str) -> list[dict]:
    """
    input: manga id recived from search() function
    output scheme:
        list( --> list of all chapters the specific manga
            {
                name: chapters name, used when saving the chapter to a .cbz file
                url: url to the read-online page of the chapter
                id: chapters id used in other functions
            },
            .
            ..
            ...
        )

    """
    chap_list = requests.get(
        f"https://{host}/series/{manga_id}/full-chapter-list", headers=headers)
    if chap_list.status_code != 200:
        error(f"Connection error: {chap_list.status_code}")
        exit(1)

    chap_list_soup = BeautifulSoup(chap_list.text, "html.parser")

    reuslts = []

    for div in chap_list_soup.find_all("div", {"class": "flex items-center"}):
        link = div.find("a").get("href")
        name = div.find("a").find_all("span")[1].find("span").string
        reuslts.append({
            "name": name,
            "url": link,
            "id": link.split("/")[-1]
        })

    reuslts.reverse()
    return reuslts


def query_chapter_images(chap_id: str) -> list[str]:
    """
    input scheme: chapter recived from query_chapters function
    output scheme:
        list( --> list of url's for each page of the chapter, the name of image files are in order by default
        )
    """

    chap_images = requests.get(
        f"https://{host}/chapters/{chap_id}/images?is_prev=False&current_page=1&reading_style=long_strip", headers=headers)
    if chap_images.status_code != 200:
        error(f"connection error, status code: {chap_images.status_code}")
        exit(1)

    chap_images_soup = BeautifulSoup(chap_images.text, "html.parser")

    image_urls = []

    for img in chap_images_soup.find("section").find_all("img"):
        image_urls.append(img.get("src"))

    return image_urls
