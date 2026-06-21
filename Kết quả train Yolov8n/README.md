# Huấn luyện YOLOv8 phát hiện vùng biển số

Thư mục này gom riêng tài liệu và artifact của phần huấn luyện YOLOv8n. Phạm vi của nó chỉ là bài toán phát hiện **vùng biển số** bằng bounding box, không bao gồm OCR và không bao gồm phần đánh giá module nhận diện trên 200 ảnh.

## 1. Nội dung chính

| Thành phần | Đường dẫn |
|---|---|
| Báo cáo quá trình huấn luyện | `bao_cao_qua_trinh_huan_luyen.md` |
| Hướng dẫn train trên Google Colab | `huong_dan_train_yolo.md` |
| Notebook train | `Train_YOLOv8_Bien_So_VN.ipynb` |
| Artifact huấn luyện | `NhanDienBienSo_YOLOv8-2/` |

## 2. Mục tiêu của mô hình

Mô hình YOLOv8n trong đồ án chỉ làm một việc:

- nhận ảnh đầu vào
- phát hiện vùng chứa biển số
- trả về bounding box để hệ thống cắt ảnh và chuyển sang PaddleOCR

Mô hình này **không đọc ký tự**, **không nhận dạng từng chữ số**, và **không thay thế phần hậu xử lý biển số** trong `nhan_dien_bien_so.py`.

## 3. Dataset train

Dataset train nằm riêng tại:

```text
../dataset_train_yolov8n/
```

Đặc điểm:

- định dạng nhãn: YOLO bounding box
- số lớp: 1 lớp duy nhất là vùng biển số
- chia sẵn train / valid / test

## 4. Kết quả huấn luyện đã chốt

| Chỉ số | Giá trị |
|---|---:|
| Precision | 99.18% |
| Recall | 99.43% |
| mAP50 | 99.48% |
| mAP50-95 | 72.74% |
| Epochs | 100 |
| Image size | 640 |
| Batch size | 16 |

## 5. Artifact quan trọng

Trong thư mục `NhanDienBienSo_YOLOv8-2/`:

- `weights/best.pt`: trọng số tốt nhất sau huấn luyện
- `results.png`: biểu đồ hội tụ
- `BoxPR_curve.png`: đường cong precision-recall
- `confusion_matrix.png`: ma trận nhầm lẫn
- `results.csv`: log chỉ số theo epoch
- `args.yaml`: tham số train

Trong hệ thống chạy thật, file `best.pt` được dùng làm nguồn để tạo:

```text
../mo_hinh/bien_so_yolo.pt
```

## 6. Ghi chú đồng bộ với hệ thống

- Chỉ số trong thư mục này là chỉ số của **mô hình YOLO phát hiện vùng biển số**.
- Phần đánh giá **module nhận diện biển số hoàn chỉnh** được đặt riêng trong:

```text
../danh_gia_module_nhan_dien_bien_so/
```

- Không dùng số liệu đánh giá module 200 ảnh để mô tả lại phần huấn luyện YOLO.
