import json
import logging
from typing import Dict, Any, Tuple, Optional
import requests

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """Bạn là một chuyên gia tài chính và chuyên viên phân tích thị trường chứng khoán Việt Nam sắc bén, súc tích và khách quan.
Nhiệm vụ của bạn là nhận dữ liệu thị trường cuối ngày (EOD) của các chỉ số VNINDEX, VN30, VN100 và các mã cổ phiếu theo dõi, sau đó tạo ra 2 nội dung:
1. "notification": Một bản tin ngắn gọn (3-4 dòng, tối đa 150 từ) để bắn pop-up notification lên màn hình khóa điện thoại iPhone. Cần hiển thị rõ điểm số, mức tăng/giảm (+/- điểm, +/-%), thanh khoản và 1 câu nhận định cốt lõi.
2. "report_markdown": Báo cáo phân tích đầy đủ định dạng Markdown lưu vào nhật ký, gồm:
   - Tổng quan diễn biến phiên giao dịch (Điểm số, thanh khoản so với trung bình, độ rộng thị trường).
   - Phân tích nhóm VN30, VN100 và các nhóm ngành nổi bật.
   - Nhận định xu hướng và khuyến nghị hành động ngắn hạn cho phiên tiếp theo.

Định dạng trả về BẮT BUỘC là JSON hợp lệ theo cấu trúc:
{
  "notification": "Chuỗi văn bản ngắn hiển thị notification",
  "report_markdown": "Chuỗi văn bản định dạng Markdown đầy đủ"
}
Không kèm theo bất kỳ văn bản ngoài nào khác ngoài khối JSON này.
"""


class MarketAgentBrain:
    def __init__(self, api_key: Optional[str], model: str = "gemini-flash-lite-latest"):
        self.api_key = api_key
        self.model = model

    def analyze(self, market_data: Dict[str, Any]) -> Tuple[str, str]:
        """
        Takes structured market data, prompts Gemini, and returns (short_notification, full_markdown).
        """
        if not self.api_key:
            return self._generate_fallback_summary(market_data, note="[Chưa cấu hình GEMINI_API_KEY]")

        user_content = (
            f"Dưới đây là dữ liệu thị trường chứng khoán Việt Nam hôm nay ({market_data.get('date', 'Hôm nay')}):\n\n"
            f"{json.dumps(market_data, ensure_ascii=False, indent=2)}\n\n"
            f"Hãy phân tích và trả về đúng định dạng JSON như đã hướng dẫn."
        )

        # Fallback candidates list in case of temporary demand spikes (503/404)
        candidates = [self.model, "gemini-flash-lite-latest", "gemini-3.6-flash", "gemini-3.5-flash-lite"]
        seen = set()
        model_queue = [m for m in candidates if not (m in seen or seen.add(m))]

        last_error = ""
        for model_name in model_queue:
            try:
                return self._call_gemini_sdk(user_content, model_name=model_name)
            except Exception as e_sdk:
                logger.debug(f"SDK call failed with {model_name}: {e_sdk}")
                try:
                    return self._call_gemini_rest(user_content, model_name=model_name)
                except Exception as e_rest:
                    logger.debug(f"REST call failed with {model_name}: {e_rest}")
                    last_error = str(e_rest)
                    continue

        # If all fail, use deterministic fallback
        return self._generate_fallback_summary(
            market_data,
            note=f"[Lỗi gọi Gemini: {last_error[:100]}]"
        )

    def _call_gemini_sdk(self, user_prompt: str, model_name: str) -> Tuple[str, str]:
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config={
                    "system_instruction": SYSTEM_PROMPT,
                    "response_mime_type": "application/json",
                },
            )
            raw_text = response.text or ""
            clean_text = raw_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()

            data = json.loads(clean_text)
            return data.get("notification", ""), data.get("report_markdown", "")
        except ImportError:
            # Try legacy google.generativeai if installed
            import google.generativeai as genai_legacy
            genai_legacy.configure(api_key=self.api_key)
            model = genai_legacy.GenerativeModel(
                model_name=model_name,
                system_instruction=SYSTEM_PROMPT,
                generation_config={"response_mime_type": "application/json"}
            )
            response = model.generate_content(user_prompt)
            data = json.loads(response.text)
            return data.get("notification", ""), data.get("report_markdown", "")

    def _call_gemini_rest(self, user_prompt: str, model_name: str) -> Tuple[str, str]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_PROMPT}]
            },
            "contents": [
                {"role": "user", "parts": [{"text": user_prompt}]}
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.3
            }
        }
        res = requests.post(url, json=payload, timeout=30)
        res.raise_for_status()
        result_json = res.json()
        raw_text = result_json["candidates"][0]["content"]["parts"][0]["text"]
        
        # Clean any accidental markdown code fence
        clean_text = raw_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        data = json.loads(clean_text)
        return data.get("notification", ""), data.get("report_markdown", "")

    def _generate_fallback_summary(self, market_data: Dict[str, Any], note: str = "") -> Tuple[str, str]:
        """
        Deterministic rule-based summary when LLM is unavailable or skipped.
        """
        date_str = market_data.get("date", "Hôm nay")
        indices = market_data.get("indices", {})
        watchlist = market_data.get("watchlist", {})

        notif_lines = [f"📊 Thị trường {date_str}:"]
        for sym in ["VNINDEX", "VN30", "VN100"]:
            if sym in indices:
                d = indices[sym]
                sign = "+" if d.get("change", 0) >= 0 else ""
                notif_lines.append(f"• {sym}: {d.get('close', 'N/A')} ({sign}{d.get('change', 0):.2f}đ | {sign}{d.get('change_pct', 0):.2f}%)")

        if note:
            notif_lines.append(f"({note})")
        short_notif = "\n".join(notif_lines)

        report_lines = [
            f"# BÁO CÁO THỊ TRƯỜNG CHỨNG KHOÁN ({date_str})",
            "",
            "## 1. Diễn biến các chỉ số chính",
            "| Chỉ số | Điểm đóng cửa | Biến động | Thay đổi (%) | Khối lượng |",
            "| :--- | :---: | :---: | :---: | :---: |",
        ]
        for sym, d in indices.items():
            sign = "+" if d.get("change", 0) >= 0 else ""
            vol = f"{d.get('volume', 0):,}" if isinstance(d.get('volume'), (int, float)) else str(d.get('volume', 'N/A'))
            report_lines.append(
                f"| **{sym}** | {d.get('close', 'N/A')} | {sign}{d.get('change', 0):.2f} | {sign}{d.get('change_pct', 0):.2f}% | {vol} |"
            )

        if watchlist:
            report_lines.extend([
                "",
                "## 2. Cổ phiếu theo dõi (Watchlist)",
                "| Mã | Giá đóng cửa | Biến động | Thay đổi (%) |",
                "| :--- | :---: | :---: | :---: |",
            ])
            for ticker, d in watchlist.items():
                sign = "+" if d.get("change", 0) >= 0 else ""
                report_lines.append(
                    f"| **{ticker}** | {d.get('close', 'N/A')} | {sign}{d.get('change', 0):.2f} | {sign}{d.get('change_pct', 0):.2f}% |"
                )

        if note:
            report_lines.extend(["", f"> [!NOTE]\n> {note}"])

        full_md = "\n".join(report_lines)
        return short_notif, full_md

