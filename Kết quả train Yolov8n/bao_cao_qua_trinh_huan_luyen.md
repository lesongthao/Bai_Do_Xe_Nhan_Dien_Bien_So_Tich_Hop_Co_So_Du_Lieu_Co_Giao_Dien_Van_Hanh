# Báo cáo quá trình huấn luyện mô hình YOLOv8n

## 1. Mục tiêu huấn luyện

Mục tiêu của bước huấn luyện là tạo ra mô hình YOLOv8n có khả năng phát hiện **vùng biển số** trong ảnh đầu vào. Mô hình này chỉ phục vụ bước định vị vùng biển số để hệ thống cắt ảnh và chuyển sang OCR.

Phạm vi của mô hình:

- đầu vào: ảnh xe hoặc ảnh giao thông có chứa biển số
- đầu ra: bounding box vùng biển số
- không đọc ký tự
- không thay thế OCR
- không thay thế phần hậu xử lý biển số Việt Nam trong module nhận diện

## 2. Dataset huấn luyện

Dataset huấn luyện được lưu tại:

```text
../dataset_train_yolov8n/
```

Thông tin chính:

| Nội dung | Giá trị |
|---|---|
| Bài toán | Phát hiện đối tượng |
| Đối tượng phát hiện | Vùng biển số |
| Số lớp | 1 |
| Định dạng nhãn | YOLO bounding box |
| Chia dữ liệu | train / valid / test |

Vì đây là bài toán phát hiện vùng biển số, toàn bộ annotation của dataset chỉ mô tả khung bao quanh biển số, không mô tả từng ký tự trên biển.

## 3. Môi trường và nền tảng train

Huấn luyện được thực hiện trên Google Colab.

| Thành phần | Giá trị |
|---|---|
| Nền tảng | Google Colab |
| GPU | NVIDIA T4 |
| Kiến trúc | YOLOv8n |
| Trọng số khởi tạo | `yolov8n.pt` |
| Kiểu huấn luyện | Transfer learning |

Lý do chọn Colab:

- có GPU miễn phí đủ dùng cho đồ án
- dễ lưu notebook và artifact
- thuận tiện chạy lại hoặc tinh chỉnh nhanh

## 4. Cấu hình huấn luyện

| Tham số | Giá trị |
|---|---:|
| Mô hình | YOLOv8n |
| Epochs | 100 |
| Image size | 640 |
| Batch size | 16 |
| Optimizer | auto |
| Learning rate ban đầu | 0.01 |
| Patience | 50 |
| AMP | bật |

Các augmentation do Ultralytics quản lý trong quá trình train, phù hợp với bài toán phát hiện một đối tượng nhỏ trong ảnh.

## 5. Quy trình thực hiện

1. Chuẩn bị dataset YOLO trong `dataset_train_yolov8n`.
2. Cài đặt thư viện `ultralytics` trên Google Colab.
3. Khởi tạo mô hình `YOLO('yolov8n.pt')`.
4. Huấn luyện 100 epoch trên GPU T4.
5. Lưu artifact huấn luyện về thư mục:

```text
Kết quả train Yolov8n/NhanDienBienSo_YOLOv8-2/
```

6. Lấy `weights/best.pt` làm mô hình tốt nhất.
7. Đồng bộ mô hình này vào hệ thống dưới tên:

```text
../mo_hinh/bien_so_yolo.pt
```

## 6. Kết quả huấn luyện

Kết quả chính của mô hình YOLOv8n:

| Chỉ số | Giá trị |
|---|---:|
| Precision | 99.18% |
| Recall | 99.43% |
| mAP50 | 99.48% |
| mAP50-95 | 72.74% |

Nhận xét:

- `mAP50 = 99.48%` cho thấy mô hình phát hiện vùng biển số rất tốt trên tập đánh giá của quá trình train.
- `Recall = 99.43%` cho thấy tỷ lệ bỏ sót vùng biển số thấp.
- `mAP50-95 = 72.74%` cho thấy khi siết chặt IoU, độ khít khung bao vẫn còn có thể cải thiện thêm, nhưng đã đủ tốt cho bước crop phục vụ OCR.

## 7. Artifact cần dùng trong đồ án

Các file quan trọng:

| File | Vai trò |
|---|---|
| `NhanDienBienSo_YOLOv8-2/weights/best.pt` | Trọng số tốt nhất sau train |
| `NhanDienBienSo_YOLOv8-2/results.png` | Biểu đồ hội tụ huấn luyện |
| `NhanDienBienSo_YOLOv8-2/BoxPR_curve.png` | Đường cong precision-recall |
| `NhanDienBienSo_YOLOv8-2/confusion_matrix.png` | Ma trận nhầm lẫn |
| `NhanDienBienSo_YOLOv8-2/results.csv` | Bảng log theo epoch |
| `NhanDienBienSo_YOLOv8-2/args.yaml` | Tham số huấn luyện |

File hệ thống thực sự sử dụng khi chạy phần mềm là:

```text
../mo_hinh/bien_so_yolo.pt
```

## 8. Liên hệ với module nhận diện

Trong `nhan_dien_bien_so.py`, YOLO được gọi với vai trò:

- nhận ảnh gốc
- dự đoán bounding box biển số
- cắt vùng biển số
- nếu không có box hợp lệ thì dùng ảnh gốc làm phương án fallback

Sau bước này, hệ thống mới chuyển sang:

- tạo 3 biến thể ảnh
- PaddleOCR đọc chuỗi
- hậu xử lý theo luật biển số Việt Nam
- gộp và chọn ứng viên cuối

Vì vậy, phần huấn luyện YOLO này chỉ là **một tầng** trong toàn bộ module nhận diện biển số.

## 9. Ghi chú về đánh giá

Phần đánh giá trên 200 ảnh hiện nay không thuộc báo cáo huấn luyện YOLO. Nó thuộc đánh giá **module nhận diện biển số hoàn chỉnh** trong thư mục:

```text
../danh_gia_module_nhan_dien_bien_so/
```

Do đó tài liệu này không đưa các số liệu như:

- độ chính xác cấp biển số
- CER
- tỷ lệ OCR đọc được
- tỷ lệ chọn đúng ứng viên

Những chỉ số đó là của pipeline nhận diện hoàn chỉnh, không phải của mô hình YOLO đơn lẻ.
