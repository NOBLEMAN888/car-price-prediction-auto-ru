from cookies import COOKIES

BASE_URLS = {
    "moskva_new": "https://auto.ru/moskva/cars/new/",
    "moskva_used": "https://auto.ru/moskva/cars/used/",
    "sankt-peterburg_new": "https://auto.ru/sankt-peterburg/cars/new/",
    "sankt-peterburg_used": "https://auto.ru/sankt-peterburg/cars/used/",
    "vladivostok_new": "https://auto.ru/vladivostok/cars/new/",
    "vladivostok_used": "https://auto.ru/vladivostok/cars/used/",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9",
}

MAX_PAGES = 99
MAX_CARS = 10_000

SLEEP_FROM = 0.8
SLEEP_TO = 1.5

OUTPUT_PATH = "data/raw.csv"
