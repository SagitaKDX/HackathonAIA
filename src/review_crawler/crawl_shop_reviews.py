from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


FOODY_ROOT = "https://www.foody.vn"
DEFAULT_LINK_FILE = Path("link_food_hcm.txt")
DEFAULT_OUTPUT_DIR = Path("output")
VN_TZ = timezone(timedelta(hours=7))


@dataclass(frozen=True)
class ShopTarget:
    source_url: str
    foody_review_url: str
    city_slug: str
    shop_slug: str


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFD", value)
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def read_link_file(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Link file not found: {path}")

    links = []
    for line in path.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if value and value != "link error":
            links.append(value)
    return links


def split_shop_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        raise ValueError(f"Cannot parse city/shop slug from URL: {url}")
    return parts[0], parts[1]


def build_target(url: str) -> ShopTarget:
    city_slug, shop_slug = split_shop_url(url)
    foody_review_url = f"{FOODY_ROOT}/{city_slug}/{shop_slug}/binh-luan"
    return ShopTarget(
        source_url=url,
        foody_review_url=foody_review_url,
        city_slug=city_slug,
        shop_slug=shop_slug,
    )


def find_shop_url(shop_query: str, links: list[str]) -> str:
    query = normalize_text(shop_query)
    if not query:
        raise ValueError("Shop query is empty after normalization")

    best_url = ""
    best_score = 0
    query_tokens = set(query.split("-"))

    for url in links:
        try:
            _, shop_slug = split_shop_url(url)
        except ValueError:
            continue

        slug_tokens = set(shop_slug.split("-"))
        overlap = len(query_tokens & slug_tokens)
        score = overlap

        if query == shop_slug:
            score = 100
        elif query in shop_slug:
            score = 90
        elif query_tokens and query_tokens <= slug_tokens:
            score = 80 + overlap

        if score > best_score:
            best_url = url
            best_score = score

    if not best_url or best_score <= 0:
        raise ValueError(f"No matching shop found in link file for: {shop_query}")
    return best_url


def resolve_target(args: argparse.Namespace) -> ShopTarget:
    if args.url:
        return build_target(args.url)

    links = read_link_file(args.link_file)
    if args.index is not None:
        if args.index < 0 or args.index >= len(links):
            raise IndexError(f"--index must be between 0 and {len(links) - 1}")
        return build_target(links[args.index])

    if args.shop:
        return build_target(find_shop_url(args.shop, links))

    if not links:
        raise ValueError(f"No links found in {args.link_file}")
    return build_target(links[0])


def fetch_text(url: str, *, referer: str | None = None, timeout: int = 30) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    if referer:
        headers["Referer"] = referer

    request = Request(url, headers=headers)
    with urlopen(request, timeout=timeout) as response:
        raw = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace")


def fetch_json(
    url: str,
    *,
    params: dict[str, Any],
    referer: str,
    timeout: int = 30,
) -> dict[str, Any]:
    query = urlencode({key: "" if value is None else value for key, value in params.items()})
    request_url = f"{url}?{query}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": referer,
        "X-Requested-With": "XMLHttpRequest",
    }

    request = Request(request_url, headers=headers)
    with urlopen(request, timeout=timeout) as response:
        raw = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
        return json.loads(raw.decode(charset, errors="replace"))


def extract_json_variable(html: str, variable_name: str) -> dict[str, Any]:
    match = re.search(rf"\bvar\s+{re.escape(variable_name)}\s*=\s*", html)
    if not match:
        raise ValueError(f"Cannot find JS variable: {variable_name}")

    start = match.end()
    while start < len(html) and html[start].isspace():
        start += 1

    if start >= len(html) or html[start] not in "{[":
        raise ValueError(f"JS variable {variable_name} does not start with JSON")

    opener = html[start]
    closer = "}" if opener == "{" else "]"
    depth = 0
    in_string = False
    escaped = False

    for idx in range(start, len(html)):
        char = html[idx]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return json.loads(html[start : idx + 1])

    raise ValueError(f"Cannot parse full JSON payload for: {variable_name}")


def parse_foody_date(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"/Date\((\d+)\)/", value)
    if not match:
        return value
    milliseconds = int(match.group(1))
    return datetime.fromtimestamp(milliseconds / 1000, tz=VN_TZ).isoformat()


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def meta_content(soup: BeautifulSoup, property_name: str) -> str:
    tag = soup.find("meta", attrs={"property": property_name})
    return clean_text(tag.get("content")) if tag else ""


def parse_restaurant(html: str, nav_data: dict[str, Any]) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")

    address = clean_text(" ".join(soup.select_one(".res-common-add").stripped_strings)) if soup.select_one(".res-common-add") else ""
    opening_time_node = soup.select_one(".micro-timesopen")
    if opening_time_node:
        popup = opening_time_node.select_one(".opening-time-popup")
        if popup:
            popup.decompose()
        opening_time = clean_text(" ".join(opening_time_node.stripped_strings))
    else:
        opening_time = ""
    price_range = clean_text(" ".join(soup.select_one(".res-common-minmaxprice").stripped_strings)) if soup.select_one(".res-common-minmaxprice") else ""

    return {
        "restaurant_id": nav_data.get("RestaurantID"),
        "name": clean_text(meta_content(soup, "og:title").split(" ở ")[0]),
        "address": address,
        "opening_time": opening_time,
        "price_range": price_range,
        "microsite_url": nav_data.get("MicrositeUrl"),
        "total_reviews": nav_data.get("TotalReviews"),
        "location": nav_data.get("Location"),
        "url_rewrite_name": nav_data.get("UrlRewriteName"),
        "is_delivery": nav_data.get("IsDelivery"),
    }


def normalize_comment(comment: dict[str, Any]) -> dict[str, Any]:
    user = comment.get("User") or {}
    return {
        "comment_id": comment.get("Id"),
        "parent_id": comment.get("ParentId"),
        "comment": clean_text(comment.get("Comment")),
        "created_at": parse_foody_date(comment.get("CreatedOn")),
        "created_label": comment.get("Date"),
        "user": {
            "id": user.get("Id"),
            "display_name": user.get("DisplayName"),
            "url": urljoin(FOODY_ROOT, user.get("Url") or ""),
        },
    }


def normalize_review(item: dict[str, Any], review_url: str) -> dict[str, Any]:
    owner = item.get("Owner") or {}
    pictures = item.get("Pictures") or []

    return {
        "review_id": item.get("Id"),
        "restaurant_id": item.get("ResId"),
        "title": clean_text(item.get("Title")),
        "comment": clean_text(item.get("Description")),
        "rating": item.get("AvgRating"),
        "created_at": parse_foody_date(item.get("CreatedDate")),
        "created_label": item.get("CreatedOnTimeDiff"),
        "device_name": item.get("DeviceName"),
        "review_url": urljoin(FOODY_ROOT, item.get("Url") or ""),
        "source_page": review_url,
        "total_views": item.get("TotalViews") or item.get("TotalView"),
        "total_like": item.get("TotalLike"),
        "total_comment": item.get("TotalComment"),
        "total_pictures": item.get("TotalPictures"),
        "author": {
            "id": owner.get("Id"),
            "display_name": owner.get("DisplayName"),
            "url": urljoin(FOODY_ROOT, owner.get("Url") or ""),
            "total_reviews": owner.get("TotalReviews"),
            "total_pictures": owner.get("TotalPictures"),
        },
        "pictures": [
            {
                "id": picture.get("Id"),
                "url": picture.get("Url"),
                "caption": clean_text(picture.get("Description")),
            }
            for picture in pictures
        ],
        "comments": [normalize_comment(comment) for comment in item.get("Comments") or []],
    }


def fetch_more_reviews(
    restaurant_id: int,
    last_id: int | None,
    count: int,
    exclude_ids: str,
    referer: str,
) -> dict[str, Any]:
    return fetch_json(
        f"{FOODY_ROOT}/__get/Review/ResLoadMore",
        referer=referer,
        params={
            "ResId": restaurant_id,
            "LastId": last_id,
            "Count": count,
            "Type": 1,
            "fromOwner": "",
            "isLatest": "true",
            "HasPicture": "",
            "ExcludeIds": exclude_ids,
            "t": int(time.time() * 1000),
        },
    )


def crawl_reviews(target: ShopTarget, limit: int) -> dict[str, Any]:
    html = fetch_text(target.foody_review_url)
    nav_data = extract_json_variable(html, "initDataNavBar")
    review_data = extract_json_variable(html, "initDataReviews")

    restaurant = parse_restaurant(html, nav_data)
    restaurant_id = review_data.get("ResId") or restaurant.get("restaurant_id")
    if not restaurant_id:
        raise ValueError("Cannot find restaurant id in Foody page")

    raw_items = list(review_data.get("Items") or [])
    total = review_data.get("Total") or len(raw_items)
    count = review_data.get("Count") or 10
    last_id = review_data.get("LastId")
    exclude_ids = review_data.get("ExcludeIds") or ""

    while len(raw_items) < min(limit, total):
        page = fetch_more_reviews(
            restaurant_id=restaurant_id,
            last_id=last_id,
            count=count,
            exclude_ids=exclude_ids,
            referer=target.foody_review_url,
        )
        new_items = page.get("Items") or []
        if not new_items:
            break
        raw_items.extend(new_items)
        last_id = page.get("LastId")
        count = page.get("Count") or count
        exclude_ids = page.get("ExcludeIds") or exclude_ids

    selected = raw_items[:limit]
    reviews = [normalize_review(item, target.foody_review_url) for item in selected]

    return {
        "shop": {
            **restaurant,
            "city_slug": target.city_slug,
            "shop_slug": target.shop_slug,
            "source_url": target.source_url,
            "foody_review_url": target.foody_review_url,
        },
        "crawl": {
            "crawled_at": datetime.now(tz=VN_TZ).isoformat(),
            "requested_limit": limit,
            "total_available": total,
            "reviews_saved": len(reviews),
            "last_id": last_id,
            "count": count,
        },
        "reviews": reviews,
    }


def safe_output_stem(shop_slug: str) -> str:
    return re.sub(r"[^a-z0-9_-]+", "_", shop_slug.lower()).strip("_") or "shop"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, data: dict[str, Any]) -> None:
    rows = []
    shop = data["shop"]
    for review in data["reviews"]:
        rows.append(
            {
                "review_id": review["review_id"],
                "restaurant_id": review["restaurant_id"],
                "shop_name": shop.get("name"),
                "rating": review["rating"],
                "comment": review["comment"],
                "created_at": review["created_at"],
                "created_label": review["created_label"],
                "author_id": review["author"]["id"],
                "author_name": review["author"]["display_name"],
                "total_like": review["total_like"],
                "total_comment": review["total_comment"],
                "total_pictures": review["total_pictures"],
                "review_url": review["review_url"],
                "source_page": review["source_page"],
                "comments_json": json.dumps(review["comments"], ensure_ascii=False),
            }
        )

    fieldnames = [
        "review_id",
        "restaurant_id",
        "shop_name",
        "rating",
        "comment",
        "created_at",
        "created_label",
        "author_id",
        "author_name",
        "total_like",
        "total_comment",
        "total_pictures",
        "review_url",
        "source_page",
        "comments_json",
    ]

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Crawl Foody/ShopeeFood review data for one shop from a shop name, URL, or link-file index."
    )
    parser.add_argument("--shop", help="Shop name to match against link_food_hcm.txt")
    parser.add_argument("--url", help="Direct ShopeeFood/Foody shop URL")
    parser.add_argument("--index", type=int, help="Zero-based index in the link file. Useful for quick tests.")
    parser.add_argument("--link-file", type=Path, default=DEFAULT_LINK_FILE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--limit", type=int, default=50, help="Maximum reviews to save")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.limit < 1:
        print("--limit must be >= 1", file=sys.stderr)
        return 2

    try:
        target = resolve_target(args)
        data = crawl_reviews(target, args.limit)
        args.output_dir.mkdir(parents=True, exist_ok=True)

        stem = safe_output_stem(target.shop_slug)
        json_path = args.output_dir / f"reviews_{stem}.json"
        csv_path = args.output_dir / f"reviews_{stem}.csv"
        write_json(json_path, data)
        write_csv(csv_path, data)

        shop = data["shop"]
        crawl = data["crawl"]
        print("Crawl success")
        print(f"Shop: {shop.get('name') or target.shop_slug}")
        print(f"Source URL: {target.source_url}")
        print(f"Foody review URL: {target.foody_review_url}")
        print(f"Total available: {crawl['total_available']}")
        print(f"Reviews saved: {crawl['reviews_saved']}")
        print(f"JSON: {json_path}")
        print(f"CSV: {csv_path}")
        return 0
    except (HTTPError, URLError, TimeoutError, ValueError, FileNotFoundError, IndexError, json.JSONDecodeError) as exc:
        print(f"Crawl failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
