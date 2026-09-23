import os
import sys
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Prevent terminal encoding issues on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

os.environ["VNSTOCK_TELEMETRY"] = "off"
try:
    import vnai
    vnai.disable_telemetry()
except Exception:
    pass

logger = logging.getLogger(__name__)


def fetch_symbol_data(symbol: str, count_back: int = 5) -> Optional[Dict[str, Any]]:
    """
    Fetch OHLCV history for an index or stock symbol using vnstock.
    """
    try:
        from vnstock.api.quote import Quote
        q = Quote(symbol=symbol, source="VCI")
        df = q.history(count_back=count_back)
        if df is None or df.empty:
            logger.warning(f"No data returned for {symbol}")
            return None

        # Sort by time ascending
        df = df.sort_values(by="time").reset_index(drop=True)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        close = float(latest["close"])
        prev_close = float(prev["close"]) if len(df) > 1 else close
        change = round(close - prev_close, 2)
        change_pct = round((change / prev_close * 100), 2) if prev_close != 0 else 0.0

        volume = int(latest["volume"]) if "volume" in latest and latest["volume"] is not None else 0

        # Calculate avg volume of recent sessions
        avg_vol = int(df["volume"].mean()) if "volume" in df else 0

        date_val = latest["time"]
        if hasattr(date_val, "strftime"):
            date_str = date_val.strftime("%Y-%m-%d")
        else:
            date_str = str(date_val)[:10]

        return {
            "symbol": symbol,
            "date": date_str,
            "close": close,
            "prev_close": prev_close,
            "open": float(latest.get("open", close)),
            "high": float(latest.get("high", close)),
            "low": float(latest.get("low", close)),
            "change": change,
            "change_pct": change_pct,
            "volume": volume,
            "avg_volume_5d": avg_vol,
        }
    except Exception as e:
        logger.error(f"Error fetching data for symbol {symbol}: {e}")
        return None


def fetch_market_snapshot(indices: List[str], watchlist: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Collects market snapshot for all requested indices and watchlist tickers.
    """
    indices_data = {}
    watchlist_data = {}
    latest_date = datetime.now().strftime("%Y-%m-%d")

    for sym in indices:
        data = fetch_symbol_data(sym)
        if data:
            indices_data[sym] = data
            latest_date = data["date"]

    if watchlist:
        for ticker in watchlist:
            data = fetch_symbol_data(ticker)
            if data:
                watchlist_data[ticker] = data

    return {
        "date": latest_date,
        "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "indices": indices_data,
        "watchlist": watchlist_data,
    }

