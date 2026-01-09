from typing import Any, Dict, List, Optional


def build_params(keyword: str, page: int = 1, page_size: int = 10,
                 mintime: str = "", maxtime: str = "") -> Dict[str, Any]:
    """
    构造 gov.cn 搜索接口参数（最小集）
    """
    return {
        "t": "zhengcelibrary",
        "q": keyword,
        "timetype": "timeqb",
        "mintime": mintime,
        "maxtime": maxtime,
        "sort": "score",
        "sortType": "1",
        "searchfield": "title",
        "pcodeJiguan": "",
        "childtype": "",
        "subchildtype": "",
        "tsbq": "",
        "pubtimeyear": "",
        "puborg": "",
        "pcodeYear": "",
        "pcodeNum": "",
        "filetype": "",
        "p": page,
        "n": page_size,
        "inpro": "",
        "bmfl": "",
        "dup": "",
        "orpro": "",
        "type": "gwyzcwjk",
    }


def parse_items(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    list_vo = (
        data.get("searchVO", {})
        .get("catMap", {})
        .get("gongwen", {})
        .get("listVO", [])
    )

    items = []
    for it in list_vo:
        title = (it.get("title") or "").replace("<em>", "").replace("</em>", "")
        summary = (it.get("summary") or "").replace("<em>", "").replace("</em>", "")

        items.append({
            "title": title,
            "pubtimeStr": it.get("pubtimeStr", ""),
            "puborg": it.get("puborg", ""),
            "pcode": it.get("pcode", ""),
            "summary": summary,
            "url": it.get("url", ""),
            "index": it.get("index", ""),
            "id": it.get("id", ""),
        })
    return items


