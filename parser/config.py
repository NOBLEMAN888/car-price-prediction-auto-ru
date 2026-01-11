from cookies import COOKIES

BASE_URL = "https://auto.ru/sankt-peterburg/cars/all/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9",
}

MAX_PAGES = 1
MAX_CARS = 10_000

SLEEP_FROM = 0.8
SLEEP_TO = 1.5

OUTPUT_PATH = "data/raw.csv"
