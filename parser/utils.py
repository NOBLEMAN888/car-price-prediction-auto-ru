import json
import random
import time
from bs4 import BeautifulSoup
import re
from urllib.parse import urlsplit, urlunsplit
from config import SLEEP_FROM, SLEEP_TO

NEW_CAR_RE = re.compile(
    r"^https://auto\.ru/cars/new/group/[^/]+/[^/]+/.*$",
    re.IGNORECASE
)

USED_CAR_RE = re.compile(
    r"^https://auto\.ru/cars/used/sale/[^/]+/[^/]+/.*$",
    re.IGNORECASE
)

ENGINE_TYPE_MAP = {
    "GASOLINE": "petrol",
    "DIESEL": "diesel",
    "HYBRID": "hybrid",
    "ELECTRO": "electric",
    "ELECTRIC": "electric"
}

TRANSMISSION_MAP = {
    "AUTOMATIC": "automatic",
    "ROBOT": "robot",
    "MECHANICAL": "manual",
    "VARIATOR": "variator"
}


def is_car_ad_url(url: str) -> bool:
    return bool(NEW_CAR_RE.match(url) or USED_CAR_RE.match(url))


def _clean_url(u: str) -> str:
    parts = urlsplit(u)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def get_listing_links(base_url, page: int, session) -> list[str]:
    url = base_url if page == 1 else f"{base_url}?page={page}"
    r = session.get(url, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml")

    links = set()

    for a in soup.select("a[href]"):
        href = a.get("href")
        if not href:
            continue

        if href.startswith("/"):
            href = "https://auto.ru" + href

        if not (href.startswith("http://") or href.startswith("https://")):
            continue

        if not href.startswith("https://auto.ru/"):
            continue

        href = _clean_url(href)

        if not is_car_ad_url(href):
            continue

        links.add(href)

    return sorted(links)


def _extract_sale_data_attributes(soup):
    div = soup.find("div", id="sale-data-attributes")
    if not div:
        return {}
    raw = div.get("data-bem")
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data.get("sale-data-attributes", {}) or {}


def parse_characteristics(soup: BeautifulSoup) -> dict:
    result = {}

    for row in soup.select("li[class*='CardInfoSummaryComplexRow']"):
        label = row.select_one("div[class*='cellTitle']")
        value = row.select_one("div[class*='cellValue']")
        if not label or not value:
            continue

        key = label.get_text(strip=True).lower()
        val = value.get_text(" ", strip=True)
        result[key] = val

    for row in soup.select("li[class*='CardInfoSummarySimpleRow']"):
        label = row.select_one("div[class*='label']")
        value = row.select_one("div[class*='content']")
        if not label or not value:
            continue

        key = label.get_text(strip=True).lower()
        val = value.get_text(" ", strip=True)
        result[key] = val

    return result


def parse_tax(tax_str: str) -> int | None:
    if not tax_str:
        return None
    digits = re.sub(r"[^\d]", "", tax_str)
    return int(digits) if digits else None


def parse_engine(engine_str: str) -> dict:
    if not engine_str:
        return {}

    result = {}

    vol = re.search(r"(\d+(?:\.\d+)?)\s*л", engine_str)
    hp = re.search(r"(\d+)\s*л\.с", engine_str)
    fuel = None

    fuel_types = ["бензин", "дизель", "электро", "гибрид"]

    for fuel_type in fuel_types:
        if fuel_type in engine_str.lower():
            fuel = fuel_type

    result["engine_volume"] = float(vol.group(1)) if vol else None
    result["power_hp"] = int(hp.group(1)) if hp else None
    result["fuel_type"] = fuel

    return result


def parse_steering_wheel(value: str):
    if not value:
        return None
    v = value.lower()
    if "левый" in v:
        return True
    if "правый" in v:
        return False
    return None


def parse_color(soup):
    meta = soup.find("meta", property="og:description")
    if not meta or not meta.get("content"):
        return None

    text = meta["content"].lower()
    m = re.search(r"цвет\s+([а-яa-zё]+)", text)
    return m.group(1) if m else None


def parse_body_type(soup, sale):
    if sale.get("type"):
        return sale["type"]

    meta = soup.find("meta", property="og:description")
    if not meta:
        return None

    text = meta["content"].lower().strip()
    body_type = text.split()[0]

    return body_type


def parse_car_page(url: str, session, city: str):
    r = session.get(url, timeout=20)
    if r.status_code != 200:
        return None

    soup = BeautifulSoup(r.text, "lxml")

    if not soup.find("div", id="sale-data-attributes"):
        return None

    sale = _extract_sale_data_attributes(soup)

    characteristics = parse_characteristics(soup)
    engine_info = parse_engine(characteristics.get("двигатель"))

    city = city
    is_new = sale.get("state") == "new"

    price = sale.get("price")

    tax_per_year = parse_tax(characteristics.get("налог"))

    year = sale.get("year")
    year = int(year) if year is not None else None

    raw_km_age = sale.get("km-age")
    km_age = int(raw_km_age) if isinstance(raw_km_age, (int, float)) else None

    brand = sale.get("markName")

    model = sale.get("modelName")

    color = parse_color(soup)

    body_type = parse_body_type(soup, sale)

    drive_type = characteristics.get("привод")

    raw_transmission_type = sale.get("transmission")
    transmission_type = TRANSMISSION_MAP.get(raw_transmission_type)

    raw_engine_type = sale.get("engine-type")
    engine_type = ENGINE_TYPE_MAP.get(raw_engine_type)

    engine_volume = None if engine_type == "electric" else engine_info.get("engine_volume")

    raw_power_hp = sale.get("power")
    power_hp = int(raw_power_hp) if isinstance(raw_power_hp, (int, float)) else None

    is_left_hand_drive = parse_steering_wheel(characteristics.get("руль"))

    car = {
        "city": city,
        "is_new": is_new,
        "price": price,
        "tax_per_year": tax_per_year,
        "year": year,
        "km-age": km_age,
        "brand": brand,
        "model": model,
        "color": color,

        "body_type": body_type,
        "drive_type": drive_type,
        "transmission": transmission_type,
        "engine_type": engine_type,
        "engine_volume": engine_volume,
        "power_hp": power_hp,
        "is_left_hand_drive": is_left_hand_drive,

        "url": url,
    }

    return car


def polite_sleep():
    time.sleep(random.uniform(SLEEP_FROM, SLEEP_TO))
