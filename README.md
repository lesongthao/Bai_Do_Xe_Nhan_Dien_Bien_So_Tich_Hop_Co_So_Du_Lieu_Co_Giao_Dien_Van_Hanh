# Hệ thống quản lý bãi đỗ xe thông minh ứng dụng xử lý ảnh

Đồ án xây dựng mô hình bãi đỗ xe thông minh có khả năng phát hiện xe, nhận diện biển số, kiểm tra dữ liệu xe vào/ra và điều khiển barie bằng Arduino Uno R3.

## Tác giả

- **Sinh viên thực hiện:** Lê Sông Thao
- **Mã sinh viên:** 0392019545
- **Lớp:** Kỹ thuật Điện tử - Tin học Công nghiệp 2 - K62 - Trường Đại học Giao thông vận tải
- **Giảng viên hướng dẫn:** TS. Nguyễn Thúy Bình
- **Đề tài:** Thiết kế và xây dựng hệ thống quản lý bãi đỗ xe thông minh sử dụng Arduino Uno R3

## Chức năng chính

- Phát hiện xe tại cổng vào và cổng ra bằng cảm biến hồng ngoại LM393.
- Chụp ảnh từ camera USB khi có xe hoặc khi người dùng thao tác thủ công.
- Nhận diện biển số bằng pipeline `YOLOv8n -> OpenCV -> PaddleOCR -> hậu xử lý`.
- Kiểm tra biển số với cơ sở dữ liệu SQLite.
- Điều khiển 2 servo mô phỏng barie cổng vào và cổng ra qua Arduino Uno R3.
- Lưu danh sách xe trong bãi và lịch sử ra/vào.
- Hiển thị camera, kết quả nhận diện, trạng thái bãi xe và nhật ký trên giao diện Tkinter.

## Luồng xử lý tổng quát

```text
LM393 phát hiện xe
        ↓
Arduino Uno R3 đọc cảm biến
        ↓ Serial
Module giao tiếp Arduino
        ↓
Module điều phối hệ thống
        ↓
Module nhận diện biển số + Module quản lý CSDL
        ↓
Quyết định mở/không mở barie
        ↓ Serial
Arduino Uno R3 điều khiển servo
        ↓
Cập nhật SQLite và nhật ký vận hành
```

## Module nhận diện biển số

- **YOLOv8n** chỉ phát hiện vùng biển số, không đọc ký tự.
- **OpenCV** cắt vùng biển số và tạo 3 biến thể ảnh: ảnh gốc, ảnh CLAHE và ảnh Otsu.
- **PaddleOCR** đọc chuỗi ký tự từ từng biến thể ảnh. PaddleOCR dùng mô hình pretrained, không fine-tune lại.
- **Hậu xử lý biển số** chuẩn hóa chuỗi, sửa lỗi OCR theo vị trí ký tự, kiểm tra cấu trúc biển số và chọn ứng viên tốt nhất.

Model chạy chính thức:

```text
mo_hinh/bien_so_yolo.pt
```

## Cấu trúc thư mục

```text
.
├── giao_dien_chinh.py                 # Giao diện chính Tkinter
├── dieu_khien_he_thong.py             # Điều phối camera, AI, CSDL và Arduino
├── nhan_dien_bien_so.py               # Module nhận diện biển số
├── quan_ly_du_lieu.py                 # Module quản lý SQLite
├── giao_tiep_arduino.py               # Giao tiếp Serial với Arduino
├── mo_hinh/
│   └── bien_so_yolo.pt                # Model YOLOv8n dùng khi chạy hệ thống
├── phan_cung_arduino/
│   └── dieu_khien_barie_lm393/
│       └── dieu_khien_barie_lm393.ino # Firmware Arduino
├── dataset_train_yolov8n/             # Metadata dataset train YOLOv8n
├── Kết quả train Yolov8n/             # Kết quả và báo cáo huấn luyện YOLO
└── danh_gia_module_nhan_dien_bien_so/ # Notebook, dataset 200 ảnh và kết quả đánh giá module
```

## Cài đặt

Yêu cầu khuyến nghị:

- Python 3.10 hoặc mới hơn
- Arduino IDE
- Camera USB
- Arduino Uno R3
- 2 cảm biến LM393
- 2 servo SG90
- Nguồn ngoài 5V cho servo

Cài thư viện Python:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Chạy hệ thống

1. Nạp firmware Arduino:

```text
phan_cung_arduino/dieu_khien_barie_lm393/dieu_khien_barie_lm393.ino
```

2. Kết nối camera USB và Arduino với máy tính.

3. Chạy giao diện:

```powershell
python giao_dien_chinh.py
```

4. Trên giao diện, chọn cổng COM của Arduino, kết nối và vận hành ở chế độ tự động hoặc thủ công.

## Cơ sở dữ liệu

Hệ thống sử dụng SQLite. File cơ sở dữ liệu runtime là:

```text
co_so_du_lieu_bai_xe.db
```

Các bảng chính:

- `bien_so_hop_le`: danh sách biển số được phép vào bãi.
- `xe_trong_bai`: danh sách xe đang ở trong bãi.
- `lich_su_ra_vao`: lịch sử xe vào và xe ra.
- `cai_dat`: cấu hình hệ thống, ví dụ sức chứa bãi.

File `.db` là dữ liệu runtime nên được bỏ qua khi push GitHub.

## Kết quả huấn luyện YOLOv8n

Mô hình YOLOv8n được train cho bài toán **một lớp**, trong đó lớp `0` là vùng biển số xe.

Thống kê dataset train:

| Tập dữ liệu | Số ảnh | Số file nhãn | Tổng số bounding box |
|---|---:|---:|---:|
| Train | 5845 | 5845 | 5989 |
| Valid | 1680 | 1680 | 1710 |
| Test | 832 | 832 | 849 |
| Tổng | 8357 | 8357 | 8548 |

Kết quả huấn luyện:

| Chỉ số | Giá trị |
|---|---:|
| Precision | 99.18% |
| Recall | 99.43% |
| mAP50 | 99.48% |
| mAP50-95 | 72.74% |

## Kết quả đánh giá module nhận diện

Module nhận diện được đánh giá trên tập 200 ảnh đã gán nhãn biển số đúng thủ công.

| Chỉ số | Giá trị |
|---|---:|
| Đúng hoàn toàn | 195/200 |
| Accuracy cấp biển số | 97.50% |
| Accuracy cấp ký tự | 98.56% |
| CER | 1.44% |
| YOLO phát hiện vùng biển số | 99.50% |
| OCR đọc được ít nhất một chuỗi | 99.50% |

Các kết quả chi tiết nằm trong:

```text
danh_gia_module_nhan_dien_bien_so/ket_qua_danh_gia_200/
```

## Ghi chú khi đưa lên GitHub

- Raw dataset train YOLOv8n có nhiều ảnh nên đã được đưa vào `.gitignore`.
- Model chạy chính thức nằm tại `mo_hinh/bien_so_yolo.pt`.
- File cơ sở dữ liệu runtime `.db`, cache, file khóa Word và notebook checkpoint không nên commit.
- Nếu cần tái lập huấn luyện YOLO, xem tài liệu trong `Kết quả train Yolov8n/` và `dataset_train_yolov8n/data.yaml`.

## Giấy phép và phạm vi sử dụng

Dự án được xây dựng cho mục đích học tập, nghiên cứu và trình diễn mô hình đồ án tốt nghiệp. Khi sử dụng lại dataset hoặc model, cần kiểm tra giấy phép của nguồn dữ liệu tương ứng.
