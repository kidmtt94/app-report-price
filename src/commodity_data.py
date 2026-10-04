"""
Fetch daily commodity prices: gold (SJC + world) and oil (VN retail fuel + world crude).
All sources are free and require no API key.
"""
import re
import html
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import requests

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}
TIMEOUT = 20

# Yahoo Finance tickers for world prices
WORLD_TICKERS = {
    "XAU": "GC=F",    # Gold futures (USD/oz)
    "BRENT": "BZ=F",  # Brent crude (USD/barrel)
    "WTI": "CL=F",    # WTI crude (USD/barrel)
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _clean_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def _parse_vn_number(s: str) -> Optional[float]:
    """Parse '26,560' / '26.560' / '+170' / '-780 ▼' into a number."""
    s = s.strip()
    if not s or s == "-":
        return None
    m = re.search(r"[-+]?\d[\d.,]*", s)
    if not m:
        return None
    num = m.group(0).replace(",", "").replace(".", "")
    try:
        return float(num)
    except ValueError:
        return None


def _parse_tables(page: str) -> List[List[List[str]]]:
    tables = []
    for tb in re.findall(r"<table.*?</table>", page, flags=re.S | re.I):
        rows = []
        for row in re.findall(r"<tr.*?</tr>", tb, flags=re.S | re.I):
            cells = [_clean_html(c) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row, flags=re.S | re.I)]
            if cells:
                rows.append(cells)
        tables.append(rows)
    return tables


# ---------------------------------------------------------------------------
# World prices (Yahoo Finance)
# ---------------------------------------------------------------------------
def fetch_world_price(yahoo_symbol: str) -> Optional[Dict[str, Any]]:
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}?range=5d&interval=1d"
        res = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        res.raise_for_status()
        result = res.json()["chart"]["result"][0]
        closes = [c for c in result["indicators"]["quote"][0]["close"] if c is not None]
        if not closes:
            return None
        price = float(result["meta"].get("regularMarketPrice") or closes[-1])
        prev = float(closes[-2]) if len(closes) > 1 else price
        change = round(price - prev, 2)
        change_pct = round(change / prev * 100, 2) if prev else 0.0
        return {"price": round(price, 2), "prev_close": round(prev, 2), "change": change, "change_pct": change_pct}
    except Exception as e:
        logger.error(f"Error fetching world price {yahoo_symbol}: {e}")
        return None


# ---------------------------------------------------------------------------
# Gold
# ---------------------------------------------------------------------------
def _sjc_price_on(date: datetime) -> Optional[Dict[str, float]]:
    """Return SJC 1L/10L/1KG price (Ho Chi Minh branch) for a specific date."""
    from vnstock.explorer.misc.gold_price import sjc_gold_price
    df = sjc_gold_price(date=date.strftime("%Y-%m-%d"))
    if df is None or df.empty:
        return None
    row = df[df["branch"].str.contains("Hồ Chí Minh", na=False)]
    row = row.iloc[0] if not row.empty else df.iloc[0]
    return {"name": row["name"], "buy": float(row["buy_price"]), "sell": float(row["sell_price"])}


def fetch_sjc_gold() -> Optional[Dict[str, Any]]:
    try:
        today = datetime.now()
        current = _sjc_price_on(today)
        if not current:
            return None

        # Look back up to 7 days for the previous different trading day to compute change
        prev = None
        for i in range(1, 8):
            p = _sjc_price_on(today - timedelta(days=i))
            if p:
                prev = p
                break

        buy_change = current["buy"] - prev["buy"] if prev else 0.0
        sell_change = current["sell"] - prev["sell"] if prev else 0.0
        return {
            "name": current["name"],
            "unit": "VND/lượng",
            "buy": current["buy"],
            "sell": current["sell"],
            "buy_change": buy_change,
            "sell_change": sell_change,
        }
    except Exception as e:
        logger.error(f"Error fetching SJC gold price: {e}")
        return None


def fetch_gold() -> Dict[str, Any]:
    return {
        "sjc": fetch_sjc_gold(),
        "world": fetch_world_price(WORLD_TICKERS["XAU"]),  # USD/oz
    }


# ---------------------------------------------------------------------------
# Oil
# ---------------------------------------------------------------------------
def _fetch_retail_fuel_giaxanghomnay() -> List[Dict[str, Any]]:
    page = requests.get("https://giaxanghomnay.com/", headers=HEADERS, timeout=TIMEOUT).text
    for rows in _parse_tables(page):
        if not rows or "Giá vùng 1" not in " ".join(rows[0]):
            continue
        items = []
        for cells in rows[1:]:
            if len(cells) < 5:
                continue
            items.append({
                "name": cells[0],
                "price_zone1": _parse_vn_number(cells[3]),
                "price_zone2": _parse_vn_number(cells[4]),
                "change": _parse_vn_number(cells[1]) or 0.0,          # thay đổi hôm nay
                "last_adjustment": _parse_vn_number(cells[2]) or 0.0,  # kỳ điều chỉnh gần nhất
            })
        if items:
            return items
    return []


def _fetch_retail_fuel_webgia() -> List[Dict[str, Any]]:
    page = requests.get("https://webgia.com/gia-xang-dau/petrolimex/", headers=HEADERS, timeout=TIMEOUT).text
    for rows in _parse_tables(page):
        if not rows or "Vùng 1" not in " ".join(rows[0]):
            continue
        items = []
        for cells in rows[1:]:
            if len(cells) < 3:
                continue
            p1 = _parse_vn_number(cells[1])
            if p1 is None:
                continue
            items.append({
                "name": cells[0],
                "price_zone1": p1,
                "price_zone2": _parse_vn_number(cells[2]),
                "change": 0.0,
                "last_adjustment": 0.0,
            })
        if items:
            return items
    return []


def fetch_retail_fuel() -> List[Dict[str, Any]]:
    for source in (_fetch_retail_fuel_giaxanghomnay, _fetch_retail_fuel_webgia):
        try:
            items = source()
            if items:
                return items
        except Exception as e:
            logger.error(f"Error fetching retail fuel from {source.__name__}: {e}")
    return []


def fetch_oil() -> Dict[str, Any]:
    return {
        "retail": fetch_retail_fuel(),  # VND/lít
        "world": {
            "BRENT": fetch_world_price(WORLD_TICKERS["BRENT"]),  # USD/thùng
            "WTI": fetch_world_price(WORLD_TICKERS["WTI"]),
        },
    }
