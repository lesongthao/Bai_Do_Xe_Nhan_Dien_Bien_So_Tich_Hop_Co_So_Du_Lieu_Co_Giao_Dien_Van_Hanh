# Sơ Đồ Khối & Lưu Đồ Thuật Toán — Hệ Thống Quản Lý Bãi Đỗ Xe Tự Động

## 1. Sơ đồ khối tổng quan hệ thống

```mermaid
graph TB
    subgraph PHAN_CUNG["Phần cứng"]
        CAM["Camera USB"]
        ARD["Arduino Uno"]
        SV1["Servo barie VÀO"]
        SV2["Servo barie RA"]
        CB1["Cảm biến hồng ngoại\nCổng VÀO"]
        CB2["Cảm biến hồng ngoại\nCổng RA"]
    end

    subgraph PHAN_MEM["Phần mềm (Máy tính)"]
        GUI["Giao diện người dùng\n(Tkinter)"]
        CTL["Điều khiển hệ thống\n(Logic chính)"]
        AI["Nhận diện biển số\n(YOLOv8 + PaddleOCR)"]
        DB["Cơ sở dữ liệu\n(SQLite)"]
        SER["Giao tiếp Serial\n(pySerial)"]
    end

    CAM -->|"Ảnh video"| GUI
    GUI <-->|"Sự kiện + Trạng thái"| CTL
    CTL -->|"Ảnh chụp"| AI
    AI -->|"Biển số"| CTL
    CTL <-->|"Đọc/Ghi"| DB
    CTL <-->|"Lệnh/Cảm biến"| SER
    SER <-->|"Serial USB"| ARD
    ARD --> SV1
    ARD --> SV2
    CB1 -->|"Tín hiệu"| ARD
    CB2 -->|"Tín hiệu"| ARD

    style PHAN_CUNG fill:#1a1a2e,stroke:#e94560,color:#fff
    style PHAN_MEM fill:#16213e,stroke:#0f3460,color:#fff
    style AI fill:#533483,stroke:#e94560,color:#fff
```

---

## 2. Sơ đồ khối các module phần mềm

```mermaid
graph LR
    
<truncated 7819 bytes>
ch:** Hệ thống sử dụng 4 luồng (thread) chạy song song để tránh giao diện bị đơ:
> - **Main Thread**: Vòng lặp Tkinter, cập nhật giao diện
> - **Camera Reader**: Đọc ảnh từ camera liên tục
> - **AI Worker**: Chạy nhận diện (nặng nhất, ~0.3-0.6s)
> - **Sensor Worker**: Đọc cảm biến Arduino mỗi 100ms

---

## 9. Sơ đồ cơ sở dữ liệu (ERD)

```mermaid
erDiagram
    BIEN_SO_HOP_LE {
        text bien_so PK "Biển số xe (VD: 51F32488)"
        text chu_xe "Tên chủ xe (tùy chọn)"
        text tao_luc "Thời gian thêm"
    }

    XE_TRONG_BAI {
        text bien_so PK "Biển số xe"
        text vao_luc "Thời gian vào bãi"
    }

    CAI_DAT {
        text khoa PK "Tên cài đặt"
        text gia_tri "Giá trị (VD: suc_chua = 3)"
    }

    BIEN_SO_HOP_LE ||--o{ XE_TRONG_BAI : "Xe hợp lệ mới được vào"
```

---

## 10. Sơ đồ giao thức Serial (Arduino)

```mermaid
sequenceDiagram
    participant PC as Máy tính
    participant ARD as Arduino
    participant SV as Servo
    participant CB as Cảm biến

    Note over PC,ARD: Kết nối Serial 9600 baud

    loop Mỗi 100ms
        CB->>ARD: Đọc tín hiệu hồng ngoại
        ARD->>PC: CAM_BIEN:xe_vao=1,xe_ra=0
    end

    Note over PC: Xe vào → Nhận diện OK
    PC->>ARD: VAO_MO
    ARD->>SV: Servo VÀO quay 90°

    Note over PC: Xe đã qua cảm biến
    PC->>ARD: VAO_DONG
    ARD->>SV: Servo VÀO quay về 0°

    Note over PC: Xe ra
    PC->>ARD: RA_MO
    ARD->>SV: Servo RA quay 90°
    PC->>ARD: RA_DONG
    ARD->>SV: Servo RA quay về 0°
```
