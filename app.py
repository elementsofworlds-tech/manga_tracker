"""Manga Price Tracker (India) - the screen you look at.

Start it with:  streamlit run app.py
"""
import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st

from scraper import STORES, search_all

DB_FILE = "manga_tracker.db"


# ----------------------------- saved data ---------------------------------
def get_db():
    con = sqlite3.connect(DB_FILE)
    con.execute("CREATE TABLE IF NOT EXISTS watch (query TEXT PRIMARY KEY)")
    con.execute(
        "CREATE TABLE IF NOT EXISTS history ("
        "ts TEXT, query TEXT, store TEXT, title TEXT, price REAL, url TEXT, trusted INTEGER)"
    )
    return con


def watch_list():
    with get_db() as con:
        return [r[0] for r in con.execute("SELECT query FROM watch ORDER BY query")]


def add_watch(query):
    with get_db() as con:
        con.execute("INSERT OR IGNORE INTO watch (query) VALUES (?)", (query,))


def remove_watch(query):
    with get_db() as con:
        con.execute("DELETE FROM watch WHERE query = ?", (query,))
        con.execute("DELETE FROM history WHERE query = ?", (query,))


def save_check(query, rows):
    """Save the cheapest listing from each store for this check."""
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    best = {}
    for r in rows:
        if r["Store"] not in best or r["Price (₹)"] < best[r["Store"]]["Price (₹)"]:
            best[r["Store"]] = r
    with get_db() as con:
        for r in best.values():
            con.execute(
                "INSERT INTO history VALUES (?,?,?,?,?,?,?)",
                (stamp, query, r["Store"], r["Title"], r["Price (₹)"], r["Link"], int(r["trusted"])),
            )


def summary_for(query):
    with get_db() as con:
        df = pd.read_sql_query("SELECT * FROM history WHERE query = ?", con, params=(query,))
    if df.empty:
        return None
    stamps = sorted(df["ts"].unique())
    latest = df[df["ts"] == stamps[-1]].sort_values("price").iloc[0]
    previous = None
    if len(stamps) > 1:
        previous = df[df["ts"] == stamps[-2]]["price"].min()
    return {
        "Manga": query,
        "Cheapest now (₹)": latest["price"],
        "Store": latest["store"],
        "Seller": "Trusted store" if latest["trusted"] else "Marketplace - check seller",
        "Last check (₹)": previous,
        "Lowest ever (₹)": df["price"].min(),
        "Checked on": stamps[-1],
        "Link": latest["url"],
    }


# ------------------------------- the page ---------------------------------
st.set_page_config(page_title="Manga Price Tracker", page_icon="📚", layout="wide")
st.title("📚 Manga Price Tracker (India)")
st.caption("Compares manga prices across Indian stores. Always confirm the price and seller on the store's page before paying.")

with st.sidebar:
    st.header("Settings")
    use_marketplaces = st.checkbox("Include Amazon.in and Flipkart", value=True,
                                   help="These list many sellers, so check who the seller is before buying.")
    add_manga_word = st.checkbox("Add the word 'manga' to searches", value=True)
    blocked_text = st.text_area("Sellers to avoid (one name per line)", value="",
                                help="Any listing mentioning one of these names is hidden.")
    st.caption("Tip: ask other collectors which sellers sell fakes and add them here.")

blocked = [b.strip().lower() for b in blocked_text.splitlines() if b.strip()]
stores = [s for s in STORES if s["trusted"] or use_marketplaces]
link_col = st.column_config.LinkColumn("Link", display_text="Open")

if "results" not in st.session_state:
    st.session_state.results = None

tab_search, tab_watch = st.tabs(["🔍 Search", "⭐ Watchlist"])

# ------------------------------ search tab --------------------------------
with tab_search:
    query = st.text_input("Manga title and volume", placeholder="e.g. Jujutsu Kaisen vol 5")
    if st.button("Search all stores", type="primary") and query.strip():
        with st.spinner("Checking stores... this takes about 10-20 seconds"):
            rows, notes = search_all(query.strip(), stores, add_manga_word, blocked)
        st.session_state.results = (query.strip(), rows, notes)

    if st.session_state.results:
        q, rows, notes = st.session_state.results
        st.subheader(f"Results for: {q}")
        if rows:
            df = pd.DataFrame(rows).drop(columns=["trusted"])
            st.dataframe(df, hide_index=True, use_container_width=True,
                         column_config={"Link": link_col,
                                        "Price (₹)": st.column_config.NumberColumn(format="₹%.0f")})
            cheapest_trusted = [r for r in rows if r["trusted"]]
            if cheapest_trusted:
                c = cheapest_trusted[0]
                st.success(f"Cheapest from a trusted store: ₹{c['Price (₹)']:.0f} at {c['Store']}")
            if st.button("⭐ Add this to my watchlist"):
                add_watch(q)
                save_check(q, rows)
                st.success("Added. Open the Watchlist tab to see it.")
        else:
            st.warning("No prices could be read for this search.")
        for n in notes:
            st.write(f"**{n['store']}**: {n['note']}. [Open the store's search page]({n['url']})")

# ----------------------------- watchlist tab ------------------------------
with tab_watch:
    items = watch_list()
    if not items:
        st.info("Your watchlist is empty. Search for a manga and press 'Add this to my watchlist'.")
    else:
        if st.button("🔄 Check all prices now", type="primary"):
            progress = st.progress(0.0)
            for i, item in enumerate(items):
                rows, _ = search_all(item, stores, add_manga_word, blocked)
                if rows:
                    save_check(item, rows)
                progress.progress((i + 1) / len(items))
            st.success("Prices updated.")

        table = [s for s in (summary_for(i) for i in items) if s]
        if table:
            st.dataframe(pd.DataFrame(table), hide_index=True, use_container_width=True,
                         column_config={"Link": link_col,
                                        "Cheapest now (₹)": st.column_config.NumberColumn(format="₹%.0f"),
                                        "Last check (₹)": st.column_config.NumberColumn(format="₹%.0f"),
                                        "Lowest ever (₹)": st.column_config.NumberColumn(format="₹%.0f")})
            for t in table:
                if t["Last check (₹)"] and t["Cheapest now (₹)"] < t["Last check (₹)"]:
                    st.success(f"📉 {t['Manga']} dropped to ₹{t['Cheapest now (₹)']:.0f} at {t['Store']}")

        st.divider()
        to_remove = st.selectbox("Remove something from the watchlist", ["-"] + items)
        if to_remove != "-" and st.button("Remove"):
            remove_watch(to_remove)
            st.rerun()
