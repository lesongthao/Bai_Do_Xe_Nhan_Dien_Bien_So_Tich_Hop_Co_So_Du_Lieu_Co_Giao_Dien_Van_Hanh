# Báo Cáo Quá Trình Huấn Luyện Mô Hình

## 1. Huấn luyện mô hình YOLOv8 (Phát hiện vùng biển số)

### 1.1. Mục tiêu

Huấn luyện mô hình YOLOv8 để phát hiện và xác định vị trí vùng biển số xe trong ảnh. Mô hình chỉ cần phát hiện được **vùng chứa biển số** (bounding box), không cần đọc ký tự.

### 1.2. Bộ dữ liệu huấn luyện

| Thông tin | Chi tiết |
|---|---|
| Nguồn | Roboflow Universe (dataset công khai) |
| Tên dataset | Vietnamese License Plate |
| Đường dẫn gốc | `vietnamese-license-plate-1/data.yaml` |
| Nội dung | Ảnh biển số xe Việt Nam (biển trắng, biển vàng, biển xanh) |
| Annotation | Bounding box quanh vùng biển số, định dạng YOLOv8 |
| Số lớp | 1 lớp duy nhất (biển số xe) |

Bộ dữ liệu được Roboflow chia sẵn thành 3 phần:
- **Train set**: ảnh để huấn luyện
- **Validation set**: ảnh để đánh giá trong quá trình train
- **Test set**: ảnh để kiểm thử sau khi train xong

### 1.3. Nền tảng huấn luyện

| Thông tin | Chi tiết |
|---|---|
| Nền tảng | Google Colab |
| GPU | NVIDIA T4 (do Google cung cấp miễn phí) |
| Lý do dùng Colab | Máy cá nhân không có GPU đủ mạnh để train deep learning |
| Thời gian train | Khoảng 3 giờ 13 phút (11599 giây) |
| Lưu kết quả | Google Drive → thư mục `Do_An_Tot_Nghiep/NhanDienBienSo_YOLOv8-2` |

### 1.4. Cấu hình huấn luyện

| Thông số | Giá trị | Giải thích |
|---|---|---|
| Kiến trúc | YOLOv8n (nano) | Phiên bản nhẹ nhất, phù hợp chạy real-time trên CPU |
| Model khởi tạo | `yolov8n.pt` (pretrained) | Dùng trọng số đã train sẵn trên COCO → transfer learning |
| Image size | 640×640 pixel | Kích thước ảnh đầu vào khi train |
| Epochs | 100 | Số lần lặp lại toàn bộ dataset |
| Batch size | 16 | Số ảnh xử lý cùng lúc mỗi bước |
| Optimizer | Auto (SGD) | Tự chọn thuật toán tối ưu |
| Learning rate | 0.01 | Tốc độ học ban đầu |
| Patience | 50 | Dừng sớm nếu 50 epoch không cải thiện |
| AMP | Enabled | Huấn luyện mixed precision để tăng tốc |
| Augmentation | Mosaic, Flip, HSV, Scale, Translate | Tăng cường dữ liệu tự động |

### 1.5. Quy trình thực hiện

```
Bước 1: Tải dataset từ Roboflow về Colab
  ↓
Bước 2: Cài đặt thư viện ultralytics (YOLOv8)
  ↓
Bước 3: Khởi tạo model YOLOv8n (pretrained trên COCO)
  ↓
Bước 4: Train 100 epochs trên GPU T4
  ↓
Bước 5: Kết quả lưu vào Google Drive
  ↓
Bước 6: Tải file best.pt về → đổi tên thành bien_so_yolo.pt
  ↓
Bước 7: Đặt vào thư mục mo_hinh/ trong dự án
```

### 1.6. Code huấn luyện (chạy trên Google Colab)

```python
# Ô 1: Cài đặt thư viện
!pip install ultralytics

# Ô 2: Tải dataset từ Roboflow
!curl -L "https://universe.roboflow.com/ds/..." > roboflow.zip
!unzip roboflow.zip; rm roboflow.zip

# Ô 3: Huấn luyện
from ultralytics import YOLO
model = YOLO('yolov8n.pt')  # Pretrained trên COCO
results = model.train(
    data='vietnamese-license-plate-1/data.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    optimizer='auto',
    lr0=0.01,
    patience=50,
    device=0,  # GPU
    project='/content/drive/MyDrive/Do_An_Tot_Nghiep',
    name='NhanDienBienSo_YOLOv8'
)
```

### 1.7. Kết quả huấn luyện

| Chỉ số | Epoch 1 | Epoch 100 (cuối) |
|---|---|---|
| Precision | 96.01% | 99.18% |
| Recall | 93.74% | 99.43% |
| mAP50 | 97.37% | 99.48% |
| mAP50-95 | 62.85% | 72.74% |
| Train box_loss | 1.233 | 0.912 |
| Train cls_loss | 1.497 | 0.313 |

**Nhận xét:**
- mAP50 đạt **99.48%** cho thấy mô hình phát hiện vùng biển số rất chính xác.
- Loss giảm đều qua 100 epochs, chứng tỏ quá trình train ổn định, không bị overfit.
- mAP50-95 đạt 72.74% là mức hợp lý cho bài toán phát hiện 1 lớp đối tượng.

### 1.8. Sản phẩm thu được

| File | Mô tả | Vị trí trong dự án |
|---|---|---|
| `best.pt` → `bien_so_yolo.pt` | Trọng số model tốt nhất | `mo_hinh/bien_so_yolo.pt` |
| `results.png` | Biểu đồ Loss, mAP qua 100 epochs | `bieu_do_bao_cao/results.png` |
| `confusion_matrix.png` | Ma trận nhầm lẫn YOLO | `bieu_do_bao_cao/confusion_matrix.png` |
| `results.csv` | Số liệu chi tiết từng epoch | `bieu_do_bao_cao/results.csv` |
| `args.yaml` | Toàn bộ cấu hình train | `bieu_do_bao_cao/args.yaml` |

### 1.9. Thông số khi suy luận (inference) trong phần mềm

Khi tích hợp vào phần mềm bãi xe, model chạy với cấu hình nhẹ hơn:

| Thông số | Giá trị | Lý do |
|---|---|---|
| Image size | 320×320 | Giảm kích thước để tăng tốc trên CPU |
| Confidence | 0.25 | Ngưỡng phát hiện |
| Device | CPU | Máy tính tại bãi xe không có GPU |

---

## 2. Mô hình OCR — PaddleOCR (Không huấn luyện)

### 2.1. Lý do không tự huấn luyện OCR

PaddleOCR **không được huấn luyện lại** trong đề tài này. Sử dụng trực tiếp model có sẵn (pretrained) với lý do:

1. **PaddleOCR đã đủ tốt** cho bài toán đọc biển số. Model tiếng Anh (`lang="en"`) nhận dạng được tất cả ký tự Latin (A-Z) và số (0-9) — đúng là bộ ký tự trên biển số Việt Nam.
2. **Huấn luyện OCR rất phức tạp**, đòi hỏi:
   - Hàng chục ngàn ảnh ký tự đã gán nhãn
   - GPU mạnh và thời gian train dài
   - Kiến thức chuyên sâu về kiến trúc CRNN/Transformer
3. **Kết quả thực tế đã rất cao** (99.69% accuracy ký tự), chứng minh model pretrained đã đáp ứng yêu cầu.
4. **Phần tự viết (hậu xử lý)** đã bù đắp được các lỗi nhỏ của OCR, nâng accuracy biển số từ 95.00% lên 97.50%.

### 2.2. Cấu hình PaddleOCR sử dụng

```python
self.ocr = PaddleOCR(use_angle_cls=False, lang="en", show_log=False)
```

| Tham số | Giá trị | Giải thích |
|---|---|---|
| `use_angle_cls` | `False` | Tắt phân loại góc (biển số luôn ngang sau khi YOLO crop) |
| `lang` | `"en"` | Dùng model tiếng Anh (nhận dạng A-Z, 0-9) |
| `show_log` | `False` | Tắt log để không spam console |

### 2.3. Model PaddleOCR được tải tự động

Khi chạy lần đầu, PaddleOCR tự tải model pretrained từ server:
- Model phát hiện vùng text (Text Detection)
- Model nhận dạng ký tự (Text Recognition)

Các model này được cache cục bộ, lần chạy sau không cần tải lại.

---

## 3. Tóm tắt so sánh

| Thành phần | YOLOv8 (phát hiện biển số) | PaddleOCR (đọc ký tự) |
|---|---|---|
| **Có tự train không?** | ✅ Có | ❌ Không |
| **Nền tảng train** | Google Colab (GPU T4) | — |
| **Dataset** | Roboflow (Vietnamese License Plate) | — |
| **Thời gian train** | ~3 giờ 13 phút | — |
| **Model gốc** | YOLOv8n pretrained (COCO) | PaddleOCR pretrained (Eng) |
| **Kết quả** | mAP50 = 99.48% | Accuracy ký tự = 99.69% |
| **File model** | `mo_hinh/bien_so_yolo.pt` | Tự tải + cache |
