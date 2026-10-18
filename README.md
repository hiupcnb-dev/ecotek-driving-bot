# 🚗 EcoTek Driving Study Bot - Cloud Edition 24/7 (Bằng C1)

Hệ thống Trợ lý Học & Thi Sát Hạch Lái Xe Hạng C1 chạy trên Đám mây (Cloud) trực tuyến 24/7, không phụ thuộc vào máy tính cá nhân.

## ✨ Tính Năng Nổi Bật

1. **Trực Tuyến 24/7 Mọi Lúc Mọi Nơi:**
   - Bot hoạt động liên tục trên Render.com, dùng thoải mái trên điện thoại di động ngay cả khi tắt máy tính PC.
   - Cơ chế **Anti-Sleep Keep-Alive** tự động ping mỗi 9 phút để máy chủ Render luôn thức, không bao giờ rơi vào trạng thái ngủ đông.

2. **Ngân Hàng 600 Câu Sát Hạch Chuẩn 100% Bộ GTVT:**
   - 60 Câu Điểm Liệt (Cấm sai tuyệt đối).
   - Đầy đủ 6 Chương lý thuyết & Luật TTATGTĐB 2024.
   - Hệ thống Biển Báo & Sa Hình có ảnh đồ họa chuẩn mực.
   - Sổ tay câu sai (tự động lưu lại các câu làm nhầm để ôn lại).

3. **Thi Thử Sát Hạch Hạng C1 (40 Câu / 24 Phút):**
   - Chấm điểm tự động: Đạt từ 36/40 câu trở lên & không sai câu điểm liệt.
   - Hiển thị chi tiết đáp án và phân tích mẹo ngay sau khi nộp bài.

4. **Tương Tác Bằng Giọng Nói Thông Minh (Voice AI):**
   - Đọc câu hỏi và các lựa chọn tự động bằng âm thanh sinh động (gTTS).
   - Gửi tin nhắn giọng riêng biệt giải thích đáp án và mẹo nhớ.
   - Nhận diện giọng nói của học viên qua Voice Note Telegram (Faster-Whisper).
   - Chế độ **Sách Nói 600 Câu Rảnh Tay:** Tự động phát liên tiếp các câu hỏi để nghe khi đi đường hoặc trước khi ngủ mà không cần chạm màn hình.

5. **Đồng Bộ Dữ Liệu 2 Chiều Với PC:**
   - PC khi mở và học trên EcoTek LMS sẽ tự động gửi giờ học thực tế lên Cloud (`POST /api/sync_status`).
   - Bot trên điện thoại luôn hiển thị chuẩn xác số giờ đã học hôm nay, bảo vệ ngắt an toàn lúc 9h30 tránh vượt trần 10 tiếng/ngày.
   - Cho phép bấm nút "Bật Tự Học Trên Máy" từ xa ngay trên điện thoại.

## 🚀 Triển Khai Nhanh Lên Render.com

1. Vào Dashboard Render: https://dashboard.render.com
2. Bấm **New** -> **Web Service**.
3. Chọn Repository: `hiupcnb-dev/ecotek-driving-bot`.
4. Render sẽ tự động nhận diện `render.yaml` hoặc cài đặt:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python app.py`
5. Thêm biến môi trường `RENDER_EXTERNAL_URL`: `https://<ten-dich-vu>.onrender.com` để kích hoạt Keep-Alive.
