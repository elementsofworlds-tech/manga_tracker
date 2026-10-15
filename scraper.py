"""Finds manga prices on Indian online stores.

This file does the searching. app.py shows the results on screen.
You normally never need to edit this file, except to add or fix a store in STORES.
"""
import re
import time
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# STORES. "trusted": True  = a bookstore that sells its own stock.
#         "trusted": False = a marketplace where many different sellers list
#                            items (fakes are possible, so check the seller).
# {q} is replaced by what you typed in the search box.
# These search-page addresses are written from general knowledge and have not
# been tested live. If a store always shows "no results", open its search link
# in your browser, copy the address from the address bar, and replace the URL
# here (put {q} where the search words go).
# ---------------------------------------------------------------------------
STORES = [
    {"name": "Bookswagon", "url": "https://www.bookswagon.com/search-books/{q}", "trusted": True},
    {"name": "SapnaOnline", "url": "https://www.sapnaonline.com/searchproducts?keyword={q}", "trusted": True},
    {"name": "Crossword", "url": "https://www.crossword.in/search?q={q}", "trusted": True},
    {"name": "Amazon.in", "url": "https://www.amazon.in/s?k={q}", "trusted": False},
    {"name": "Flipkart", "url": "https://www.flipkart.com/search?q={q}", "trusted": False},
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}

PRICE_RE = re.compile(r"(?:₹|Rs\.?|INR)\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)")
MIN_PRICE = 100  # manga volumes cost more than this; ignores things like "save ₹50"
SKIP_WORDS_BEFORE_PRICE = ("save", "off", "above", "over", "extra", "flat", "cashback")


def _words(text):
    """Lower-case words of a title, with 'volume' treated the same as 'vol'."""
    text = text.lower().replace("volume", "vol")
    return set(re.findall(r"[a-z0-9]+", text))


def _parse_price(text):
    """Cheapest sensible rupee price found in a block of text (or None)."""
    values = []
    for m in PRICE_RE.finditer(text):
        before = text[max(0, m.start() - 15):m.start()].lower()
        if any(w in before for w in SKIP_WORDS_BEFORE_PRICE):
            continue
        try:
            value = float(m.group(1).replace(",", ""))
        except ValueError:
            continue
        if value >= MIN_PRICE:
            values.append(value)
    return min(values) if values else None


def extract_listings(html, query, base_url, blocked=()):
    """Pull (title, price, link) items out of a store's search-results page."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    wanted = _words(query)

    def is_match(text):
        return len(text) >= 8 and wanted.issubset(_words(text))

    def link_of(a):
        return urljoin(base_url, a["href"]).split("#")[0]

    seen, found = set(), []
    for a in soup.find_all("a", href=True):
        title = a.get_text(" ", strip=True)
        if not is_match(title):
            continue
        url = link_of(a)
        if url in seen:
            continue

        # Walk up from the title to the product "card" that also holds the price.
        node, price, card_text = a, None, ""
        for _ in range(6):
            node = node.parent
            if node is None or node.name in ("body", "html"):
                break
            matching_links = {
                link_of(x)
                for x in node.find_all("a", href=True)
                if is_match(x.get_text(" ", strip=True))
            }
            if len(matching_links) > 1:  # reached a block with several products
                break
            card_text = node.get_text(" ", strip=True)
            price = _parse_price(card_text)
            if price:
                break

        if price is None:
            continue
        if any(b and b in card_text.lower() for b in blocked):
            continue
        seen.add(url)
        found.append({"title": title[:120], "price": price, "url": url})

    found.sort(key=lambda r: r["price"])
    return found[:5]


def search_store(store, query, add_manga_word=True, blocked=()):
    """Search one store. Returns (listings, note, search_page_url)."""
    words = f"{query} manga" if add_manga_word else query
    url = store["url"].format(q=quote_plus(words))
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
    except requests.RequestException:
        return [], "could not connect", url
    if resp.status_code != 200:
        return [], f"store refused the request (HTTP {resp.status_code})", url
    listings = extract_listings(resp.text, query, url, blocked)
    if not listings:
        return [], "no matching prices found (the page may load results with JavaScript, or nothing matched)", url
    return listings, "", url


def search_all(query, stores, add_manga_word=True, blocked=()):
    """Search every store. Returns (rows, notes)."""
    rows, notes = [], []
    for store in stores:
        listings, note, page_url = search_store(store, query, add_manga_word, blocked)
        for item in listings:
            rows.append(
                {
                    "Store": store["name"],
                    "Title": item["title"],
                    "Price (₹)": item["price"],
                    "Seller": "Trusted store" if store["trusted"] else "Marketplace - check seller",
                    "Link": item["url"],
                    "trusted": store["trusted"],
                }
            )
        if not listings:
            notes.append({"store": store["name"], "note": note, "url": page_url})
        time.sleep(1)  # be polite to the stores
    rows.sort(key=lambda r: r["Price (₹)"])
    return rows, notes
