# Phân Tích Chuyên Sâu: Module AI Nhận Diện Biển Số (`nhan_dien_bien_so.py`)

Module `nhan_dien_bien_so.py` là "trái tim" của hệ thống. Nó không chỉ đơn thuần là gọi thư viện AI, mà là một **Pipeline 5 bước** được thiết kế tinh vi để khắc phục các nhược điểm thực tế của Camera, điều kiện ánh sáng, và đặc thù biển số Việt Nam.

Dưới đây là phân tích chi tiết về kiến trúc, luồng dữ liệu, và hành trình giải quyết các bài toán khó để đạt được độ chính xác hiện tại.

---

## 1. Kiến Trúc & Luồng Dữ Liệu (Data Flow)

Module nhận đầu vào là một mảng Numpy (ảnh chụp từ Camera) và trả về chuỗi biển số chính xác nhất cùng hình ảnh vùng biển số.

![Pipeline AI Nhận Diện Biển Số](./assets/pipeline_nhan_dien_bien_so.png)
*Lưu ý: Nếu không xem được ảnh, xem mô tả tóm tắt bên dưới.*

**Tóm tắt luồng dữ liệu:**
1. **Input:** Ảnh frame từ camera (Numpy array BGR).
2. **Bước 1:** YOLOv8 custom model phát hiện vùng biển số, cắt các bounding box có độ tin cậy ≥ 0.25.
3. **Bước 2:** Tiền xử lý tạo ra 3 phiên bản ảnh: gốc, CLAHE (cân bằng histogram), Otsu (nhị phân).
4. **Bước 3:** PaddleOCR chạy nhận diện trên cả 3 ảnh.
5. **Bước 4:** Hậu xử lý: nối các dòng bằng dấu *, loại bỏ ký tự đặc biệt, viết hoa, sửa lỗi nhầm lẫn số/chữ theo vị trí.
6. **Bước 5:** Tính điểm cho từng kết quả (OCR confidence + format score), chọn kết quả tốt nhất.
7. **Output:** Trả về biển số cuối cùng và ảnh crop tốt nhất.

---

## 2. Các Khó Khăn Cốt Lõi & Quá Trình Tinh Chỉnh

Quá trình phát triển module này không phải là cắm thư viện vào là chạy được ngay. Dưới đây là các vấn đề hóc búa nhất và cách chúng được giải quyết theo thời gian.

### Khó khăn #1: Khởi động quá chậm (Cold Start Problem)
- **Vấn đề ban đầu:** Lần đầu tiên gọi hàm `nhan_dien()`, hệ thống bị treo từ 4-5 giây. Những lần chụp sau thì chỉ mất 0.3s - 0.5s. Điều này làm trải nghiệm người dùng rất tệ ở lượt xe đầu tiên.
- **Phân tích:** Lần chạy đầu tiên (inference đầu tiên), các framework deep learning (PyTorch/YOLO và PaddlePaddle) phải compile computational graph, khởi tạo CUDA/CPU backend, và load model weights vào memory cache.
- **Giải pháp (Warm-up):** Đưa cơ chế "chạy nháp" (warm-up) vào thẳng hàm `__init__()`. 
  ```python
  # Tạo ảnh ma trận 0 (đen xì)
  _dummy = np.zeros((100, 200, 3), dtype=np.uint8)
  self.yolo.predict(source=_dummy, ...) # Chạy nháp YOLO
  self.ocr.ocr(_dummy, cls=False)       # Chạy nháp PaddleOCR
  ```
- **Kết quả:** Lượt xe thật đầu tiên đi vào hệ thống chỉ mất 0.3s để nhận diện, mượt mà như các lượt sau.

### Khó khăn #2: OCR nhầm lẫn "Chữ" và "Số" (S ↔ 5, O ↔ 0, B ↔ 8)
- **Vấn đề ban đầu:** PaddleOCR là model nhận diện chữ chung (General Text OCR), không hiểu đặc thù biển số. Nó liên tục đọc `51H` thành `S1H` hoặc `51H59531` thành `51H59S3I`.
- **Lựa chọn sai lầm đầu tiên:** Cố gắng huấn luyện lại (fine-tune) PaddleOCR. Quá trình này tốn rất nhiều thời gian gom data và nhãn, nhưng cải thiện không đáng kể vì model gốc đã rất mạnh, lỗi nằm ở font chữ biển số VN quá hẹp.
- **Giải pháp đột phá (Heuristics theo vị trí):** Biển số VN có luật rất chặt chẽ. Hàm `sua_loi_theo_vi_tri_vn()` ra đời.
  - Vị trí 0 và 1: Bắt buộc là **SỐ** (Mã tỉnh). Nếu OCR đọc là `O, I, Z, S, B, G`, ép kiểu về `0, 1, 2, 5, 8, 6`.
  - Vị trí 2: Bắt buộc là **CHỮ** (Seri). Nếu OCR đọc là `0, 1, 2, 5, 8`, ép kiểu về `D, I, Z, S, B`.
  - Phân loại xe máy (2 chữ cái seri) vs Ô tô (1 chữ cái seri) để ép kiểu phần còn lại thành **SỐ**.
- **Kết quả:** Độ chính xác tăng vọt từ ~70% lên >95% đối với các ký tự dễ nhầm lẫn mà không cần train lại model.

### Khó khăn #3: Ánh sáng môi trường thay đổi liên tục
- **Vấn đề ban đầu:** Ban ngày nhận diện cực tốt. Ban đêm (kamera bị lóa đèn pha) hoặc trời mưa, ảnh bị mờ, PaddleOCR trả về chuỗi rác.
- **Quá trình thử nghiệm:** 
  1. Thử dùng ảnh xám (Grayscale): Cải thiện chút ít ban đêm, nhưng mất data màu ban ngày.
  2. Thử dùng Nhị phân Adaptive Threshold: Nhiễu hạt (noise) quá nhiều.
- **Quyết định thiết kế (Sinh 3 phiên bản):** Hàm `_tien_xu_ly()` không cố gắng tạo ra 1 bức ảnh hoàn hảo nhất. Thay vào đó, nó tạo ra **3 bức ảnh đại diện cho 3 trường phái ánh sáng**:
  1. Gốc (cho môi trường lý tưởng)
  2. Cân bằng Histogram CLAHE (kéo lại chi tiết vùng tối)
  3. Nhị phân Otsu (triệt tiêu hoàn toàn màu nền, giữ lại nét chữ đen/trắng, cực tốt khi bị lóa).
- Sau đó, đẩy CẢ 3 ảnh qua PaddleOCR.

### Khó khăn #4: Chọn kết quả nào trong 3 kết quả?
- **Vấn đề:** Khi đưa 3 ảnh qua OCR, ta thu được 3 chuỗi kết quả (VD: `51H59531`, `51H59S31`, `S1H59531`). Làm sao máy biết chuỗi nào đúng nhất? Không thể chỉ dựa vào `Confidence Score` của PaddleOCR vì nhiều khi nó tự tin 99% vào một chuỗi sai.
- **Giải pháp (Hệ thống chấm điểm 2 chiều):** Hàm `_diem_hop_le()` kết hợp với Confidence Score.
  - Tổng điểm = `OCR_Confidence` (từ 0.0 đến 1.0) + `Format_Score` (điểm thưởng nếu khớp định dạng VN).
  - Khớp Regex Ô tô `\d{2}[A-Z]\d{5}` -> Thưởng 1.0
  - Khớp Regex Xe máy `\d{2}[A-Z]{2}\d{5}` -> Thưởng 1.0
- **Kết quả:** Model tự động "bầu chọn" ra kết quả chuẩn format Việt Nam nhất trong số các phiên bản nhiễu.

### Khó khăn #5: Xung đột Multi-threading (Vấn đề chí mạng nhất)
- **Vấn đề:** Ứng dụng Tkinter bị treo cứng (deadlock) bất thình lình khi bấm chụp.
- **Phân tích:** PaddleOCR sử dụng thư viện OpenMP (C++) dưới nền để tối ưu CPU đa nhân. Khi gọi từ Python bằng một Thread mới (sinh ra từ Tkinter), OpenMP cố gắng fork process/thread, đụng độ với cơ chế GIL (Global Interpreter Lock) của Python.
- **Khắc phục:** 
  1. Ép hệ thống vô hiệu hóa đa luồng nội bộ của thư viện C bằng các biến môi trường: `OMP_NUM_THREADS=1`.
  2. Kiến trúc lại Threading: Thay vì tạo Thread mới mỗi lần chụp, tạo 1 **Worker Thread cố định** (`_ai_worker`) duy nhất sống từ lúc mở app đến lúc đóng app. Module `NhanDienBienSo` chỉ được khởi tạo và gọi inference duy nhất bên trong Thread này. Nhận ảnh qua `Queue`.

---

## 3. Tổng Kết Các Thay Đổi (Changelog)

Quá trình tiến hóa của file `nhan_dien_bien_so.py`:

| Phiên bản | Nhược điểm | Tinh chỉnh & Giải pháp đã áp dụng |
| :--- | :--- | :--- |
| **v1.0 (Khởi thủy)** | Chạy YOLO + EasyOCR trên ảnh gốc. Quá chậm (3-4s), sai vặt rất nhiều. | Đổi từ EasyOCR sang PaddleOCR (nhanh & nhẹ hơn). |
| **v1.1 (Tiền xử lý)** | Mù ban đêm hoặc lóa sáng. | Thêm CLAHE và Otsu Thresholding. Đẩy cả 3 ảnh vào OCR. |
| **v1.2 (Heuristic)** | Nhầm O/0, S/5, Z/2. Không biết kết quả nào tốt nhất. | Viết hàm `sua_loi_theo_vi_tri_vn()` và regex `_diem_hop_le()`. Độ chính xác vọt lên. |
| **v1.3 (Ổn định UI)** | Khởi động chậm 5s. Thỉnh thoảng gây đứng UI (Deadlock). | Thêm cơ chế Warm-up `_dummy`. Ép `OMP_NUM_THREADS=1`. |
| **v2.0 (Cuối cùng)** | Nhận diện biển vuông (2 dòng) bị thiếu dòng. | Viết logic gộp bounding box đa dòng, nối bằng ký tự `*`. Hoàn thiện file. |

## 4. Thành Quả Cuối Cùng

Thiết kế hiện tại biến một model AI general-purpose (PaddleOCR) thành một cỗ máy **chuyên biệt cho biển số Việt Nam** mà không cần tốn tài nguyên train lại từ đầu. Thuật toán cân bằng hoàn hảo giữa sức mạnh của Deep Learning (YOLO/OCR) và Rule-based Heuristics (Quy tắc vị trí), kết hợp xử lý song song, giải quyết triệt để vấn đề giật lag UI.
