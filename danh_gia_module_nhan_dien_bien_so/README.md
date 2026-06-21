# Đánh giá module nhận diện biển số trên 200 ảnh

Thư mục này là nguồn đánh giá chính thức cho module nhận diện biển số của đồ án. Phạm vi đánh giá là module trong `nhan_dien_bien_so.py`, không phải đánh giá riêng YOLO và cũng không phải huấn luyện OCR.

## 1. Dữ liệu đánh giá

| Thành phần | Đường dẫn |
|---|---|
| Ảnh đánh giá | `dataset_danh_gia_200/images/` |
| Nhãn đúng biển số | `dataset_danh_gia_200/labels/nhan_bien_so.csv` |
| Mô tả tập dữ liệu | `dataset_danh_gia_200/mo_ta_dataset.txt` |

Tập đánh giá có 200 ảnh đã được gán nhãn biển số đúng ở cấp chuỗi. Đây là ground truth chính thức dùng để so sánh với kết quả cuối của module.

## 2. Notebook chính

Notebook chính:

```text
danh_gia_module_200_anh.ipynb
```

Notebook này chạy lại pipeline theo đúng logic hiện tại của module:

1. YOLOv8n phát hiện và cắt vùng biển số.
2. PaddleOCR đọc chuỗi trên 3 biến thể ảnh: gốc, CLAHE, Otsu.
3. Hậu xử lý chuẩn hóa, sửa lỗi OCR theo vị trí và kiểm tra cấu trúc.
4. Gộp ứng viên và chọn kết quả cuối theo luật xếp hạng.

## 3. Kết quả chính thức

Kết quả đầu ra nằm trong:

```text
ket_qua_danh_gia_200/
```

Các chỉ số đã chốt:

| Chỉ số | Giá trị |
|---|---:|
| Tổng số ảnh | 200 |
| Đúng hoàn toàn | 195 |
| Sai | 5 |
| Độ chính xác cấp biển số | 97.50% |
| Độ chính xác cấp ký tự | 98.56% |
| CER | 1.44% |
| YOLO tìm được vùng biển số | 99.50% |
| OCR đọc được ít nhất một chuỗi | 99.50% |
| Tạo được phương án biển số | 99.50% |
| Có phương án đúng trong danh sách | 98.00% |
| Chọn đúng khi phương án đúng xuất hiện | 99.49% |

## 4. File kết quả quan trọng

| File | Nội dung |
|---|---|
| `ket_qua_danh_gia_200/du_lieu/tong_hop_chi_so.csv` | Các KPI chính |
| `ket_qua_danh_gia_200/du_lieu/ket_qua_chi_tiet.csv` | Kết quả từng ảnh |
| `ket_qua_danh_gia_200/du_lieu/phan_tich_loi.csv` | Phân tích lỗi theo bản chất |
| `ket_qua_danh_gia_200/du_lieu/danh_gia_chon_ung_vien.csv` | Đánh giá bước chọn ứng viên |
| `ket_qua_danh_gia_200/anh_bao_cao/` | Hình dùng trong báo cáo |

## 5. Nguyên tắc sử dụng

- Không dùng thư mục này để mô tả kết quả train YOLO.
- Không dùng lại các số liệu đánh giá cũ.
- Khi chạy lại notebook, cần kiểm tra lại báo cáo để bảo đảm số liệu `195/200`, `97.50%`, `98.56%` và `CER 1.44%` còn khớp.
