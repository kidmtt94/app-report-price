import os
import sys
from pathlib import Path
from datetime import datetime

# Prevent encoding crashes on Windows terminal
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

from src.config import parse_args
from src.market_data import fetch_market_snapshot
from src.commodity_data import fetch_gold, fetch_oil
from src.agent_brain import MarketAgentBrain
from src.notifier import BarkNotifier


def main():
    config = parse_args()

    print("=" * 60)
    print("🚀 VIETNAM STOCK MARKET MINI SWE AGENT")
    print(f"🕒 Khởi chạy lúc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📈 Chỉ số theo dõi: {', '.join(config.symbols)}")
    if config.watchlist:
        print(f"👀 Cổ phiếu theo dõi: {', '.join(config.watchlist)}")
    print(f"🤖 LLM Model: {config.gemini_model if not config.skip_llm else 'SKIPPED (Template)'}")
    print(f"📱 Bark Notifier: {'ENABLED' if config.bark_key else 'NO KEY PROVIDED'} (Dry run: {config.dry_run})")
    print("=" * 60)

    # 1. Fetch Market Data
    print("\n[1/4] 📥 Đang lấy dữ liệu thị trường...")
    snapshot = fetch_market_snapshot(indices=config.symbols, watchlist=config.watchlist)
    if not snapshot["indices"]:
        print("[ERROR] Không thể lấy được dữ liệu các chỉ số. Vui lòng kiểm tra lại kết nối mạng!")
        sys.exit(1)

    print(f"✅ Đã tải xong dữ liệu phiên giao dịch ngày: {snapshot['date']}")
    for sym, d in snapshot["indices"].items():
        sign = "+" if d.get("change", 0) >= 0 else ""
        print(f"   • {sym}: {d.get('close')} ({sign}{d.get('change')}đ | {sign}{d.get('change_pct')}%) - Khối lượng: {d.get('volume'):,}")

    print("\n📥 Đang lấy giá vàng & giá dầu...")
    snapshot["gold"] = fetch_gold()
    snapshot["oil"] = fetch_oil()
    sjc = snapshot["gold"].get("sjc")
    xau = snapshot["gold"].get("world")
    if sjc:
        print(f"   • Vàng SJC: Mua {sjc['buy']:,.0f} / Bán {sjc['sell']:,.0f} VND/lượng")
    if xau:
        print(f"   • Vàng thế giới: ${xau['price']:,.2f}/oz ({xau['change_pct']:+.2f}%)")
    for name, d in snapshot["oil"].get("world", {}).items():
        if d:
            print(f"   • Dầu {name}: ${d['price']:,.2f}/thùng ({d['change_pct']:+.2f}%)")
    print(f"   • Xăng dầu bán lẻ: {len(snapshot['oil'].get('retail', []))} mặt hàng")

    # 2. Analyze with Agent Brain
    print("\n[2/4] 🧠 Đang phân tích thị trường với Agent Brain...")
    brain = MarketAgentBrain(api_key=config.gemini_api_key, model=config.gemini_model)
    if config.skip_llm:
        short_notif, full_markdown = brain._generate_fallback_summary(snapshot, note="Chạy chế độ --skip-llm")
    else:
        short_notif, full_markdown = brain.analyze(snapshot)

    print("✅ Phân tích hoàn tất.")

    # 3. Save Markdown Report Locally
    print("\n[3/4] 💾 Đang lưu báo cáo chi tiết...")
    report_dir = Path(config.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"{snapshot['date']}.md"
    report_file.write_text(full_markdown, encoding="utf-8")
    print(f"✅ Đã lưu báo cáo tại: {report_file.resolve()}")

    # 4. Send Push Notification via Bark
    print("\n[4/4] 📲 Đang gửi thông báo về iPhone qua Bark...")
    notifier = BarkNotifier(bark_key=config.bark_key, server_url=config.bark_server)
    
    # Formulate notification title with VNINDEX change
    vnindex_data = snapshot["indices"].get("VNINDEX")
    if vnindex_data:
        sign = "+" if vnindex_data.get("change", 0) >= 0 else ""
        title = f"📊 VN-Index {snapshot['date']}: {vnindex_data.get('close')} ({sign}{vnindex_data.get('change')}đ)"
    else:
        title = f"📊 Báo cáo Chứng khoán {snapshot['date']}"

    success = notifier.send(
        title=title,
        body=short_notif,
        group="ChungKhoan",
        sound="minuet",
        is_dry_run=config.dry_run,
    )

    print("\n" + "=" * 60)
    print("🎉 TÁC VỤ HOÀN TẤT THÀNH CÔNG!")
    print("=" * 60)


if __name__ == "__main__":
    main()

