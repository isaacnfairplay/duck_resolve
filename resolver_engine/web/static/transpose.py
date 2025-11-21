from bs4 import BeautifulSoup


def transpose_table_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return html
    rows = table.find_all("tr")
    grid = [[cell.get_text() for cell in row.find_all(["th", "td"])] for row in rows]
    transposed = list(map(list, zip(*grid)))
    new_table = soup.new_tag("table", **{"class": "data-table transposed"})
    for row in transposed:
        tr = soup.new_tag("tr")
        for cell in row:
            td = soup.new_tag("td")
            td.string = cell
            tr.append(td)
        new_table.append(tr)
    return str(new_table)
