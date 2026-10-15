MANGA PRICE TRACKER (INDIA) - SETUP GUIDE
=========================================

This runs on a computer (Windows, Mac or Linux). You can then open it on your
phone too, if the phone is on the same Wi-Fi.

ONE-TIME SETUP
--------------
1. Install Python: go to python.org -> Downloads -> install it.
   On Windows, tick the box "Add Python to PATH" on the first screen.
2. Unzip this folder somewhere easy, e.g. your Desktop.
3. Open a terminal in the folder:
   - Windows: open the folder, click the address bar, type  cmd  and press Enter.
   - Mac: right-click the folder -> "New Terminal at Folder".
4. Type this and press Enter (wait until it finishes):
       pip install -r requirements.txt

EVERY TIME YOU WANT TO USE IT
-----------------------------
1. Open a terminal in the folder (step 3 above).
2. Type this and press Enter:
       streamlit run app.py
3. Your browser opens the app. To use it on your phone, open the "Network URL"
   shown in the terminal (phone must be on the same Wi-Fi).
4. Close the terminal window to stop the app.

HOW TO USE
----------
- Search tab: type a title and volume (e.g. "Jujutsu Kaisen vol 5") and press
  Search. You get prices from each store, cheapest first.
- "Trusted store" means a bookstore selling its own stock. "Marketplace" means
  Amazon.in / Flipkart, where many sellers list items - check the seller name
  on the product page before paying, because fake manga is common.
- Add manga to the Watchlist, then press "Check all prices now" whenever you
  like. It remembers earlier prices and tells you when one drops.
- Sidebar: untick the marketplaces, or list seller names to hide.

IMPORTANT - PLEASE READ
-----------------------
- This was written without being able to test it on the live shopping sites.
  Some stores may show "no matching prices found". Reasons: the store loads its
  results with JavaScript, it blocks automated visits (Amazon and Flipkart
  often do), or its search address changed. The app still shows a link to that
  store's own search page so you can check by hand.
- Prices are read automatically and can occasionally be wrong (for example the
  MRP instead of the selling price). Always confirm on the store's page.
- Store websites usually forbid automated reading in their terms. Use this
  lightly, for yourself only: a few searches a day, not hundreds.
- To fix a store's search address, open scraper.py in Notepad and edit the
  STORES list at the top.
