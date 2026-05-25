# BÁO CÁO PHÂN TÍCH CHI TIẾT HỆ THỐNG QUẢN LÝ BÃI ĐỖ XE TỰ ĐỘNG
**Đề tài:** Hệ Thống Bãi Xe Tự Động Ứng Dụng Nhận Diện Biển Số

Tài liệu phân tích toàn diện về kiến trúc, sơ đồ khối, lưu đồ thuật toán và luồng dữ liệu của hệ thống, dựa trên rà soát mã nguồn thực tế.

---

## 1. TỔNG QUAN HỆ THỐNG

### 1.1. Danh sách file mã nguồn

| File | Vai trò | Dòng code | Đặc điểm nổi bật |
|------|---------|-----------|-------------------|
| `giao_dien_chinh.py` | View (UI) | 487 | Tkinter grid, Polling 100ms, Graceful Shutdown |
| `dieu_khien_he_thong.py` | Controller | 448 | Queue đa luồng, điều phối 3 Thread (AI, Sensor, Camera) |
| `nhan_dien_bien_so.py` | AI Service | 284 | YOLOv8 + PaddleOCR + Heuristics sửa lỗi biển VN |
| `quan_ly_du_lieu.py` | Model (DB) | 110 | SQLite có Thread-Safe Lock + DB Cache |
| `giao_tiep_arduino.py` | HW Service | 95 | pySerial, tự quét cổng COM |
| `dieu_khien_barie_lm393.ino` | Firmware (C++) | 150 | Servo, LM393, chống tràn buffer Serial |
| **Tổng** | | **~1.574** | |

### 1.2. Công nghệ sử dụng

| Thành phần | Công nghệ | Chi tiết |
|------------|-----------|----------|
| Ngôn ngữ | Python 3.12 | Đa luồng (threading) |
| Phát hiện biển số | YOLOv8n | Custom-trained, mAP50: 99.48% |
| Nhận dạng ký tự | PaddleOCR | lang='en', use_angle_cls=False |
| Xử lý ảnh | OpenCV | cv2, CLAHE, Otsu |
| Giao diện | Tkinter | Built-in Python |
| CSDL | SQLite3 | Built-in, file `.db` |
| Giao tiếp phần cứng | pySerial | 9600 baud |
| Vi điều khiển | Arduino Uno | 2 servo + 2 cảm biến LM393 |

---

## 2. SƠ ĐỒ KHỐI TỔNG THỂ

```mermaid
graph TD
    subgraph "Tầng Vật Lý (Phần cứng)"
        CAM["Camera USB<br/>(Cổng VÀO)"]
        ARD["Arduino Uno"]
        CB_VAO["Cảm biến LM393<br/>(Cổng VÀO)"]
        CB_RA["Cảm biến LM393<br/>(Cổng RA)"]
        SV_VAO["Servo Barie VÀO"]
        SV_RA["Servo Barie RA"]

        CB_VAO --> ARD
        CB_RA --> ARD
        ARD --> SV_VAO
        ARD --> SV_RA
    end

    subgraph "Tầng Xử Lý Trung Tâm"
        CTRL["Điều Khiển Hệ Thống<br/>(dieu_khien_he_thong.py)"]
        SER["Giao Tiếp Serial<br/>(giao_tiep_arduino.py)"]
        AI["Nhận Diện AI<br/>(nhan_dien_bien_so.py)"]

        CAM -->|"Video Frame"| CTRL
        CTRL <-->|"Lệnh & Trạng thái"| SER
        SER <-->|"UART 9600 baud"| ARD
        CTRL <-->|"Frame / Biển số"| AI
    end

    subgraph "Tầng Lưu Trữ & Giao Diện"
        UI["Giao Diện Tkinter<br/>(giao_dien_chinh.py)"]
        DB[("CSDL SQLite<br/>(quan_ly_du_lieu.py)")]

        CTRL <-->|"Cập nhật UI"| UI
        CTRL <-->|"Query & Caching"| DB
    end
```

---

## 3. KIẾN TRÚC PHẦN MỀM

### 3.1. Kiến trúc 3 tầng (MVC)

```mermaid
graph TB
    subgraph "Tầng Giao Diện (View)"
        V["giao_dien_chinh.py<br/>Tkinter UI<br/>- Hiển thị camera, kết quả nhận diện<br/>- Nút điều khiển barie, chọn chế độ<br/>- Quản lý biển số, log hệ thống"]
    end

    subgraph "Tầng Logic (Controller)"
        C["dieu_khien_he_thong.py<br/>DieuKhienHeThong<br/>- Xử lý cảm biến, quyết định mở/đóng barie<br/>- Quản lý chế độ tự động/thủ công<br/>- Điều phối AI, camera, Arduino, CSDL"]
    end

    subgraph "Tầng Dữ Liệu & Phần Cứng (Model + Service)"
        M1["nhan_dien_bien_so.py<br/>AI Pipeline"]
        M2["quan_ly_du_lieu.py<br/>SQLite Database"]
        M3["giao_tiep_arduino.py<br/>Serial Communication"]
    end

    V <-->|"Gọi hàm / Đọc state"| C
    C <-->|"Gửi ảnh / Trả biển số"| M1
    C <-->|"Đọc / Ghi dữ liệu"| M2
    C <-->|"Gửi lệnh / Đọc cảm biến"| M3
```

**Nguyên tắc thiết kế:** Giao diện **KHÔNG** truy cập trực tiếp AI, CSDL, hay Arduino. Mọi thao tác đều đi qua `DieuKhienHeThong`. Điều này cho phép thay đổi giao diện (Tkinter → Web) mà không ảnh hưởng logic.

### 3.3. Firmware Arduino (`dieu_khien_barie_lm393.ino`)

Firmware viết bằng C++, chạy trên Arduino Uno, đảm nhận điều khiển phần cứng cấp thấp.

**Sơ đồ chân kết nối:**

| Chân Arduino | Thiết bị | Chức năng |
|-------------|----------|----------|
| Pin 9 (PWM) | Servo cổng VÀO | Góc mở: 90°, góc đóng: 0° |
| Pin 10 (PWM) | Servo cổng RA | Góc mở: 90°, góc đóng: 0° |
| Pin 2 (Digital) | Cảm biến LM393 VÀO | INPUT_PULLUP, tác động mức thấp |
| Pin 3 (Digital) | Cảm biến LM393 RA | INPUT_PULLUP, tác động mức thấp |

**Bảng lệnh Serial (nhận từ máy tính):**

| Lệnh | Hành động | Phản hồi |
|------|-----------|----------|
| `VAO_MO` | Servo VÀO quay 90° | `THONG_TIN:VAO_MO_OK` |
| `VAO_DONG` | Servo VÀO quay 0° | `THONG_TIN:VAO_DONG_OK` |
| `RA_MO` | Servo RA quay 90° | `THONG_TIN:RA_MO_OK` |
| `RA_DONG` | Servo RA quay 0° | `THONG_TIN:RA_DONG_OK` |
| `TRANG_THAI` | Đọc cảm biến | `CAM_BIEN:xe_vao=X,xe_ra=X` |
| `PING` | Kiểm tra kết nối | `THONG_TIN:PONG` |

**Lưu đồ vòng lặp `loop()` của Arduino:**

```mermaid
flowchart TD
    START(["loop()"]) --> READ["Đọc lệnh Serial<br/>(nếu có)"]
    READ --> SENSOR["Đọc cảm biến LM393<br/>Pin 2 (VÀO) + Pin 3 (RA)"]
    SENSOR --> CHANGED{"Trạng thái<br/>thay đổi?"}
    CHANGED -- "Có" --> SEND["Gửi ngay:<br/>CAM_BIEN:xe_vao=X,xe_ra=X"]
    CHANGED -- "Không" --> TIMER{"Đã qua<br/>300ms?"}
    TIMER -- "Có" --> SEND
    TIMER -- "Không" --> DELAY["delay(10ms)"]
    SEND --> DELAY
    DELAY --> START
```

**Đặc điểm kỹ thuật quan trọng:**
- **Chu kỳ gửi trạng thái:** Mỗi 300ms hoặc ngay khi trạng thái thay đổi (event-driven)
- **Chống tràn buffer:** Nếu bộ đệm lệnh > 120 ký tự → reset và gửi `RESET_BO_DEM`
- **Cảm biến tác động mức thấp:** LM393 output LOW khi có vật cản → `docCamBien()` đảo logic
- **Khởi động an toàn:** `setup()` đóng cả 2 barie → đọc cảm biến → gửi `KHOI_DONG_OK`

### 3.2. Sơ đồ đa luồng (Multi-threading)

Hệ thống sử dụng **4 luồng** chạy song song để tránh giao diện bị đơ:

```mermaid
graph TB
    subgraph "Main Thread (Tkinter)"
        UI["Vòng lặp mainloop()<br/>poll() mỗi 100ms<br/>Đọc queue, cập nhật UI"]
    end

    subgraph "Camera Thread"
        CAM["cv2.read() liên tục<br/>Resize ảnh<br/>→ latest_frame (30 FPS)"]
    end

    subgraph "AI Worker Thread"
        AI["Đợi ảnh từ q_ai<br/>Chạy YOLO + OCR<br/>→ q_msg (~0.3-0.6s)"]
    end

    subgraph "Sensor Worker Thread"
        SEN["doc_cam_bien() mỗi 100ms<br/>Đọc Serial từ Arduino<br/>→ q_sensor"]
    end

    CAM -->|"latest_frame"| UI
    AI -->|"q_msg (Queue)"| UI
    SEN -->|"q_sensor (Queue)"| UI
    UI -->|"q_ai (Queue)"| AI
```

**Giao tiếp giữa các luồng:** Sử dụng `Queue` (thread-safe), không truy cập UI trực tiếp từ thread phụ.

---

## 4. PIPELINE NHẬN DIỆN BIỂN SỐ

### 4.1. Tổng quan pipeline (5 bước)

```mermaid
flowchart LR
    IMG["Ảnh đầu vào<br/>(Camera 640x480)"] --> YOLO["YOLOv8<br/>Phát hiện vùng<br/>conf=0.25, imgsz=320"]
    YOLO --> PRE["Tiền xử lý<br/>(3 phiên bản ảnh)"]
    PRE --> OCR["PaddleOCR<br/>Đọc ký tự<br/>lang='en'"]
    OCR --> POST["Hậu xử lý VN<br/>Sửa lỗi ký tự"]
    POST --> BEST["Chọn kết quả<br/>tốt nhất"]
    BEST --> OUT["Biển số chuẩn<br/>VD: 51F32488"]
```

### 4.2. Lưu đồ chi tiết giải thuật AI

```mermaid
flowchart TD
    IMG(["Ảnh Đầu Vào"]) --> YOLO{"YOLOv8 cắt<br/>Bounding Box?"}
    YOLO -- "Có biển số" --> CROP["Crop vùng biển số"]
    YOLO -- "Không có" --> RAW["Giữ nguyên toàn bộ ảnh"]

    CROP & RAW --> PRE["Tạo 3 phiên bản:<br/>1. Ảnh gốc (BGR)<br/>2. CLAHE (clipLimit=2.0)<br/>3. Otsu (nhị phân)"]
    PRE --> OCR["PaddleOCR đọc ký tự<br/>→ Danh sách (text, confidence)"]
    OCR --> NORM["Chuẩn hóa: Bỏ ký tự đặc biệt, viết hoa"]
    NORM --> HEU["Sửa lỗi theo vị trí VN:<br/>Vị trí 0-1: bắt buộc SỐ (O→0, S→5)<br/>Vị trí 2: bắt buộc CHỮ (0→D, 8→B)<br/>Vị trí 3+: ưu tiên SỐ"]
    HEU --> SCORE{"Chấm điểm<br/>= OCR conf + Format score"}

    SCORE -- "Điểm cao nhất" --> WIN["Lưu kết quả"]
    SCORE -- "Chưa cao" --> SKIP["Bỏ qua"]

    WIN & SKIP --> LOOP{"Còn phiên bản<br/>ảnh nào không?"}
    LOOP -- "Còn" --> OCR
    LOOP -- "Hết" --> FINAL(["Trả về biển số có điểm Max"])
```

### 4.3. Bảng chấm điểm format biển số VN

| Format score | Regex | Ví dụ |
|-------------|-------|-------|
| 1.0 | `\d{2}[A-Z]\d{5}` | 51H59531 (ô tô) |
| 1.0 | `\d{2}[A-Z]\d{6}` | 36F504327 (xe máy) |
| 1.0 | `\d{2}[A-Z]{2}\d{5}` | 80CD12345 (đặc biệt) |
| 0.9 | `\d{2}[A-Z]{1,2}\d{4,6}` | Biển hợp lệ gần chuẩn |
| 0.5 | `[A-Z0-9]{7,10}` | Đúng độ dài, không rõ format |
| 0.0 | Khác | Không khớp |

---

## 5. LUỒNG DỮ LIỆU

### 5.1. Luồng tự động: Xe VÀO bãi

```mermaid
sequenceDiagram
    autonumber
    participant CB as Cảm biến VÀO
    participant ARD as Arduino
    participant CTRL as Điều Khiển Trung Tâm
    participant AI as Luồng AI Worker
    participant DB as SQLite
    participant UI as Giao Diện

    CB->>ARD: Phát hiện có xe (LOW)
    ARD->>CTRL: Serial: CAM_BIEN:xe_vao=1
    CTRL->>UI: Hiển thị "Đang xử lý AI..."
    CTRL->>AI: Gửi Frame Camera vào q_ai
    Note over AI: YOLO cắt ảnh → 3 phiên bản<br/>→ OCR đọc ký tự → Hậu xử lý VN<br/>→ Chấm điểm → Chọn tốt nhất
    AI->>CTRL: Trả kết quả: "51F32488" + Ảnh
    CTRL->>DB: Kiểm tra: Hợp lệ? Còn chỗ? Chưa trong bãi?
    DB-->>CTRL: Hợp lệ (True)
    CTRL->>DB: INSERT INTO xe_trong_bai
    CTRL->>ARD: Serial: VAO_MO
    ARD-->>CB: Servo quay 90 độ (mở barie)
    CTRL->>UI: Cập nhật: Số chỗ còn lại, Log
    Note over CTRL: Đợi 5 giây hoặc cảm biến hết xe
    CTRL->>ARD: Serial: VAO_DONG (sau kiểm tra an toàn)
```

### 5.2. Luồng tự động: Xe RA khỏi bãi

Cổng RA **không có Camera**, không cần nhận diện biển số. Xóa xe theo FIFO.

```mermaid
sequenceDiagram
    autonumber
    participant CB as Cảm biến RA
    participant ARD as Arduino
    participant CTRL as Điều Khiển Trung Tâm
    participant DB as SQLite

    CB->>ARD: Phát hiện xe (LOW)
    ARD->>CTRL: Serial: CAM_BIEN:xe_ra=1
    CTRL->>ARD: Serial: RA_MO
    Note over CTRL: Bật cờ xe_ra_dang_qua = True
    Note over ARD: Xe chạy qua
    CB->>ARD: Hết xe (HIGH)
    ARD->>CTRL: Serial: CAM_BIEN:xe_ra=0
    Note over CTRL: Chạy auto_close("ra")
    CTRL->>DB: Tìm xe vào sớm nhất → Xóa khỏi xe_trong_bai
    CTRL->>ARD: Serial: RA_DONG
```

### 5.3. Bảng luồng dữ liệu chi tiết

| Nguồn | Dữ liệu | Đích | Giao thức |
|-------|----------|------|-----------|
| Camera → Main | Ảnh BGR (640×480) | `latest_frame` | OpenCV Thread |
| Main → AI Thread | Ảnh chụp | `q_ai` | Queue |
| AI Thread → Main | Biển số + ảnh | `q_msg` | Queue |
| Arduino → Sensor | `CAM_BIEN:xe_vao=1,xe_ra=0` | `q_sensor` | Serial 9600 |
| Main → Arduino | `VAO_MO` / `RA_DONG` ... | Serial TX | pySerial |
| Logic → SQLite | INSERT/DELETE/SELECT | File `.db` | sqlite3 + Lock |

---

## 6. LƯU ĐỒ THUẬT TOÁN

### 6.1. Lưu đồ hoạt động tổng quát

```mermaid
flowchart TD
    START(["Khởi động hệ thống"]) --> LOAD["Tải module AI<br/>(YOLO + OCR + Warm-up)"]
    LOAD --> CONN["Tự động kết nối Arduino<br/>(quét cổng COM)"]
    CONN --> CAMM["Bật camera"]
    CAMM --> WAIT["Đợi sự kiện<br/>(cảm biến / người dùng)"]
    WAIT --> MODE{"Chế độ?"}
    MODE -- "Tự động" --> AUTO["Xử lý tự động<br/>(xe vào: xem 5.1)<br/>(xe ra: xem 5.2)"]
    MODE -- "Thủ công" --> MANUAL["Xử lý thủ công<br/>(người dùng bấm nút)"]
    AUTO --> UPDATE["Cập nhật giao diện"]
    MANUAL --> UPDATE
    UPDATE --> WAIT
```

### 6.2. Lưu đồ xử lý xe VÀO (chế độ tự động)

```mermaid
flowchart TD
    START(["Cảm biến VÀO phát hiện xe"]) --> CHUP["Chụp ảnh từ camera"]
    CHUP --> YOLO["YOLOv8 phát hiện vùng biển số"]
    YOLO --> FOUND{"Tìm thấy<br/>biển số?"}
    FOUND -- "Không" --> ERR1["Thông báo:<br/>Không nhận diện được"]
    FOUND -- "Có" --> AI["Tiền xử lý + PaddleOCR<br/>+ Hậu xử lý VN"]
    AI --> VALID{"Biển số<br/>hợp lệ?"}
    VALID -- "Không" --> ERR2["Xe không hợp lệ"]
    VALID -- "Có" --> EXIST{"Xe đã có<br/>trong bãi?"}
    EXIST -- "Có" --> ERR3["Xe đã có trong bãi"]
    EXIST -- "Không" --> FULL{"Bãi còn<br/>chỗ trống?"}
    FULL -- "Không" --> ERR4["Bãi xe đã đầy"]
    FULL -- "Có" --> SAVE["Lưu xe vào CSDL<br/>+ Mở barie VÀO"]
    SAVE --> CLOSE["Đợi xe qua<br/>→ Đóng barie an toàn"]
```

### 6.3. Lưu đồ đóng barie an toàn (Anti-Pinch)

```mermaid
flowchart TD
    START(["Yêu cầu đóng barie"]) --> CHECK{"Cảm biến tại cổng<br/>còn phát hiện xe?"}
    CHECK -- "Có xe đứng cản" --> DELAY["Set cờ cho_dong = True<br/>Dừng 500ms"]
    DELAY --> CHECK
    CHECK -- "Đã quang đãng" --> CLOSE["Gửi lệnh VAO_DONG / RA_DONG"]
    CLOSE --> END(["Servo đóng barie<br/>An toàn!"])
```

---

## 7. CƠ SỞ DỮ LIỆU

### 7.1. Biểu đồ quan hệ thực thể (ERD)

```mermaid
erDiagram
    bien_so_hop_le {
        TEXT bien_so PK "Biển số xe (VD: 51F32488)"
        TEXT chu_xe "Tên chủ xe (tùy chọn)"
        TEXT tao_luc "Thời gian thêm vào whitelist"
    }

    xe_trong_bai {
        TEXT bien_so PK "Biển số xe đang ở trong bãi"
        TEXT vao_luc "Thời gian vào bãi"
    }

    cai_dat {
        TEXT khoa PK "Tên cài đặt (VD: suc_chua)"
        TEXT gia_tri "Giá trị (VD: 3)"
    }

    bien_so_hop_le ||--o{ xe_trong_bai : "Xe hợp lệ mới được vào"
```

**Đặc tính kỹ thuật:**
- File: `co_so_du_lieu_bai_xe.db`
- Toàn bộ thao tác CSDL được bọc trong `threading.Lock()` để tránh xung đột đa luồng
- Lớp Controller lưu **DB Cache** trong RAM — chỉ đọc ổ cứng khi có thay đổi

### 7.2. Giao thức Serial (Arduino)

```mermaid
sequenceDiagram
    participant PC as Máy tính (Python)
    participant ARD as Arduino Uno
    participant SV as Servo
    participant CB as Cảm biến LM393

    Note over PC,ARD: Kết nối Serial USB 9600 baud

    loop Mỗi 100ms
        CB->>ARD: Đọc tín hiệu hồng ngoại
        ARD->>PC: CAM_BIEN:xe_vao=1,xe_ra=0
    end

    Note over PC: Nhận diện OK → Cho xe vào
    PC->>ARD: VAO_MO
    ARD->>SV: Servo VÀO quay 90°

    Note over PC: Xe đã đi qua cảm biến
    PC->>ARD: VAO_DONG
    ARD->>SV: Servo VÀO quay về 0°
```

---

## 8. TỔNG KẾT

### 8.1. Kết quả đánh giá

| Chỉ số | Giá trị |
|--------|---------|
| Độ chính xác nhận diện biển số (200 ảnh test) | **97.5%** |
| Độ chính xác ký tự (1600 ký tự) | **99.3%** |
| YOLO mAP50 | **99.48%** |
| Thời gian xử lý trung bình | **0.3–0.6 giây** |

### 8.2. Điểm mạnh kiến trúc

1. **Kiến trúc lỏng (Decoupled):** UI và luồng xử lý nặng (AI, Camera) không nằm chung luồng. Dù AI treo hay Camera giật, người dùng vẫn tương tác bình thường.
2. **Phòng ngừa lỗi (Fault-Tolerance):** Xử lý đứt Serial, thiếu thư viện AI (báo lỗi không crash), warm-up AI (tránh lag lượt đầu tiên).
3. **An toàn phần cứng:** Cảm biến đóng vai trò quyết định, barie luôn ưu tiên "an toàn cho phương tiện" hơn "đóng đúng giờ".
4. **Pipeline AI 3 phiên bản:** Tăng độ chính xác trong nhiều điều kiện ánh sáng khác nhau.

### 8.3. Hạn chế và hướng phát triển

| Hạn chế | Hướng phát triển |
|---------|-----------------|
| Chỉ chạy standalone 1 máy | Chuyển sang kiến trúc client-server (Web API) |
| Sử dụng CPU | Tận dụng GPU hoặc edge device |
| Chưa hỗ trợ biển ngoại giao, quân đội | Mở rộng regex và bảng sửa lỗi |
| Cổng RA không nhận diện (FIFO) | Thêm camera cổng RA để đối chiếu |
| SQLite đơn luồng | Nâng cấp PostgreSQL cho đa người dùng |
