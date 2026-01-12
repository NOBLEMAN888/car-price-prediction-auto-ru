import os

import requests
import pandas as pd

from config import (
    COOKIES,
    BASE_URLS,
    HEADERS,
    MAX_PAGES,
    MAX_CARS,
    OUTPUT_PATH,
)
from utils import (
    get_listing_links,
    parse_car_page,
    polite_sleep,
)


def run_parser():
    session = requests.Session()
    session.headers.update(HEADERS)
    session.cookies.update(COOKIES)

    if os.path.exists(OUTPUT_PATH):
        existing = pd.read_csv(OUTPUT_PATH)
        seen_urls = set(existing["url"].dropna())
    else:
        seen_urls = set()

    results = []

    for city, base_url in BASE_URLS.items():
        print(f"[START] Searching for {city} cars, url: {base_url}")
        for page in range(1, MAX_PAGES + 1):

            links = get_listing_links(base_url, page, session)
            print(f"[INFO] Page {page}, found {len(links)} links")

            if not links:
                print(f"[INFO] No listings on page {page}, stopping.")
                break

            for link in links:
                if link in seen_urls:
                    continue

                car = parse_car_page(link, session, city.split("_")[0])

                if car:
                    if car["url"] in seen_urls:
                        continue

                    seen_urls.add(car["url"])
                    results.append(car)
                else:
                    print("[WARN] Empty car:", link)
                    continue

                if len(results) >= MAX_CARS:
                    break

                polite_sleep()

            if len(results) >= MAX_CARS:
                break

        new_df = pd.DataFrame(results)

        if os.path.exists(OUTPUT_PATH):
            old_df = pd.read_csv(OUTPUT_PATH)
            df = pd.concat([old_df, new_df], ignore_index=True)
        else:
            df = new_df

        df = df.drop_duplicates(subset=["url"])
        df.to_csv(OUTPUT_PATH, index=False)
        print(f"[DONE] Saved {len(df)} total rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    run_parser()
