import rich

def notic(msg):
    rich.print(f"[italic blue] {msg}")

def warn(msg):
    rich.print(f"[bold yellow] [WARNING]: {msg}")

def error(msg):
    rich.print(f"[bold red] [ERROR]: {msg}")

def success(msg):
    rich.print(f"[italic green] {msg}")


def range_parser(r: str, chapter_list: list[dict]):
    if r.lower() in ["all", "a", "t", "total", None]:
        return chapter_list

    if r.lower() in ["l", "latest", "last", "new"]:
        return [chapter_list[-1]]

    if ":" in r:
        a, b = r.split(":")
        if int(a) > len(chapter_list) or int(a) <= 0:
            error(f"{a} was specifiec for lower bboundary of download range while the chapters start with {chapter_list[0]["name"]}")
            exit(1)
        
        if int(b) > len(chapter_list) or int(b) <= 0:
            error(f"{a} was specifiec for upper bboundary of download range while there is only {len(chapter_list)} chapters avalable")
            exit(1)
        
        return chapter_list[int(a) - 1: int(b)]
    
    if r.isdigit():
        if int(r) > len(chapter_list) or int(r) <= 0:
            error(f"{r} is out of range, there are only {len(chapter_list)} chapters avalible")
            exit(1)
        
        return [chapter_list[int(r)-1]]
    else:
        error(f"invalid range {r}")
        exit(1)