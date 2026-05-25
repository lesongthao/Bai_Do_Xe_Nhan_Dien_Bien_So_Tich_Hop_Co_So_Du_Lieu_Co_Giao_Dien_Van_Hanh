# Hướng Dẫn Học Code — Chia Nhỏ Để Hiểu

## Quy tắc #1: KHÔNG đọc từ trên xuống!

Đọc theo **nhóm chức năng**. Cả 2 file chỉ có **7 nhóm**, mỗi nhóm 3-8 hàm.

---

## `dieu_khien_he_thong.py` — 4 nhóm

### Nhóm 1: Khởi tạo & Trạng thái (dòng 21-105)
**Hiểu đơn giản:** Khai báo biến + lấy trạng thái

| Hàm | 1 câu giải thích |
|-----|------------------|
| `__init__()` | Khai báo tất cả biến: camera, barie, cảm biến, queue |
| `get_ui_state()` | Đóng gói toàn bộ trạng thái thành 1 dict cho UI đọc |
| `notify()` | Đánh dấu "có thay đổi, cần refresh UI" |
| `start()` / `stop()` | Bật/tắt hệ thống |

### Nhóm 2: Camera + AI (dòng 173-280)
**Hiểu đơn giản:** Bật camera → chụp → gửi vào queue → AI xử lý → trả kết quả

```
bat_cam() → _cam_reader() chạy ngầm → latest_frame
     ↓
chup() → q_ai.put(frame) → _ai_worker() nhận → nhan_dien() → q_msg.put(kết quả)
     ↓
poll_messages() → _handle_ai_result() → cho xe vào hoặc từ chối
```

| Hàm | 1 câu giải thích |
|-----|------------------|
| `bat_cam()` | Mở camera, tạo thread đọc liên tục |
| `_cam_reader()` | Thread ngầm: đọc frame 30fps |
| `chup()` | Copy frame → đẩy vào queue AI |
| `_ai_worker()` | Thread ngầm: lấy frame từ queue → chạy YOLO+OCR → trả kết quả |
| `_handle_ai_result()` | Nhận kết quả AI → kiểm tra whitelist → cho vào / từ chối |
| `_cho_xe_vao()` | Ghi DB + mở barie + hẹn 5s đóng |
| `_reset_ai()` | Reset flag về idle (dùng khi xong / lỗi / timeout) |

### Nhóm 3: Arduino + Cảm biến (dòng 290-340)
**Hiểu đơn giản:** Đọc cảm biến → phát hiện xe → trigger hành động

```
_sensor_worker() → đọc cảm biến mỗi 100ms → q_sensor
     ↓
poll() → _xu_ly_cam_bien() → xe_vao=1? → chup()
                             → xe_ra=1? → mở barie ra
                             → xe đã qua? → đóng barie
```

| Hàm | 1 câu giải thích |
|-----|------------------|
| `_auto_connect_arduino()` | Tự dò cổng COM, kết nối |
| `_sensor_worker()` | Thread ngầm: đọc cảm biến 10 lần/giây |
| `_xu_ly_cam_bien()` | Phát hiện xe vào/ra, trigger hành động tương ứng |
| `auto_close()` | Đóng barie an toàn (chờ xe đi qua mới đóng) |

### Nhóm 4: Quản lý biển số (dòng 123-138)
**Đơn giản nhất:** Thêm/xóa whitelist

| Hàm | 1 câu giải thích |
|-----|------------------|
| `add_plate()` | Thêm biển số vào whitelist |
| `delete_plate()` | Xóa biển số khỏi whitelist |

---

## `giao_dien_chinh.py` — 3 nhóm

### Nhóm 5: Xây UI (dòng 79-299)
**Hiểu đơn giản:** Vẽ giao diện bằng Tkinter

Bạn KHÔNG CẦN thuộc phần này. Chỉ cần biết UI có:
- Camera preview + nút Bật/Tắt/Chụp
- Ảnh biển số + text kết quả
- Trạng thái CÒN CHỖ / HẾT CHỖ
- Nút chế độ + điều khiển barie
- Quản lý whitelist + Nhật ký

### Nhóm 6: Refresh UI (dòng 405-448)
**Hiểu đơn giản:** Lấy state từ controller → cập nhật UI

| Hàm | 1 câu giải thích |
|-----|------------------|
| `_refresh_ui()` | Gọi `controller.get_ui_state()` → cập nhật tất cả label/button |
| `_refresh_camera_preview()` | Chuyển numpy array → ảnh Tkinter |
| `_on_plate_result()` | Hiển thị ảnh + text biển số nhận diện |

### Nhóm 7: Vòng lặp chính (dòng 485-493)
**Đơn giản nhất:**

```python
def _poll(self):           # Chạy mỗi 200ms
    controller.poll_messages()  # Xử lý kết quả AI
    controller.poll()           # Xử lý cảm biến
    root.after(200, _poll)      # Lặp lại
```

---

## Tóm tắt: Chỉ cần nhớ luồng chính

```
Cảm biến phát hiện xe → chup() → AI nhận diện → kiểm tra whitelist → mở barie → 5s sau đóng
```

**Thế thôi!** Tất cả 940 dòng code chỉ phục vụ luồng này.
