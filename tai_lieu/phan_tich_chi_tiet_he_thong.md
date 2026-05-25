# Phân Tích Chi Tiết Từng Module Trong Hệ Thống

Tài liệu này cung cấp cái nhìn mổ xẻ chi tiết vào từng tệp tin (file) mã nguồn của dự án. Hệ thống được thiết kế theo kiến trúc **MVC (Model-View-Controller)** kết hợp với mô hình **Đa luồng (Multi-threading)** để đảm bảo xử lý AI và phần cứng không làm treo giao diện.

---

## 1. Giao diện người dùng (View) - `giao_dien_chinh.py`

**Độ dài:** ~493 dòng
**Nhiệm vụ:** Chịu trách nhiệm hiển thị (UI) và nhận tương tác từ người dùng. Không chứa bất kỳ logic tính toán AI hay ra quyết định phần cứng nào.

**Các tính năng cốt lõi:**
1. **Thiết kế giao diện bằng Tkinter:** Sử dụng thư viện đồ họa chuẩn của Python. UI được chia thành 3 cột chính:
   - *Cột trái:* Danh sách biển số (Whitelist).
   - *Cột giữa:* Camera trực tiếp, kết quả nhận diện (chữ to), trạng thái hệ thống.
   - *Cột phải:* Số lượng xe trong bãi (để check sức chứa), các nút bấm mở/đóng thủ công, công tắc chế độ Tự động/Thủ công.
2. **Luồng cập nhật bất đồng bộ (`_poll`):**
   - Thay vì đứng đợi Controller trả kết quả, UI có một hàm `_poll()` được gọi lại mỗi 200ms bằng `root.after()`.
   - Hàm này sẽ lấy trạng thái mới nhất từ Controller (ảnh camera mới, log mới, trạng thái barie) để vẽ lại (refresh) lên màn hình.
3. **Quản lý đa luồng (Graceful Shutdown):** 
   - Hàm `_on_closing()` bắt sự kiện khi user nhấn nút X (đóng cửa sổ). Nó sẽ ra lệnh cho Controller dừng mọi thứ, tắt Camera, ngắt Serial một cách an toàn rồi mới `root.destroy()`.

---

## 2. Bộ não điều khiển (Controller) - `dieu_khien_he_thong.py`

**Độ dài:** ~448 dòng
**Nhiệm vụ:** Là "Trái tim" của hệ thống. Nó đứng ở giữa để điều phối UI, Camera, AI, CSDL và Arduino. 

**Các đặc điểm kỹ thuật phức tạp:**
1. **Quản lý 3 luồng công nhân (Worker Threads):**
   - *Luồng Camera:* Liên tục đọc ảnh từ USB Camera (~30 FPS).
   - *Luồng AI (`_ai_worker`):* Chờ lấy ảnh từ hàng đợi `q_ai`, mang đi chạy YOLO + OCR, rồi ném kết quả vào `q_msg`.
   - *Luồng Cảm biến (`_sensor_worker`):* Chạy vòng lặp vô tận mỗi 100ms để đọc dữ liệu Serial gửi về từ Arduino (xe_vao, xe_ra).
2. **Luồng Logic Tự Động (Auto Logic):**
   - Khi có người bật công tắc "Tự động": Cảm biến VÀO phát hiện xe -> Gửi lệnh bắt đầu chụp ảnh -> Nếu AI báo biển số hợp lệ VÀ bãi còn chỗ -> Gọi hàm `_cho_xe_vao()` -> Ghi CSDL -> Gửi lệnh `VAO_MO` xuống Arduino.
   - Khi xe ra: Cảm biến RA phát hiện xe -> Gửi lệnh `RA_MO` -> Mở barie ra -> Đợi cảm biến không còn xe -> Đóng barie -> Trừ số lượng trong CSDL.
3. **Cơ chế chống kẹp xe (Anti-Pinch Logic):**
   - Hàm `auto_close()`. Khi hệ thống định đóng barie sau 5 giây, nó sẽ check xem cảm biến còn đang báo `1` (có xe đứng ngáng) hay không. Nếu có xe, nó set cờ `cho_dong = True` và đợi thêm 500ms để check lại. Tuyệt đối không đóng barie nếu xe chưa đi qua hết.
4. **Xử lý Timeout AI:**
   - Đôi khi PaddleOCR bị treo ngầm. Controller có bộ đếm thời gian `_check_ai_timeout()`. Nếu gửi ảnh đi quá 8 giây mà AI không trả lời, nó sẽ tự động Reset trạng thái để tiếp tục nhận xe mới.

---

## 3. Cơ Sở Dữ Liệu (Model) - `quan_ly_du_lieu.py`

**Độ dài:** ~110 dòng
**Nhiệm vụ:** Quản lý lưu trữ bằng SQLite. File DB cực nhẹ (`.db`).

**Thiết kế bảng (Tables):**
1. **`cai_dat`**: Bảng Key-Value lưu cấu hình. Hiện dùng để lưu Sức chứa tối đa của bãi (mặc định là 3 xe).
2. **`bien_so_hop_le`**: Danh sách trắng (Whitelist). Chỉ những biển số có trong này mới được mở barie vào.
3. **`xe_trong_bai`**: Lưu các xe đang hiện diện trong bãi. Phục vụ việc đếm chỗ trống và chống việc 1 xe "vào 2 lần" (gian lận).

**Điểm nhấn kỹ thuật:**
- **Thread-Safety (An toàn đa luồng):** Vì cả UI Thread và AI Thread đều có thể thao tác CSDL, toàn bộ các hàm (thêm, xóa, đọc) đều được bọc trong một rào chắn `threading.Lock()`.
- **Database Caching:** Tránh việc giao diện (chạy 200ms/lần) liên tục Select CSDL gây nghẽn ổ cứng, file Controller có một biến cờ `_db_cache_dirty`. CSDL chỉ được Select lại khi có sự thay đổi thực sự (có xe vào/ra).

---

## 4. Giao Tiếp Phần Cứng - `giao_tiep_arduino.py`

**Độ dài:** ~95 dòng
**Nhiệm vụ:** Mở cổng COM và nói chuyện với Arduino qua cáp USB bằng giao thức Serial.

**Điểm nhấn kỹ thuật:**
- **RLock (Re-entrant Lock):** Khác với Lock thường, RLock cho phép cùng 1 thread khóa nhiều lần mà không bị kẹt (deadlock). Giúp việc vừa đọc vừa ghi cổng Serial không bị xung đột.
- **Auto-Reconnect:** Module này có khả năng tự động quét các cổng COM khả dụng. Nếu dây cáp vô tình bị rút ra và cắm lại, hệ thống sẽ cố gắng kết nối lại thay vì crash luôn phần mềm.
- **Giao thức Chuỗi (String Protocol):** 
  - Máy tính gửi: `VAO_MO\n`, `VAO_DONG\n`
  - Arduino gửi: `CAM_BIEN:xe_vao=1,xe_ra=0\n`
  Mỗi lệnh kết thúc bằng dấu xuống dòng `\n`. Dễ debug, có thể dùng Arduino IDE Serial Monitor để gõ lệnh bằng tay kiểm tra.

---

## 5. Firmware Vi Điều Khiển - `dieu_khien_barie_lm393.ino`

**Độ dài:** ~150 dòng (viết bằng C++)
**Nhiệm vụ:** Mã nguồn nạp trực tiếp vào board mạch Arduino. Chịu trách nhiệm phần cơ điện.

**Cách hoạt động:**
1. **Thư viện Servo.h:** Điều khiển 2 động cơ Servo (Pin 9 và 10) đóng vai trò làm thanh chắn. Góc `0` độ là đóng, `90` độ là mở.
2. **Interrupt / Polling Cảm biến:** Đọc tín hiệu Digital từ 2 module cảm biến hồng ngoại LM393 (Pin 2 và 3). Khi có vật cản, cảm biến trả về `LOW` (0). Khi không có, trả về `HIGH` (1).
3. **Debounce (Chống nhiễu):** Arduino không gửi tín hiệu liên tục. Nó ghi nhớ trạng thái cũ (`last_xe_vao`). Chỉ khi nào trạng thái thay đổi (Từ Không xe -> Có xe, hoặc ngược lại) VÀ duy trì trong một khoảng thời gian nhất định, nó mới đẩy dòng chữ `CAM_BIEN:...` qua dây cáp lên máy tính. Giảm tải dữ liệu cho đường truyền Serial.

---

## 6. Khối Trí Tuệ Nhân Tạo - `nhan_dien_bien_so.py`

**Độ dài:** ~305 dòng
**Nhiệm vụ:** Nhận ảnh, trả về text.

*(Chi tiết hàm đã được phân tích ở tài liệu riêng `phan_tich_code_nhan_dien.md`)*.

**Tóm tắt các điểm chốt:**
- **Pipeline 5 bước:** YOLO cắt vùng -> OpenCV tạo 3 phiên bản (Gốc, CLAHE, Otsu) -> PaddleOCR đọc chữ -> Heuristic ép kiểu Số/Chữ theo luật Việt Nam -> Regex chấm điểm chọn kết quả cao nhất.
- **Warm-up:** Chạy nháp ngay khi khởi động để nạp mô hình vào RAM. Tránh hiện tượng xe đầu tiên vào bị trễ 5 giây. 

---

## TỔNG KẾT

Hệ thống được thiết kế theo tư duy **Decoupling (Khử liên kết chặt)**. 
- Nếu Arduino bị hỏng, người dùng vẫn có thể bấm nút "Mở tay" trên phần mềm. 
- Nếu Camera hỏng, hệ thống vẫn báo "Lỗi Camera" nhưng giao diện không sập. 
- Nếu AI nhận dạng chậm, UI vẫn đếm giờ và vẽ hình bình thường mà không bị lag chuột. 
Đây là cấu trúc lý tưởng cho một đồ án tốt nghiệp kết hợp phần mềm + phần cứng mang tính ổn định cao.
