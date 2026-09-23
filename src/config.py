import argparse
import os
from dataclasses import dataclass
from typing import List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


DEFAULT_GEMINI_API_KEY = "AQ.Ab8RN6JYLtPpgz2C9hT4MeF3Rx1n0y6LsHz9sgUcMDQGguUFKg"


@dataclass
class AppConfig:
    symbols: List[str]
    watchlist: List[str]
    gemini_api_key: Optional[str]
    gemini_model: str
    bark_key: Optional[str]
    bark_server: str
    report_dir: str
    dry_run: bool
    skip_llm: bool


def parse_args() -> AppConfig:
    parser = argparse.ArgumentParser(
        description="Vietnam Stock Market Mini SWE Agent - Daily 17:00 Summary & Bark Notifier",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--symbols",
        type=str,
        default="VNINDEX,VN30,VN100",
        help="Comma-separated list of market indices to monitor.",
    )
    parser.add_argument(
        "--watchlist",
        type=str,
        default="",
        help="Optional comma-separated list of stock tickers (e.g. 'HPG,FPT,VCB').",
    )
    parser.add_argument(
        "--gemini-api-key",
        type=str,
        default=os.getenv("GEMINI_API_KEY", DEFAULT_GEMINI_API_KEY),
        help="Google Gemini API Key (or set GEMINI_API_KEY environment variable).",
    )
    parser.add_argument(
        "--gemini-model",
        type=str,
        default="gemini-2.5-flash",
        help="Gemini model to use for analysis.",
    )
    parser.add_argument(
        "--bark-key",
        type=str,
        default=os.getenv("BARK_KEY", ""),
        help="Bark device key for iOS push notification (or set BARK_KEY env var).",
    )
    parser.add_argument(
        "--bark-server",
        type=str,
        default="https://api.day.app",
        help="Bark server base URL.",
    )
    parser.add_argument(
        "--report-dir",
        type=str,
        default="./reports",
        help="Directory to save daily markdown reports.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without sending push notifications to Bark (outputs to console and file only).",
    )
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Skip Gemini LLM call and generate a standard template summary.",
    )

    args = parser.parse_args()

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    watchlist = [s.strip().upper() for s in args.watchlist.split(",") if s.strip()]

    return AppConfig(
        symbols=symbols,
        watchlist=watchlist,
        gemini_api_key=args.gemini_api_key.strip() if args.gemini_api_key else None,
        gemini_model=args.gemini_model,
        bark_key=args.bark_key.strip() if args.bark_key else None,
        bark_server=args.bark_server.rstrip("/"),
        report_dir=args.report_dir,
        dry_run=args.dry_run,
        skip_llm=args.skip_llm,
    )

