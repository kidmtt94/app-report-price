# 📈 Vietnam Stock Market Mini SWE Agent

Hệ thống Agent tự động hóa thu thập, phân tích dữ liệu thị trường chứng khoán Việt Nam (**VNINDEX, VN30, VN100** và danh mục theo dõi) mỗi ngày lúc **17:00** và gửi thông báo trực tiếp về iPhone qua **Bark**.

---

## 🚀 Tính năng nổi bật

1. **Thu thập dữ liệu tự động**: Cập nhật giá đóng cửa, mức tăng/giảm điểm, % biến động và thanh khoản phiên của VNINDEX, VN30, VN100.
2. **Bộ não phân tích Gemini 2.5 Flash**: Tự động đánh giá trạng thái thị trường, nhóm ngành dẫn dắt và đưa ra nhận định xu hướng súc tích.
3. **Thông báo đẩy như iMessage qua Bark**: Reng chuông và hiện pop-up notification trực tiếp trên màn hình khóa iPhone.
4. **Nhật ký Markdown**: Tự động lưu trữ báo cáo chi tiết vào thư mục `./reports/YYYY-MM-DD.md`.
5. **Cấu hình 100% qua CLI & .env**: Tùy biến linh hoạt qua tham số dòng lệnh.
6. **Lập lịch tự động 1-click**: Tích hợp sẵn Windows Task Scheduler chạy đúng 17:00 từ Thứ Hai đến Thứ Sáu.

---

## 🛠️ Cài đặt nhanh

### 1. Cài đặt thư viện
```powershell
pip install -r requirements.txt
```

### 2. Chuẩn bị Key
- **Bark Key**: Tải app **Bark - Customed Notifications** trên App Store (iPhone). Mở app copy khóa cá nhân (dạng `https://api.day.app/YOUR_KEY/` -> lấy `YOUR_KEY`).
- **Gemini API Key**: Lấy miễn phí tại [Google AI Studio](https://aistudio.google.com/app/apikey).

*(Có thể tạo file `.env` từ file `.env.example` hoặc truyền trực tiếp qua tham số dòng lệnh CLI).*

---

## 💻 Hướng dẫn sử dụng

### 1. Chạy thử nghiệm không gửi thông báo (`--dry-run`)
```powershell
python main.py --dry-run --skip-llm
```

### 2. Chạy với Gemini và danh mục theo dõi riêng (`--watchlist`)
```powershell
python main.py --gemini-api-key "AIzaSy..." --bark-key "YOUR_BARK_KEY" --watchlist "HPG,FPT,VCB"
```

### 3. Xem danh sách toàn bộ các cờ tùy biến
```powershell
python main.py --help
```

| Tham số | Mặc định | Mô tả |
| :--- | :--- | :--- |
| `--symbols` | `VNINDEX,VN30,VN100` | Danh sách chỉ số thị trường |
| `--watchlist` | *(trống)* | Danh sách mã cổ phiếu cá nhân (vd: `HPG,FPT`) |
| `--gemini-api-key`| Đọc từ `.env` | Google Gemini API Key |
| `--gemini-model` | `gemini-2.5-flash` | Model Gemini sử dụng |
| `--bark-key` | Đọc từ `.env` | Khóa thiết bị Bark trên iOS |
| `--bark-server` | `https://api.day.app`| Server Bark |
| `--report-dir` | `./reports` | Thư mục lưu trữ báo cáo Markdown |
| `--dry-run` | `False` | Chỉ in ra console và lưu file, không bắn Bark |
| `--skip-llm` | `False` | Dùng mẫu báo cáo thuần thống kê, không gọi Gemini |

---

## ⏰ Cài đặt tự động chạy lúc 17:00 (Windows Task Scheduler)

Mở **PowerShell** trong thư mục dự án và chạy:

```powershell
# Cài đặt tự động chạy vào 17:00 từ Thứ 2 đến Thứ 6:
.\setup_scheduler.ps1 -BarkKey "YOUR_BARK_KEY" -GeminiApiKey "YOUR_GEMINI_KEY" -Watchlist "HPG,FPT"

# Kích hoạt chạy thử ngay lập tức qua Task Scheduler:
Start-ScheduledTask -TaskName "VNStock-Daily-Agent"

# Khi muốn gỡ bỏ lịch:
.\setup_scheduler.ps1 -Uninstall
```

