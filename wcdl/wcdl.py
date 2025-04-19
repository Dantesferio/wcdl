#!/usr/bin/python
import rich.prompt
import wcdl.fetch as fetch
import wcdl.downloader as downloader
import wcdl.database as database
import argparse
import rich
from wcdl.tools import notic, error, warn, success, range_parser
    
def main():
    parser = argparse.ArgumentParser("wcdl", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        "-s", "--search", 
        action="store", 
        default="", 
        help="searching query, if used with -l, the search will be local"
    )
    parser.add_argument(
        "-l", "--local-search", 
        action="store_true", 
        help="using the local database to saerch for manga, the database can be recived using -u"
    )
    parser.add_argument(
        "-r", "--range", 
        action="store", 
        nargs="*", 
        default=["all"],
        help=
    """specifing the chapter to be selected
    [start_num]:[end_num] => select a range of chapters from index [start_num] to index [end_num]
    [single_num] => select a chapter with index of [single_num]
    all|leave empty => select all of the chapters
    new|latest|last => select the last released chapter
    """
    )
    parser.add_argument(
        "-u", "--update-database", 
        action="store_true",
        help="updates the local saerch database, if not already there, it will generate a new one (note that this operation may take some time)"
    )
    parser.add_argument(
        "-d", "--download", 
        action="store_true",
        help="download the selected manga with specified range of chapters"
    )
    parser.add_argument(
        "-j", "--save-to-json", 
        action="store_true",
        help="saves the download link of selected chapters into a json file along with its id and name"    
    )
    parser.add_argument(
        "-c", "--checkout", 
        action="store_true",
        help="fetch metadata of selected work, show status about latest realses"    
    )
    args = parser.parse_args()

    if args.update_database:
        database.update_database()
        success("updated the database")
        exit(0)
    
    if args.search == "" and args.local_search == False:
        search_prompt = rich.prompt.Prompt.ask("[blue bold] search manga ")
    elif args.search == "" and args.local_search == True:
        search_prompt = ""
    else:
        search_prompt = args.search

    notic("searching...")
    if args.local_search:
        selected_manga = database.search_local(args.search)

    else: # if not local, then online
        search_result = fetch.search(search_prompt)
        if type(search_result) is int:
            error(f"connection error while searching online, code:{search_result}")
            exit(1)
        if search_result == []:
            warn("no result were found")
            exit(1)

        table = rich.table.Table(title=f"results : {search_prompt}", box=rich.box.ROUNDED, show_lines=True)
        table.add_column("#", style="white", justify="center")
        table.add_column("Name", style="yellow", justify="center")

        n = 1
        for result in search_result:
            table.add_row(
                str(n),
                result["name"]
            )
            n+=1
        rich.print(table)
        selected = rich.prompt.Prompt.ask("choice to download", choices=[str(i) for i in range(0, n)], default=1, show_choices=False)
        selected_manga = search_result[int(selected)-1]




    if args.save_to_json == args.download == args.checkout == False:
        notic("no download, save-to-json or checkout option was specified, only printing the manga name...")
        print(selected_manga["name"])
        exit(0)

    notic(f"selected {selected_manga['name']}")

    manga_chapter_list = fetch.query_chapters(selected_manga["id"])
    selected_chapters = []
    for r in args.range:
        selected_chapters.extend(
            range_parser(r, manga_chapter_list)
        )

    if args.checkout:
        if args.local_search:
            warn("checkout option only works with online search")
            exit(0)
        items = ["name", "year", "status", "type", "author", "tags"]
        for i in items:
            print(f"{i}:{selected_manga[i]}")
        print("last chapter:", manga_chapter_list[-1]["name"])

    if args.download:
        notic(f"downloading selected range of chapters --> {' '.join(args.range)}")

        downloader.download_chapters_progress(selected_manga["name"], selected_chapters)
        success("Done")
    if args.save_to_json:
        downloader.save_data_to_json(selected_manga["name"], selected_chapters)
        success(f"manga data has been saved to {selected_manga["name"]}.json file")

