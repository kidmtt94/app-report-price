# 📈 Báo Cáo Chứng Khoán Tự Động — Miễn Phí Hoàn Toàn

Tự động gửi **thông báo chứng khoán về iPhone** mỗi ngày lúc **17:00** (Thứ 2 → Thứ 6).  
Phân tích bằng **AI Gemini**, chạy hoàn toàn **miễn phí** trên GitHub.

---

## ✨ Tính năng — Tất cả đều FREE

| Tính năng | Chi phí |
|---|---|
| 🤖 Phân tích thị trường bằng AI Gemini 2.5 Flash | **Miễn phí** (Google AI Studio) |
| ⏰ Tự động chạy mỗi ngày 17:00 trên GitHub Actions | **Miễn phí** (GitHub) |
| 📱 Gửi thông báo đẩy về iPhone qua Bark | **Miễn phí** (app Bark) |
| 📊 Theo dõi VNINDEX, VN30, VN100 và cổ phiếu riêng | **Miễn phí** |
| 🥇 Báo cáo giá vàng SJC trong nước + Vàng thế giới | **Miễn phí** |
| 🛢️ Báo cáo giá xăng dầu bán lẻ Petrolimex + Dầu Brent/WTI | **Miễn phí** |

---

## 🚀 Cài đặt — Chỉ 4 bước

### Bước 1 — Fork repo này về tài khoản GitHub của bạn

> GitHub Actions chạy dưới tài khoản của **bạn** — nên bạn cần có bản sao repo này trên GitHub của mình.

1. Vào trang repo này trên GitHub
2. Bấm nút **"Fork"** góc trên phải
3. Bấm **"Create fork"** — xong! Bạn đã có repo riêng với đầy đủ code và workflow

---

### Bước 2 — Lấy 2 khóa API


**🤖 Gemini API Key** (để AI phân tích thị trường):
1. Vào trang [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Đăng nhập bằng tài khoản Google
3. Bấm **"Create API Key"** → Copy khóa vừa tạo

**📱 Bark Key** (để nhận thông báo trên iPhone):
1. Mở App Store trên iPhone, tìm và tải app **"Bark"**
2. Mở app Bark → màn hình chính hiển thị sẵn khóa của bạn
3. Copy phần mã sau `https://api.day.app/` — đó là Bark Key

---

### Bước 3 — Cài khóa vào GitHub Secrets

> Đây là nơi lưu khóa an toàn, **không ai xem được ngoài bạn**.

1. Vào repo GitHub của bạn
2. Bấm **Settings** (góc trên phải repo)
3. Chọn **Secrets and variables → Actions**
4. Bấm **"New repository secret"**, thêm lần lượt 2 secret:

| Tên secret | Giá trị |
|---|---|
| `GEMINI_API_KEY` | Dán Gemini API Key vào đây |
| `BARK_KEY` | Dán Bark Key vào đây |

---

### Bước 4 — Tùy chỉnh cổ phiếu theo dõi

Mở file [`.github/workflows/daily-report.yml`](.github/workflows/daily-report.yml), tìm đến dòng lệnh `python main.py`:

```yaml
run: python main.py --watchlist "EVF,PLX,EIB"
```

**Sửa theo ý muốn:**

- Thêm/xóa mã cổ phiếu trong `--watchlist` (cách nhau bằng dấu phẩy):
  ```yaml
  # Ví dụ theo dõi HPG, FPT, VCB:
  run: python main.py --watchlist "HPG,FPT,VCB"
  ```

- Muốn thay chỉ số thị trường (mặc định là `VNINDEX,VN30,VN100`), thêm `--symbols`:
  ```yaml
  run: python main.py --symbols "VNINDEX,VN30" --watchlist "HPG,FPT"
  ```

Sau khi sửa, **commit & push** là xong — GitHub tự động áp dụng ngay.

---

## ⏰ Lịch chạy tự động

Hệ thống tự chạy **~17:00 ICT, Thứ 2 → Thứ 6** — không cần làm gì thêm sau khi cài đặt xong.

> **Lưu ý:** GitHub Actions không đảm bảo chạy chính xác đến phút. Do hàng triệu job chạy đồng thời trên GitHub, thông báo thực tế có thể đến muộn hơn **5–15 phút** so với giờ cài đặt — hoàn toàn bình thường.

Muốn **chạy thử thủ công**: Vào repo → **Actions** → **Daily Stock Market Report** → **Run workflow**.
