# Báo Cáo Chi Tiết Quy Trình Nhận Diện Biển Số Xe

## 1. Tổng quan pipeline

Hệ thống nhận diện biển số xe sử dụng pipeline 5 bước:

```
Ảnh đầu vào (từ camera)
  │
  ▼
┌─────────────────────────────────────────────┐
│  Bước 1: Phát hiện vùng biển số (YOLOv8)    │
│  → Xác định tọa độ biển số trong ảnh        │
│  → Cắt vùng biển số ra khỏi ảnh gốc        │
└─────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────┐
│  Bước 2: Tiền xử lý ảnh (Tự viết)          │
│  → Tạo 3 phiên bản: Gốc, CLAHE, Otsu       │
│  → Mỗi phiên bản phục vụ 1 điều kiện khác  │
└─────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────┐
│  Bước 3: Nhận dạng ký tự (PaddleOCR)        │
│  → Phát hiện vùng chữ trong ảnh             │
│  → Nhận dạng chuỗi ký tự                    │
│  → Trả về chuỗi text + confidence           │
└─────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────┐
│  Bước 4: Hậu xử lý theo quy tắc VN (Tự viết)│
│  → Chuẩn hóa biển số (bỏ ký tự đặc biệt)  │
│  → Sửa lỗi nhầm ký tự theo vị trí          │
│  → Chấm điểm mức độ hợp lệ                 │
└─────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────┐
│  Bước 5: Chọn kết quả tốt nhất              │
│  → So sánh tất cả ứng viên từ 3 phiên bản  │
│  → Chọn biển số có điểm (conf + format) cao │
└─────────────────────────────────────────────┘
  │
  ▼
Kết quả: Chuỗi biển số (VD: "51F32488")
```

---

## 2. Chi tiết từng bước

### Bước 1: Phát hiện vùng biển số bằng YOLOv8

**Mục đích:** Tìm và cắt vùng chứa biển số xe trong ảnh chụp từ camera.

**Mô hình sử dụng:**
- YOLOv8n (nano) — phiên bản nhẹ nhất, phù hợp chạy real-time trên CPU
- Mô hình được **tự huấn luyện** trên tập dữ liệu biển số xe Việt Nam (Roboflow)
- File model: `mo_hinh/bien_so_yolo.pt`

**Thông số huấn luyện:**
| Thông số | Giá trị |
|---|---|
| Kiến trúc | YOLOv8n |
| Số epoch | 100 |
| Image size khi train | 640×640 |
| Batch size | 16 |
| mAP50 | 99.48% |
| mAP50-95 | 72.74% |

**Thông số suy luận trong phần mềm:**
| Thông số | Giá trị |
|---|---|
| Image size khi predict | 320×320 |
| Confidence threshold | 0.25 |
| Device | CPU |

**Cách hoạt động:**
1. Đưa toàn bộ ảnh camera vào model YOLO
2. YOLO trả về danh sách bounding box (tọa độ x1, y1, x2, y2) cùng confidence
3. Lọc các box có confidence >= 0.25
4. Cắt (crop) vùng ảnh theo bounding box → thu được ảnh chỉ chứa biển số

**Code tương ứng:** Hàm `_cat_vung_yolo()` (dòng 138-157)

```python
kq = self.yolo.predict(source=anh, conf=0.25, imgsz=320, verbose=False, device="cpu")
# Duyệt qua từng box, cắt vùng biển số
for box in kq[0].boxes:
    x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
    ds.append(anh[y1:y2, x1:x2])
```

**Xử lý fallback:** Nếu YOLO không phát hiện được biển số, hệ thống sẽ dùng toàn bộ ảnh gốc làm đầu vào cho bước tiếp theo.

> **Lưu ý:** Các chỉ số mAP50 và mAP50-95 chỉ đánh giá khả năng phát hiện vùng biển số của YOLOv8, chưa phản ánh khả năng đọc ký tự. Do đó, hệ thống tiếp tục được đánh giá ở cấp độ ký tự và cấp độ biển số sau bước OCR và hậu xử lý.

---

### Bước 2: Tiền xử lý ảnh (Tự viết)

**Mục đích:** Tạo nhiều phiên bản ảnh nhằm tăng khả năng OCR trong nhiều điều kiện ảnh khác nhau. Kết quả thực nghiệm cho thấy ảnh gốc đạt hiệu quả cao nhất trên tập kiểm thử, trong khi cơ chế kết hợp nhiều phiên bản cho kết quả tổng thể tốt nhất.

**3 phiên bản được tạo:**

| # | Phiên bản | Kỹ thuật | Phù hợp khi |
|---|---|---|---|
| 1 | **Ảnh gốc** | Giữ nguyên ảnh màu BGR | Ánh sáng tốt, ảnh rõ nét |
| 2 | **CLAHE** | Cân bằng histogram thích ứng | Thiếu sáng, tương phản thấp |
| 3 | **Otsu** | Nhị phân hóa tự động ngưỡng | Nhiều nhiễu, nền phức tạp |

**Chi tiết kỹ thuật từng phiên bản:**

#### Phiên bản 1 — Ảnh gốc
- Giữ nguyên ảnh màu 3 kênh (BGR)
- Đây là phiên bản cho kết quả tốt nhất trong hầu hết trường hợp (accuracy 99.62% ký tự)

#### Phiên bản 2 — CLAHE (Contrast Limited Adaptive Histogram Equalization)
```python
xam = cv2.cvtColor(anh, cv2.COLOR_BGR2GRAY)          # Chuyển sang ảnh xám
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))  # Tạo bộ CLAHE
ket_qua = clahe.apply(xam)                            # Áp dụng CLAHE
ket_qua = cv2.cvtColor(ket_qua, cv2.COLOR_GRAY2BGR)  # Chuyển lại 3 kênh cho OCR
```
- **clipLimit=2.0**: Giới hạn tương phản, tránh khuếch đại nhiễu
- **tileGridSize=(8,8)**: Chia ảnh thành lưới 8x8 ô, mỗi ô cân bằng histogram riêng
- Hiệu quả khi ảnh tối hoặc tương phản kém

#### Phiên bản 3 — Otsu Thresholding
```python
# Áp CLAHE trước, rồi nhị phân Otsu
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(xam)
_, otsu = cv2.threshold(clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
otsu = cv2.cvtColor(otsu, cv2.COLOR_GRAY2BGR)
```
- Otsu tự động tìm ngưỡng tối ưu để phân tách nền và chữ
- Kết quả là ảnh đen trắng: chữ trắng trên nền đen (hoặc ngược lại)
- Hiệu quả khi ảnh nhiều nhiễu nhưng chữ vẫn rõ ràng

**Code tương ứng:** Hàm `_tien_xu_ly()` (dòng 159-183)

---

### Bước 3: Nhận dạng ký tự bằng PaddleOCR

**Mục đích:** Đọc các ký tự trên ảnh biển số và trả về chuỗi text.

**Thư viện:** PaddleOCR (của Baidu) — thư viện OCR mã nguồn mở, bao gồm các mô-đun phát hiện vùng chữ và nhận dạng ký tự. Trong đề tài, PaddleOCR được sử dụng với cấu hình tiếng Anh (`lang="en"`) và tắt phân loại góc (`use_angle_cls=False`) để nhận dạng chuỗi ký tự trên ảnh biển số.

**Đặc điểm quan trọng:**
- **Không cần phân tách từng ký tự thủ công.** PaddleOCR cho phép nhận dạng trực tiếp vùng văn bản và trả về chuỗi ký tự, do đó trong đề tài không cần tự phân tách từng ký tự thủ công.
- Sử dụng model tiếng Anh vì biển số chỉ chứa chữ cái Latin và số.
- Tắt phân loại góc vì biển số luôn nằm ngang sau khi được YOLO crop.

**Cấu hình:**
```python
self.ocr = PaddleOCR(use_angle_cls=False, lang="en", show_log=False)
```

**Đầu ra của PaddleOCR:** Với mỗi ảnh, PaddleOCR trả về danh sách các dòng text. Mỗi dòng gồm:
- Tọa độ 4 góc của vùng text
- Chuỗi ký tự nhận dạng được
- Confidence score (0.0 - 1.0)

**Ví dụ kết quả:**
```python
# Biển số 2 dòng: "51F" và "32488"
[
  [[[x1,y1],[x2,y2],[x3,y3],[x4,y4]], ("51F", 0.95)],
  [[[x1,y1],[x2,y2],[x3,y3],[x4,y4]], ("32488", 0.98)]
]
```

**Xử lý kết quả OCR:**
1. Thu thập tất cả chuỗi text từ các dòng
2. Tính confidence trung bình
3. Nối tất cả các dòng thành 1 chuỗi liên tục: `"51F" + "32488"` -> `"51F32488"`
4. Tạo danh sách ứng viên gồm: chuỗi nối đầy đủ + từng dòng riêng lẻ

**Code tương ứng:** Trong hàm `nhan_dien()` (dòng 244-268)

---

### Bước 4: Hậu xử lý theo quy tắc biển số Việt Nam (Tự viết)

**Mục đích:** Sửa các lỗi nhầm lẫn ký tự dựa trên cấu trúc biển số xe Việt Nam.

**Đây là phần hoàn toàn tự viết**, không có trong bất kỳ thư viện nào. Gồm 2 hàm chính:

#### 4.1. Chuẩn hóa biển số — `chuan_hoa_bien_so()`

```python
def chuan_hoa_bien_so(bien_so):
    return re.sub(r"[^A-Za-z0-9]", "", (bien_so or "")).upper()
```

- Loại bỏ tất cả ký tự đặc biệt (dấu gạch, dấu chấm, khoảng trắng)
- Chuyển tất cả thành chữ hoa
- Ví dụ: `"51F-324.88"` -> `"51F32488"`

#### 4.2. Sửa lỗi theo vị trí — `sua_loi_theo_vi_tri_vn()`

**Nguyên lý:** Biển số Việt Nam có cấu trúc cố định. Dựa vào vị trí của từng ký tự, ta biết nó **phải là số** hay **phải là chữ**, từ đó sửa lỗi nhầm lẫn.

**Các format biển số VN được hỗ trợ:**

| Loại | Cấu trúc | Ký tự | Ví dụ |
|---|---|---|---|
| Ô tô | 2 số + 1 chữ + 5 số | 8 | 51H59531 |
| Xe máy | 2 số + 1 chữ + 6 số | 9 | 36F504327 |
| Đặc biệt | 2 số + 2 chữ + 5 số | 9 | 80CD12345 |

Các bảng ánh xạ bên dưới được xây dựng theo quy tắc heuristic dựa trên thực nghiệm. Một số ánh xạ có thể tiếp tục được tinh chỉnh khi mở rộng dữ liệu.

**Bảng sửa lỗi chữ -> số** (dùng cho vị trí bắt buộc là số):

| OCR đọc nhầm | Sửa thành | Lý do |
|---|---|---|
| O | 0 | Hình dạng giống nhau |
| Q | 0 | Hình dạng giống nhau |
| I | 1 | Nét dọc giống nhau |
| L | 1 | Nét dọc giống nhau |
| Z | 2 | Hình dạng giống nhau |
| S | 5 | Đường cong giống nhau |
| B | 8 | Hình dạng giống nhau |
| G | 6 | Đường cong giống nhau |

**Bảng sửa lỗi số -> chữ** (dùng cho vị trí bắt buộc là chữ):

| OCR đọc nhầm | Sửa thành | Lý do |
|---|---|---|
| 0 | D | Ánh xạ heuristic cho vị trí seri trong tập thử nghiệm |
| 8 | B | Hình dạng giống nhau |
| 5 | S | Đường cong giống nhau |
| 6 | G | Đường cong giống nhau |

> Các ánh xạ số sang chữ chỉ áp dụng ở vị trí ký tự seri (vị trí thứ 2) và được xây dựng theo thực nghiệm, không áp dụng cho toàn bộ chuỗi biển số.

**Quy trình sửa lỗi theo từng vị trí:**

```
Biển số: [vị trí 0][1][2][3][4][5][6][7]
Ví dụ:     5    1    F    3    2    4    8    8

Vị trí 0,1: BẮT BUỘC là số  -> nếu là chữ -> sửa thành số
Vị trí 2:   BẮT BUỘC là chữ -> nếu là số  -> sửa thành chữ
Vị trí 3+:  BẮT BUỘC là số  -> nếu là chữ -> sửa thành số
```

**Ví dụ thực tế:**
```
OCR đọc:  "S1F3Z488"
           |     |
           S->5  Z->2
Kết quả:  "51F32488"  (đúng)
```

**Code tương ứng:** Hàm `sua_loi_theo_vi_tri_vn()` (dòng 44-86)

#### 4.3. Chấm điểm hợp lệ — `_diem_hop_le()`

Mỗi chuỗi biển số được chấm điểm dựa trên mức độ khớp với format chuẩn VN:

| Điểm | Điều kiện | Ví dụ |
|---|---|---|
| **1.0** | Khớp hoàn hảo format ô tô: `\d{2}[A-Z]\d{5}` | 51H59531 |
| **1.0** | Khớp hoàn hảo format xe máy: `\d{2}[A-Z]\d{6}` | 36F504327 |
| **1.0** | Khớp format đặc biệt: `\d{2}[A-Z]{2}\d{5}` | 80CD12345 |
| **0.9** | Đúng dạng chung: `\d{2}[A-Z]{1,2}\d{4,6}` | — |
| **0.5** | Đúng độ dài 7-10 nhưng không rõ format | — |
| **0.0** | Không khớp gì | — |

**Code tương ứng:** Hàm `_diem_hop_le()` (dòng 185-207)

---

### Bước 5: Chọn kết quả tốt nhất

**Mục đích:** Từ tất cả các ứng viên (3 phiên bản ảnh x nhiều cách ghép text), chọn ra 1 biển số chính xác nhất.

**Công thức tính điểm:**

```
điểm = confidence_OCR + điểm_hợp_lệ_format
```

Trong đó:
- `confidence_OCR`: Giá trị trung bình confidence từ PaddleOCR (0.0 - 1.0)
- `điểm_hợp_lệ_format`: Điểm từ hàm `_diem_hop_le()` (0.0 - 1.0)

**Ví dụ chọn kết quả:**

| Phiên bản ảnh | OCR kết quả | Confidence | Format | Tổng điểm |
|---|---|---|---|---|
| Gốc | 51F32488 | 0.96 | 1.0 | **1.96** (Chọn) |
| CLAHE | 51F3Z488 | 0.91 | 0.5 | 1.41 |
| Otsu | S1F32488 | 0.88 | 0.5 | 1.38 |

**Code tương ứng:** (dòng 272-283)
```python
diem = avg_conf + self._diem_hop_le(bs)
# Cuối cùng chọn biển số có điểm cao nhất
return max(diem_bs.items(), key=lambda x: x[1])[0]
```

---

## 3. Warm-up (Khởi động nóng)

Lần đầu tiên chạy, cả YOLO và PaddleOCR đều mất 4-5 giây để compile/cache model. Để tránh lag khi camera bắt đầu hoạt động, hệ thống chạy **warm-up** với một ảnh trống:

```python
_dummy = np.zeros((100, 200, 3), dtype=np.uint8)
self.yolo.predict(source=_dummy, ...)   # YOLO warm-up
self.ocr.ocr(_dummy, cls=False)          # OCR warm-up
```

Sau warm-up, mỗi lần nhận diện chỉ mất khoảng **0.3-0.6 giây**.

---

## 4. Kết quả đánh giá

Tập kiểm thử gồm 200 ảnh biển số được trích từ bộ dữ liệu biển số xe Việt Nam công khai (Roboflow). Mỗi ảnh được gán nhãn bằng chuỗi biển số đúng, sau đó chuẩn hóa về dạng chỉ gồm chữ cái và chữ số (ví dụ: `51F-324.88` → `51F32488`). Tổng cộng 1600 ký tự.

### Đánh giá theo cấp độ

| Cấp độ đánh giá | Chỉ số sử dụng | Kết quả |
|---|---|---|
| Phát hiện vùng biển số | mAP50 | 99.48% |
| Nhận dạng ký tự | Character Accuracy | 99.69% |
| Nhận dạng toàn biển số | Plate Accuracy | 97.50% |
| Tốc độ xử lý | Thời gian/ảnh | 0.3–0.6 giây |

### So sánh phương pháp tiền xử lý

| Phương pháp | Accuracy ký tự | Accuracy biển số | Đúng/Tổng |
|---|---|---|---|
| Ảnh gốc | 99.62% | 97.00% | 194/200 |
| CLAHE | 98.56% | 96.00% | 192/200 |
| Otsu | 99.19% | 93.50% | 187/200 |
| **Kết hợp chọn tốt nhất** | **99.69%** | **97.50%** | **195/200** |

### So sánh trước và sau hậu xử lý

| Chỉ số | Trước hậu xử lý | Sau hậu xử lý |
|---|---|---|
| Accuracy cấp ký tự | 99.44% | 99.69% |
| Accuracy cấp biển số | 95.00% | 97.50% |
| Số biển đọc đúng | 190 | 195 |

Bước hậu xử lý giúp tăng thêm **5 biển số** nhận diện đúng, chứng minh phần tự viết có giá trị thực tế.

### Ma trận nhầm lẫn cấp độ ký tự

Ma trận nhầm lẫn được xây dựng trên 1600 ký tự của tập kiểm thử. Kết quả cho thấy phần lớn giá trị nằm trên đường chéo chính, chứng tỏ hệ thống nhận dạng đúng hầu hết các ký tự. Các lỗi còn lại chủ yếu gồm:

| Ký tự thật | Nhận nhầm thành | Lý do |
|---|---|---|
| 1 | 2 | Nét gần nhau |
| 2 | 1 | Nét gần nhau |
| 3 | 2 | Đường cong gần nhau |
| 5 | 6 | Đường cong gần nhau |
| 6 | 9 | Nét cong tương đồng, ảnh mờ hoặc thiếu rõ nét |

Do phân bố dữ liệu chưa đồng đều, một số ký tự chữ cái như B, D, E có số mẫu rất ít (1 mẫu mỗi lớp) nên kết quả đánh giá của các lớp này chỉ mang tính tham khảo.

### Tổng kết hệ thống

| Chỉ số | Kết quả |
|---|---|
| Mô hình phát hiện | YOLOv8n (tự huấn luyện, 100 epochs) |
| mAP50 (YOLO) | 99.48% |
| Accuracy cấp ký tự | 99.69% |
| Accuracy cấp biển số | 97.50% |
| Số biển đúng / Tổng | 195 / 200 |
| Thời gian xử lý | ~0.3-0.6 giây/ảnh |

---

## 5. Tóm tắt các phần TỰ VIẾT trong pipeline

| Phần | Tự viết hay thư viện? | Giải thích |
|---|---|---|
| Phát hiện vùng biển số | **Thư viện** (YOLOv8) + **Tự train** model | Kiến trúc YOLO có sẵn, nhưng model được tự huấn luyện trên dữ liệu biển số VN |
| Tiền xử lý ảnh | **Tự viết** | Tự thiết kế pipeline 3 phiên bản (gốc, CLAHE, Otsu) phù hợp điều kiện thực tế |
| Nhận dạng ký tự | **Thư viện** (PaddleOCR) | Sử dụng model có sẵn, không cần train thêm |
| Hậu xử lý VN | **Hoàn toàn tự viết** | Chuẩn hóa, sửa lỗi theo quy tắc biển số VN, chấm điểm format |
| Chọn kết quả tốt nhất | **Tự viết** | Công thức kết hợp confidence + format score |

---

## 6. Kết luận

Module nhận diện biển số được xây dựng theo pipeline gồm phát hiện vùng biển số bằng YOLOv8, cắt vùng biển số, tạo ba phiên bản ảnh tiền xử lý, nhận dạng ký tự bằng PaddleOCR, hậu xử lý theo quy tắc biển số Việt Nam và chọn kết quả tốt nhất dựa trên độ tin cậy OCR kết hợp với điểm hợp lệ định dạng. Trên tập kiểm thử 200 ảnh gồm 1600 ký tự, pipeline kết hợp đạt accuracy cấp ký tự 99.69% và accuracy cấp biển số 97.50%, tương ứng nhận diện đúng hoàn toàn 195/200 biển số. Kết quả này cho thấy module nhận diện có khả năng hoạt động tốt trong điều kiện thử nghiệm và phù hợp để tích hợp vào hệ thống quản lý phương tiện.

---

## 7. Hạn chế

- Tập dữ liệu kiểm thử còn tương đối nhỏ, gồm 200 ảnh.
- Phân bố ký tự chưa đồng đều, một số ký tự chữ cái xuất hiện với số lượng rất ít.
- PaddleOCR được sử dụng như một mô hình có sẵn, chưa được huấn luyện lại riêng cho biển số Việt Nam.
- Kết quả có thể giảm trong điều kiện ảnh quá mờ, biển số bị che khuất hoặc góc chụp quá nghiêng.
- Một số ánh xạ sửa lỗi ký tự (ví dụ: 0 → D) được xây dựng theo kinh nghiệm thực nghiệm, có thể cần tinh chỉnh khi mở rộng dữ liệu.

---

## 8. Hướng phát triển

- Mở rộng tập dữ liệu kiểm thử, bổ sung các trường hợp ảnh khó (mờ, nghiêng, ban đêm).
- Tinh chỉnh hoặc huấn luyện bổ sung mô hình OCR trên dữ liệu biển số Việt Nam để tăng độ chính xác.
- Tiếp tục tối ưu bảng hậu xử lý dựa trên phân tích lỗi thực tế.
- Tích hợp thêm các phương pháp tiền xử lý khác (Adaptive Threshold, Super Resolution).
