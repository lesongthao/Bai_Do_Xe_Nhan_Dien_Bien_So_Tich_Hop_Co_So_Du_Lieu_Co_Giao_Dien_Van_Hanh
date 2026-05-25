# TỔNG QUAN KIẾN TRÚC & NGUYÊN LÝ HOẠT ĐỘNG
**Đề tài:** Hệ Thống Bãi Xe Tự Động Ứng Dụng Nhận Diện Biển Số

Tài liệu này là bản báo cáo rà soát toàn diện nhất về toàn bộ cấu trúc, luồng dữ liệu, cơ sở dữ liệu và thuật toán của hệ thống, dựa trên mã nguồn thực tế trong thư mục dự án.

---

## 1. Kiến Trúc Hệ Thống Tổng Thể

Hệ thống được thiết kế theo mô hình phân tán cục bộ, chia làm 3 lớp (Tầng Vật Lý - Tầng Xử Lý Trung Tâm - Tầng Lưu Trữ/Giao Diện). Mẫu thiết kế phần mềm (Software Design Pattern) được sử dụng là **MVC (Model - View - Controller)** kết hợp **Đa luồng (Multi-threading)**.

### Sơ Đồ Khối Tổng Thể (Block Diagram)

```mermaid
graph TD
    subgraph "Tầng Vật Lý (Hardware)"
        CAM["📷 Camera USB (Cổng VÀO)"]
        ARD["🔧 Arduino Uno/Nano"]
        CB_VAO["🔴 Cảm biến LM393 (VÀO)"]
        CB_RA["🔴 Cảm biến LM393 (RA)"]
        SV_VAO["⚙️ Servo Barie (VÀO)"]
        SV_RA["⚙️ Servo Barie (RA)"]
        
        CB_VAO --> ARD
        CB_RA --> ARD
        ARD --> SV_VAO
        ARD --> SV_RA
    end

    subgraph "Tầng Xử Lý Trung Tâm (Controller & Services)"
        CTRL["⚙️ Điều Khiển Trunng Tâm<br/>(dieu_khien_he_thong.py)"]
        SER["🔌 Cổng Giao Tiếp Serial<br/>(giao_tiep_arduino.py)"]
        AI["🤖 Khối Nhận Diện AI<br/>(nhan_dien_bien_so.py)"]
        
        CAM -->|"Video Frame (~30fps)"| CTRL
        CTRL <-->|"Lệnh & Trạng thái"| SER
        SER <-->|"UART 9600 baud"| ARD
        CTRL <-->|"Frame / Biển Số"| AI
    end

    subgraph "Tầng Lưu Trữ & Giao Diện (Model & View)"
        UI["💻 Giao Diện Người Dùng Tkinter<br/>(giao_dien_chinh.py)"]
        DB[("🗄️ CSDL SQLite<br/>(quan_ly_du_lieu.py)")]
        
        CTRL <-->|"Cập nhật UI 200ms/lần"| UI
        CTRL <-->|"Query & Caching"| DB
    end
```

---

## 2. Phân Tích Cơ Sở Dữ Liệu (Database Schema)

Hệ thống sử dụng **SQLite** lưu tại file `co_so_du_lieu_bai_xe.db` để đảm bảo tính gọn nhẹ, không cần cài đặt SQL Server.

### Biểu Đồ Quan Hệ Thực Thể (ERD)

```mermaid
erDiagram
    cai_dat {
        TEXT khoa PK "Ví dụ: suc_chua_toi_da"
        TEXT gia_tri "Ví dụ: 3"
    }
    
    bien_so_hop_le {
        TEXT bien_so PK "Biển số (VD: 51H59531)"
        TEXT chu_xe "Tên chủ xe"
        TEXT tao_luc "Thời gian thêm vào whitelist"
    }
    
    xe_trong_bai {
        TEXT bien_so PK "Biển số xe đang ở trong bãi"
        TEXT vao_luc "Thời gian quẹt thẻ/nhận diện vào"
    }
```
**Đặc tính kỹ thuật DB:**
- CSDL được quản lý bởi file `quan_ly_du_lieu.py`. 
- Để tránh nghẽn cổ chai (bottleneck) khi UI và AI cùng truy xuất, toàn bộ thao tác CSDL được bọc trong `threading.Lock()`.
- Lớp Controller lưu một biến cờ (flag) gọi là **DB Cache**. Nếu không có xe nào chạy ra/vào, hệ thống sẽ trả về data từ RAM thay vì đọc ổ cứng, giúp phần mềm chạy siêu nhẹ.

---

## 3. Cấu Trúc Mã Nguồn (Directory Structure)

Dự án gồm **5 file Python** và **1 file C++ (Arduino)**:

| File | Vai Trò | LoC (Dòng lệnh) | Đặc điểm nổi bật |
|------|---------|-----------------|------------------|
| `giao_dien_chinh.py` | View (UI) | ~493 | Tkinter grid, Polling 200ms, Graceful Shutdown. |
| `dieu_khien_he_thong.py` | Controller | ~448 | Quản lý Queue, điều phối 3 Thread (AI, Sensor, Camera), Auto-close Logic. |
| `nhan_dien_bien_so.py` | AI Service | ~305 | YOLOv8 + PaddleOCR + Heuristics sửa lỗi biển VN. |
| `quan_ly_du_lieu.py` | Model (DB) | ~110 | Thao tác SQLite có Thread-Safe Lock. |
| `giao_tiep_arduino.py` | HW Service | ~95 | PySerial, tự quét cổng COM, chống nhiễu đứt cáp (RLock). |
| `dieu_khien_barie...ino` | Firmware | ~150 | Chống dội cảm biến LM393 (Debounce), điều khiển góc Servo. |

---

## 4. Nguyên Lý Hoạt Động & Luồng Dữ Liệu (Data Flow)

### 4.1 Luồng Tự Động: Xe VÀO bãi

Đây là luồng phức tạp nhất, liên quan đến cả Phần cứng, Nhận diện hình ảnh và CSDL.

```mermaid
sequenceDiagram
    autonumber
    participant CB as Cảm biến VÀO
    participant ARD as Arduino
    participant CTRL as Điều Khiển Trung Tâm
    participant AI as Luồng AI (Worker)
    participant DB as SQLite
    participant UI as Giao Diện

    CB->>ARD: Phát hiện có xe chắn ngang (LOW)
    ARD->>CTRL: Serial: CAM_BIEN:xe_vao=1
    CTRL->>UI: Hiển thị "Đang xử lý AI..."
    CTRL->>AI: Gửi Frame Camera mới nhất vào q_ai
    Note over AI: YOLO Cắt ảnh -> OCR -> Chấm điểm
    AI->>CTRL: Trả kết quả: Biển số "51H59531" + Ảnh
    CTRL->>DB: Kiểm tra: Biển hợp lệ? Còn chỗ trống? Chưa trong bãi?
    DB-->>CTRL: Hợp lệ (True)
    CTRL->>DB: Ghi dữ liệu: Thêm vào bảng `xe_trong_bai`
    CTRL->>ARD: Serial: VAO_MO
    ARD-->>CB: Servo quay 90 độ
    CTRL->>UI: Cập nhật: Số chỗ còn lại, Log sự kiện
    Note over CTRL: Bắt đầu tính giờ 5 giây (Auto Close)
    CTRL->>ARD: Serial: VAO_DONG (Nếu cảm biến hết xe)
```

### 4.2 Luồng Tự Động: Xe RA khỏi bãi

Cổng ra không có Camera, chỉ dùng Cảm biến để mở cửa (do hệ thống quản lý một chiều số lượng).

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
    Note over CTRL: Bật cờ `xe_ra_dang_qua = True`
    Note over ARD: Xe chạy qua vạch
    CB->>ARD: Hết xe (HIGH)
    ARD->>CTRL: Serial: CAM_BIEN:xe_ra=0
    Note over CTRL: Chạy logic `auto_close("ra")`
    CTRL->>DB: Tìm xe vào sớm nhất -> Xóa khỏi `xe_trong_bai`
    CTRL->>ARD: Serial: RA_DONG
```

---

## 5. Lưu Đồ Thuật Toán Trọng Tâm

### 5.1 Lưu Đồ Kỹ Thuật Đóng Barie An Toàn (Anti-Pinch)
Hệ thống KHÔNG đóng barie mù quáng sau 5 giây. Nó có cơ chế chống kẹp xe cực kỳ chặt chẽ:

```mermaid
flowchart TD
    START([Bắt đầu đóng Barie]) --> CHECK{"Kiểm tra Cảm biến tương ứng<br/>(VÀO hoặc RA) == 1?"}
    CHECK -- "Có xe đứng cản" --> DELAY["Set cờ `cho_dong = True`<br/>Dừng 500ms"]
    DELAY --> CHECK
    CHECK -- "Đã quang đãng" --> CLOSE["Gửi lệnh `VAO_DONG` / `RA_DONG`"]
    CLOSE --> END([Kết thúc])
```

### 5.2 Lưu Đồ Giải Thuật Nhận Diện AI
Module `nhan_dien_bien_so.py` được thiết kế để không bỏ lỡ bất kỳ dữ liệu nào ngay cả trong môi trường thiếu sáng.

```mermaid
flowchart TD
    IMG([Ảnh Đầu Vào]) --> YOLO{"YOLOv8 cắt Bounding Box"}
    YOLO -- "Có biển số" --> CROP["Crop mảng ảnh"]
    YOLO -- "Không có" --> RAW["Giữ nguyên toàn bộ ảnh"]
    
    CROP & RAW --> PRE["Tạo 3 bộ lọc: Gốc, CLAHE, Otsu"]
    PRE --> OCR["PaddleOCR trích xuất Text"]
    OCR --> HEU["Áp dụng Regex & Luật thay thế ký tự<br/>(S->5, O->0...)"]
    HEU --> SCORE{"So sánh tổng điểm"}
    
    SCORE -- "Cao nhất" --> WIN["Lưu Kết Quả"]
    SCORE -- "Chưa cao" --> SKIP["Bỏ qua"]
    
    WIN & SKIP --> LOOP{"Còn dòng Text nào không?"}
    LOOP -- "Còn" --> HEU
    LOOP -- "Hết" --> FINAL([Trả về chuỗi có điểm Max])
```

---

## 6. Tổng Kết Kiến Trúc

Dự án này là một hệ thống mang tính chuyên nghiệp nhờ 3 đặc điểm:
1. **Decoupled Architecture (Kiến trúc lỏng):** Giao diện (UI) và Luồng xử lý nặng (AI, Camera) không nằm chung luồng. Dù AI có bị treo hoặc Camera bị giật, người dùng vẫn bấm được các nút trên màn hình bình thường.
2. **Phòng Ngừa Lỗi (Fault-Tolerance):** Code xử lý đứt dây Serial (cắm lại nhận luôn), lỗi thư viện AI (Graceful degradation - báo thiếu thư viện chứ không crash), và cơ chế Warm-up AI (Chống lag lượt xe đầu tiên).
3. **Logic Phần Cứng An Toàn:** Cảm biến đóng vai trò quyết định, barie luôn ưu tiên "an toàn cho phương tiện" hơn là "đóng đúng giờ".
