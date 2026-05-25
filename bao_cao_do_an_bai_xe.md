# BÁO CÁO ĐỒ ÁN

## 3.1. HỆ THỐNG BÃI ĐỖ XE TỰ ĐỘNG ỨNG DỤNG NHẬN DIỆN BIỂN SỐ

---

## 3.2. TÓM TẮT

Báo cáo trình bày quá trình thiết kế và xây dựng mô hình hệ thống bãi đỗ xe tự động ứng dụng nhận diện biển số. Hệ thống sử dụng hai camera (thiết bị thu hình) cho cổng vào và cổng ra, mô hình YOLOv8 (You Only Look Once version 8 - mô hình phát hiện đối tượng phiên bản 8) để phát hiện vùng biển số, PaddleOCR (Paddle Optical Character Recognition - bộ nhận dạng ký tự quang học) để nhận dạng ký tự, thuật toán hậu xử lý theo định dạng biển số Việt Nam để chọn kết quả cuối, SQLite (Structured Query Language Lite - hệ cơ sở dữ liệu nhúng dạng file) để quản lý dữ liệu và Arduino (bo mạch vi điều khiển) để điều khiển hai servo (động cơ điều khiển theo góc quay) barrier (thanh chắn/barie) thông qua tín hiệu cảm biến LM393 (module cảm biến vật cản dùng IC so sánh LM393).

Nội dung báo cáo được trình bày theo hướng từ tổng quát đến chi tiết: trước hết xác định bài toán và sơ đồ khối tổng quan, sau đó phân tích cơ sở lý thuyết của từng khối, tiếp theo là thiết kế hệ thống theo luồng dữ liệu và luồng điều khiển, cuối cùng đánh giá kết quả thực nghiệm. Trọng tâm kỹ thuật của đề tài là khối nhận diện biển số và khối điều khiển phần cứng barrier (thanh chắn/barie) an toàn.

---

## 3.3. MỤC LỤC

- [CHƯƠNG 1. TỔNG QUAN ĐỀ TÀI](#chương-1-tổng-quan-đề-tài)
- [CHƯƠNG 2. CƠ SỞ LÝ THUYẾT](#chương-2-cơ-sở-lý-thuyết)
- [CHƯƠNG 3. THIẾT KẾ HỆ THỐNG](#chương-3-thiết-kế-hệ-thống)

---

## 3.4. DANH MỤC HÌNH

| Hình | Nội dung |
|---|---|
| Hình 1.1 | Sơ đồ khối tổng quan hệ thống |
| Hình 1.2 | Minh họa bố trí mô hình hai cổng |
| Hình 2.1 | Pipeline nhận diện biển số |
| Hình 2.2 | Quy trình huấn luyện YOLOv8 (You Only Look Once version 8 - mô hình phát hiện đối tượng phiên bản 8) phát hiện biển số |
| Hình 2.3 | Chi tiết OCR (Optical Character Recognition - nhận dạng ký tự quang học) và hậu xử lý biển số Việt Nam |
| Hình 2.4 | Cơ chế an toàn khi đóng barrier (thanh chắn/barie) |
| Hình 2.5 | Giao thức Serial (giao tiếp nối tiếp) giữa máy tính và Arduino (bo mạch vi điều khiển) |
| Hình 2.6 | Sơ đồ cơ sở dữ liệu |
| Hình 3.1 | Sơ đồ module phần mềm |
| Hình 3.2 | Luồng dữ liệu trong hệ thống |
| Hình 3.3 | Lưu đồ xử lý xe vào |
| Hình 3.4 | Lưu đồ xử lý xe ra |
| Hình 3.5 | Sơ đồ đấu nối phần cứng |
| Hình 3.6 | Cơ chế đa luồng trong hệ thống |
| Hình 4.1 | So sánh tiền xử lý ảnh |
| Hình 4.2 | So sánh trước và sau hậu xử lý |

---

## 3.5. DANH MỤC BẢNG

| Bảng | Nội dung |
|---|---|
| Bảng 2.1 | Giao thức lệnh gửi từ máy tính xuống Arduino (bo mạch vi điều khiển) |
| Bảng 3.1 | Vai trò các bước trong khối nhận diện biển số |
| Bảng 3.2 | Thiết kế các bảng dữ liệu chính |
| Bảng 4.1 | Kết quả huấn luyện YOLOv8 (You Only Look Once version 8 - mô hình phát hiện đối tượng phiên bản 8) |
| Bảng 4.2 | So sánh phương pháp tiền xử lý ảnh |
| Bảng 4.3 | So sánh trước và sau hậu xử lý |

---

## 3.6. DANH MỤC TỪ TIẾNG ANH VÀ TỪ VIẾT TẮT

| Thuật ngữ | Viết đầy đủ / Diễn giải | Nghĩa sử dụng trong báo cáo |
|---|---|---|
| AI | Artificial Intelligence | Trí tuệ nhân tạo |
| Arduino | Tên nền tảng bo mạch vi điều khiển | Bo mạch điều khiển phần cứng |
| Barrier | Barrier gate | Thanh chắn/barie đóng mở cổng |
| Camera | Camera | Thiết bị thu hình |
| COM | Communication Port | Cổng giao tiếp nối tiếp trên máy tính |
| CPU | Central Processing Unit | Bộ xử lý trung tâm |
| GPU | Graphics Processing Unit | Bộ xử lý đồ họa |
| USB | Universal Serial Bus | Chuẩn kết nối giữa máy tính và thiết bị |
| Serial | Serial Communication | Giao tiếp nối tiếp |
| Servo | Servo motor | Động cơ điều khiển theo góc quay |
| PWM | Pulse Width Modulation | Điều chế độ rộng xung để điều khiển servo |
| DO | Digital Output | Ngõ ra số của cảm biến |
| VCC | Voltage Common Collector | Chân cấp nguồn dương cho module |
| GND | Ground | Chân mass/đất chung của mạch |
| LM393 | Tên IC so sánh dùng trong module cảm biến | Cảm biến vật cản hồng ngoại dùng module LM393 |
| YOLO | You Only Look Once | Mô hình phát hiện đối tượng một giai đoạn |
| YOLOv8 | You Only Look Once version 8 | Phiên bản YOLO dùng để phát hiện vùng biển số |
| YOLOv8n | YOLOv8 nano | Biến thể nhỏ, nhẹ của YOLOv8 |
| OCR | Optical Character Recognition | Nhận dạng ký tự quang học |
| PaddleOCR | Paddle Optical Character Recognition | Bộ OCR dùng để nhận dạng ký tự biển số |
| SQLite | Structured Query Language Lite | Hệ cơ sở dữ liệu nhúng dạng file |
| SQL | Structured Query Language | Ngôn ngữ truy vấn cơ sở dữ liệu |
| Python | Python programming language | Ngôn ngữ lập trình dùng xây dựng phần mềm |
| Tkinter | Tk interface | Thư viện giao diện đồ họa của Python |
| OpenCV | Open Source Computer Vision Library | Thư viện xử lý ảnh/máy tính thị giác |
| BGR | Blue - Green - Red | Thứ tự kênh màu xanh dương, xanh lá, đỏ trong OpenCV |
| CLAHE | Contrast Limited Adaptive Histogram Equalization | Cân bằng lược đồ xám thích nghi có giới hạn tương phản |
| Otsu | Otsu thresholding | Phương pháp tự động chọn ngưỡng nhị phân ảnh |
| Dataset | Dataset | Bộ dữ liệu ảnh dùng để huấn luyện/đánh giá |
| Bounding box / bbox | Bounding box | Hộp giới hạn bao quanh đối tượng cần phát hiện |
| Frame | Video frame | Khung hình lấy từ camera |
| Crop | Crop image | Cắt vùng ảnh cần xử lý |
| Confidence | Confidence score | Độ tin cậy của kết quả dự đoán |
| Precision | Precision | Độ chính xác của các dự đoán dương |
| Recall | Recall | Khả năng phát hiện đủ các đối tượng thật |
| IoU | Intersection over Union | Tỷ lệ giao/hợp giữa hộp dự đoán và hộp nhãn |
| mAP | mean Average Precision | Độ chính xác trung bình trong bài toán phát hiện đối tượng |
| mAP50 | mean Average Precision at IoU 0.5 | mAP tại ngưỡng IoU bằng 0.5 |
| mAP50-95 | mean Average Precision from IoU 0.5 to 0.95 | mAP trung bình trên nhiều ngưỡng IoU từ 0.5 đến 0.95 |
| Epoch | Epoch | Một vòng huấn luyện qua toàn bộ tập dữ liệu |
| Batch | Batch | Một lô dữ liệu dùng trong một bước huấn luyện |
| Train | Training | Huấn luyện mô hình |
| Validation | Validation set | Tập kiểm định dùng đánh giá trong quá trình huấn luyện |
| Pretrained | Pre-trained model | Mô hình đã được huấn luyện sẵn |
| Firmware | Firmware | Chương trình nạp vào vi điều khiển Arduino |

---

# CHƯƠNG 1. TỔNG QUAN ĐỀ TÀI

## 3.7. 1.1. Đặt vấn đề

Trong các bãi đỗ xe truyền thống, việc kiểm soát phương tiện thường được thực hiện thủ công thông qua nhân viên bảo vệ, vé giấy hoặc ghi chép bằng tay. Cách làm này có một số hạn chế như tốn nhân lực, dễ nhầm lẫn khi ghi nhận biển số, khó kiểm tra lịch sử vào ra và chưa đảm bảo tính tự động trong quá trình vận hành.

Với sự phát triển của xử lý ảnh, trí tuệ nhân tạo và vi điều khiển, việc xây dựng một hệ thống bãi đỗ xe tự động có khả năng nhận diện biển số, quản lý dữ liệu và điều khiển barrier (thanh chắn/barie) là hướng tiếp cận phù hợp cho các mô hình bãi xe thông minh. Hệ thống có thể tự động ghi nhận biển số phương tiện, kiểm tra điều kiện cho phép vào hoặc ra, đồng thời điều khiển barrier (thanh chắn/barie) thông qua phần cứng.

Đề tài này tập trung xây dựng mô hình bãi đỗ xe tự động sử dụng camera (thiết bị thu hình) để thu nhận hình ảnh biển số, mô hình YOLOv8 (You Only Look Once version 8 - mô hình phát hiện đối tượng phiên bản 8) để phát hiện vùng biển số, PaddleOCR (Paddle Optical Character Recognition - bộ nhận dạng ký tự quang học) để nhận dạng ký tự, SQLite (Structured Query Language Lite - hệ cơ sở dữ liệu nhúng dạng file) để lưu trữ dữ liệu và Arduino (bo mạch vi điều khiển) để điều khiển servo (động cơ điều khiển theo góc quay) barrier (thanh chắn/barie) dựa trên tín hiệu cảm biến vật cản LM393 (module cảm biến vật cản dùng IC so sánh LM393).

## 3.8. 1.2. Mục tiêu đề tài

Mục tiêu chính của đề tài là xây dựng một hệ thống mô phỏng bãi đỗ xe tự động có khả năng vận hành theo cả chế độ tự động và thủ công. Hệ thống cần đáp ứng các yêu cầu sau:

- Thu nhận hình ảnh từ camera (thiết bị thu hình) cổng vào và camera (thiết bị thu hình) cổng ra.
- Nhận diện biển số xe từ ảnh chụp camera (thiết bị thu hình).
- Kiểm tra biển số với danh sách biển số hợp lệ.
- Quản lý danh sách xe đang có trong bãi.
- Kiểm tra số lượng chỗ trống trước khi cho xe vào.
- Kiểm tra xe có trong bãi trước khi cho xe ra.
- Điều khiển barrier (thanh chắn/barie) cổng vào và cổng ra bằng servo (động cơ điều khiển theo góc quay).
- Đọc tín hiệu cảm biến để xác định xe đang chắn barrier (thanh chắn/barie) hay đã đi qua.
- Đóng barrier (thanh chắn/barie) sau khi cảm biến không còn phát hiện vật cản trong một khoảng thời gian an toàn.
- Hiển thị trạng thái camera (thiết bị thu hình), biển số, số lượng xe, nhật ký và trạng thái phần cứng trên giao diện.

## 3.9. 1.3. Phạm vi thực hiện

Đề tài được thực hiện ở mức mô hình đồ án, tập trung vào việc chứng minh nguyên lý hoạt động của một hệ thống bãi xe tự động. Phạm vi của hệ thống gồm:

- Mô hình bãi xe quy mô nhỏ với số lượng chỗ giới hạn.
- Hai cổng hoạt động độc lập: cổng vào và cổng ra.
- Hai camera (thiết bị thu hình) tương ứng với hai cổng.
- Một mạch Arduino (bo mạch vi điều khiển) điều khiển hai servo (động cơ điều khiển theo góc quay) và đọc hai cảm biến LM393 (module cảm biến vật cản dùng IC so sánh LM393).
- Phần mềm điều khiển chạy trên máy tính bằng Python (ngôn ngữ lập trình Python).
- Cơ sở dữ liệu cục bộ dùng SQLite (hệ cơ sở dữ liệu nhúng dạng file).
- Nhận diện biển số trong điều kiện camera (thiết bị thu hình) được lắp đặt và căn chỉnh phù hợp.

Đề tài chưa mở rộng đến các chức năng thương mại như tính phí tự động, thanh toán điện tử, quản lý người dùng nhiều cấp hoặc triển khai trên hệ thống máy chủ từ xa.

## 3.10. 1.4. Bài toán tổng thể

Bài toán của hệ thống có thể mô tả như sau: khi một phương tiện đi tới cổng vào hoặc cổng ra, cảm biến phát hiện vật cản và gửi trạng thái về máy tính thông qua Arduino (bo mạch vi điều khiển). Phần mềm lấy khung hình từ camera (thiết bị thu hình) tương ứng, nhận diện biển số xe, kiểm tra dữ liệu trong cơ sở dữ liệu rồi quyết định có mở barrier (thanh chắn/barie) hay không. Sau khi phương tiện đi qua, cảm biến không còn phát hiện xe, hệ thống chờ thêm một khoảng thời gian an toàn rồi hạ barrier (thanh chắn/barie).

Quy trình này cần đảm bảo ba yêu cầu quan trọng:

- **Đúng dữ liệu:** biển số phải được nhận diện và đối chiếu chính xác.
- **Đúng logic vận hành:** xe vào, xe ra, bãi đầy, xe không hợp lệ phải được xử lý khác nhau.
- **An toàn cơ khí:** barrier (thanh chắn/barie) không được hạ ngay khi xe vẫn còn nằm trong vùng cảm biến.

## 3.11. 1.5. Sơ đồ khối tổng quan hệ thống

![Hình 1.1. Sơ đồ khối tổng quan hệ thống](hinh_bao_cao/hinh_1_1_so_do_tong_quan.svg)

**Hình 1.1** mô tả cấu trúc tổng quát của hệ thống. Hệ thống được chia thành sáu khối chính:

- **Khối thu nhận hình ảnh:** gồm camera (thiết bị thu hình) cổng vào và camera (thiết bị thu hình) cổng ra, có nhiệm vụ cung cấp khung hình cho hệ thống xử lý.
- **Khối nhận diện biển số:** phát hiện vùng biển số, xử lý ảnh, nhận dạng ký tự và trả về chuỗi biển số.
- **Khối điều khiển trung tâm:** tiếp nhận dữ liệu từ camera (thiết bị thu hình), cảm biến, cơ sở dữ liệu và quyết định điều khiển barrier (thanh chắn/barie).
- **Khối cơ sở dữ liệu:** lưu danh sách biển số hợp lệ, xe trong bãi, sức chứa và lịch sử vào ra.
- **Khối giao diện người dùng:** hiển thị camera (thiết bị thu hình), kết quả nhận diện, trạng thái hệ thống và cho phép thao tác thủ công.
- **Khối phần cứng barrier (thanh chắn/barie):** gồm Arduino (bo mạch vi điều khiển), servo (động cơ điều khiển theo góc quay) và cảm biến LM393 (module cảm biến vật cản dùng IC so sánh LM393) để thực hiện đóng mở cổng.

![Hình 1.2. Minh họa bố trí mô hình hai cổng](hinh_bao_cao/hinh_1_2_minh_hoa_mo_hinh.svg)

**Hình 1.2** minh họa cách bố trí phần cứng trong mô hình. Mỗi cổng có một camera (thiết bị thu hình) để thu ảnh biển số, một cảm biến LM393 (module cảm biến vật cản dùng IC so sánh LM393) để phát hiện xe tại vùng barrier (thanh chắn/barie) và một servo (động cơ điều khiển theo góc quay) để nâng hạ thanh chắn. Camera (thiết bị thu hình) cần được đặt sao cho biển số nằm trọn trong khung hình, còn cảm biến cần nằm tại vùng xe đi qua để hỗ trợ cơ chế đóng barrier (thanh chắn/barie) an toàn.

## 3.12. 1.6. Ý nghĩa thực tiễn của đề tài

Hệ thống giúp mô phỏng một quy trình quản lý bãi xe tự động có tính thực tế cao. Thay vì chỉ nhận diện biển số đơn lẻ, đề tài kết hợp cả phần mềm, cơ sở dữ liệu, giao diện và phần cứng điều khiển. Điều này giúp người thực hiện hiểu rõ mối liên hệ giữa xử lý ảnh, điều khiển tự động và quản lý dữ liệu trong một hệ thống nhúng kết hợp máy tính.

---

# CHƯƠNG 2. CƠ SỞ LÝ THUYẾT

## 3.13. 2.1. Tổng quan các khối lý thuyết

Hệ thống bãi đỗ xe tự động trong đề tài được xây dựng từ nhiều khối kỹ thuật khác nhau. Các khối này không hoạt động riêng lẻ mà liên kết với nhau thành một chuỗi xử lý thống nhất:

1. Camera thu nhận hình ảnh phương tiện.
2. Mô hình nhận diện tìm vùng biển số.
3. Bộ OCR (Optical Character Recognition - nhận dạng ký tự quang học) đọc ký tự trên biển số.
4. Bộ hậu xử lý chuẩn hóa kết quả theo định dạng biển số Việt Nam.
5. Bộ điều khiển trung tâm kiểm tra dữ liệu và quyết định mở/đóng cổng.
6. Arduino (bo mạch vi điều khiển) thực hiện điều khiển servo (động cơ điều khiển theo góc quay) và gửi trạng thái cảm biến.
7. Cơ sở dữ liệu lưu trữ trạng thái bãi xe.
8. Giao diện hiển thị và cho phép người dùng điều khiển.

## 3.14. 2.2. Khối nhận diện biển số

Khối nhận diện biển số là khối kỹ thuật trọng tâm của hệ thống, đóng vai trò quyết định dữ liệu đầu vào cho toàn bộ quá trình quản lý xe. Thay vì chỉ dùng một mô hình OCR đơn giản, hệ thống thiết kế một luồng xử lý (pipeline) phức tạp và chặt chẽ gồm nhiều bước nối tiếp nhau nhằm đảm bảo độ chính xác cao nhất trong nhiều điều kiện môi trường. Quá trình này được thực hiện tuần tự qua 6 bước như sau:

**Bước 1: Tiếp nhận nguồn ảnh đầu vào**
- **Nguồn ảnh:** Lấy trực tiếp từ luồng video (stream) của camera cổng vào hoặc cổng ra.
- **Định dạng:** Mỗi khung hình (frame) được trích xuất là một ma trận điểm ảnh (numpy array) ở hệ màu BGR (định dạng chuẩn của OpenCV).
- **Mục tiêu:** Cung cấp khung hình toàn cảnh chứa phương tiện và biển số cho hệ thống phân tích.

**Bước 2: Phát hiện và cắt vùng biển số (YOLOv8)**
- **Mô hình và Cấu hình:** Sử dụng mô hình YOLOv8n (bản nano nhẹ và nhanh). Trọng số mô hình `bien_so_yolo.pt` đã được huấn luyện trước trên tập dữ liệu biển số Việt Nam (100 epochs, kích thước ảnh 640x640, batch 16).
- **Thông số dự đoán:** Hàm nhận diện chạy với độ tin cậy tối thiểu `conf=0.25`, kích thước xử lý `imgsz=640` và chạy trên môi trường `CPU`.
- **Kết quả xử lý:** YOLO trả về tọa độ hộp giới hạn (bounding box - `x1, y1, x2, y2`) của các vùng nghi ngờ là biển số. 
- **Cắt ảnh (Crop):** Hệ thống dùng tọa độ này để cắt (crop) riêng vùng biển số ra khỏi ảnh toàn cảnh. Việc cắt nhỏ ảnh giúp OCR chạy nhanh hơn và không bị nhiễu bởi các chữ viết xuất hiện trên phông nền (như chữ trên áo, biển quảng cáo).

![Hình 2.1. Pipeline nhận diện biển số](hinh_bao_cao/hinh_2_1_pipeline_nhan_dien.svg)
*Hình 2.1. Chuỗi xử lý (pipeline) nhận diện biển số từ ảnh camera.*

**Bước 3: Tiền xử lý - Tạo các phiên bản ảnh (OpenCV)**
- **Số lượng ảnh sinh ra:** Từ 1 ảnh crop vùng biển số ban đầu, hệ thống tạo ra 3 phiên bản ảnh khác nhau để tối đa hóa khả năng đọc của OCR trong mọi điều kiện ánh sáng.
- **Môi trường:** Xử lý bằng thư viện OpenCV.
- **Các phiên bản:**
  1. **Ảnh gốc (BGR):** Giữ lại màu sắc tự nhiên, hoạt động tốt khi điều kiện ánh sáng lý tưởng.
  2. **Ảnh CLAHE:** Ảnh được chuyển sang ảnh xám (grayscale) và áp dụng thuật toán CLAHE (Contrast Limited Adaptive Histogram Equalization) với thông số `clipLimit=2.0`, `tileGridSize=(8, 8)`. Phương pháp này giúp cân bằng sáng, làm rõ nét chữ khi biển số bị lóa đèn hoặc nằm trong vùng sấp bóng.
  3. **Ảnh Otsu:** Lấy ảnh CLAHE đi qua bộ lọc `cv2.threshold` với cờ `THRESH_BINARY + THRESH_OTSU` để phân ngưỡng tự động. Chữ và nền được tách biệt hoàn toàn thành 2 màu Đen/Trắng, vô cùng hiệu quả với ảnh có độ tương phản cao.

**Bước 4: Nhận dạng ký tự quang học (PaddleOCR)**
- **Môi trường:** Sử dụng mô hình PaddleOCR mã nguồn mở.
- **Quá trình thực thi:** 3 phiên bản ảnh (Gốc, CLAHE, Otsu) được lần lượt đưa vào PaddleOCR một cách độc lập.
- **Ghép dòng tạo ứng viên:** Với các biển số xe máy gồm 2 dòng, PaddleOCR thường nhận diện thành nhiều mảnh rời rạc. Hệ thống sẽ thu thập toàn bộ các dòng chữ đọc được, ghép nối chúng lại thành một chuỗi văn bản hoàn chỉnh. Tập hợp chuỗi được ghép và các mảnh rời này tạo thành một danh sách các "ứng viên" (candidates) tiềm năng.

![Hình 2.3. Chi tiết OCR và hậu xử lý biển số Việt Nam](hinh_bao_cao/hinh_2_3_ocr_hau_xu_ly_chi_tiet.svg)
*Hình 2.3. Chi tiết quá trình sinh 3 phiên bản ảnh, qua OCR và chấm điểm.*

**Bước 5: Chuẩn hóa và Sửa lỗi theo vị trí (Post-processing)**
Hậu xử lý là bắt buộc vì mô hình OCR tổng quát không hiểu luật biển số Việt Nam và thường nhầm lẫn giữa số và chữ (VD: 0 và O, 1 và I, 5 và S).
- **Chuẩn hóa:** Dùng Biểu thức chính quy (Regex) `[^A-Za-z0-9]` để loại bỏ hoàn toàn các ký tự lạ, dấu gạch ngang, dấu chấm, khoảng trắng, và chuyển toàn bộ chuỗi về chữ in hoa.
- **Sửa lỗi theo vị trí:** Hệ thống rà soát chuỗi ký tự theo luật biển số VN. Ví dụ:
  - 2 ký tự đầu tiên (mã tỉnh) bắt buộc phải là số. Nếu OCR đọc ra chữ `O`, `I`, `S`, `Z`, hệ thống tự động ép kiểu về `0`, `1`, `5`, `2`.
  - Ký tự thứ 3 (seri) bắt buộc là chữ. Nếu OCR ra số `0`, `8`, hệ thống ép về chữ `D`, `B`.

**Bước 6: Chấm điểm và Lựa chọn kết quả cuối cùng**
- **Quy tắc chấm điểm:** Mỗi ứng viên (sau khi chuẩn hóa) được chấm điểm dựa trên 3 yếu tố:
  1. *Khớp định dạng (Regex):* Chấm 1.0 điểm (hoàn hảo) nếu khớp định dạng Ô tô (2 số + 1 chữ + 5 số), Xe máy (2 số + 1 chữ + 6 số) hoặc Biển đặc biệt (2 số + 2 chữ + 5 số). Chấm 0.9 điểm nếu khớp một phần.
  2. *Độ tin cậy OCR:* Cộng thêm điểm trung bình độ tin cậy (Confidence score) mà PaddleOCR trả về.
  3. *Độ dài phù hợp:* Cộng điểm thưởng nhỏ (0.01 - 0.04) nếu độ dài chuỗi là 8 hoặc 9 ký tự (chuẩn độ dài biển số VN).
- **Kết quả:** Hệ thống so sánh điểm số của tất cả các ứng viên sinh ra từ cả 3 nhánh ảnh. Ứng viên có tổng điểm cao nhất sẽ được chọn làm kết quả chuỗi biển số đầu ra để ghi vào Cơ sở dữ liệu. Đồng thời, hệ thống tạo ra một ảnh hiển thị phụ (nền đen chữ trắng) của biển số để hiển thị trực quan lên giao diện người dùng.

## 3.15. 2.3. Khối điều khiển tự động

Khối điều khiển trung tâm hoạt động dựa trên sự kiện. Các sự kiện chính gồm:

- Cảm biến cổng vào phát hiện xe.
- Cảm biến cổng ra phát hiện xe.
- AI (Artificial Intelligence - trí tuệ nhân tạo) trả về kết quả biển số.
- Người dùng bấm nút điều khiển thủ công.
- Camera bật/tắt hoặc mất khung hình.
- Arduino (bo mạch vi điều khiển) gửi trạng thái cảm biến.

Khi nhận được sự kiện, bộ điều khiển không xử lý độc lập từng sự kiện mà phải xét trạng thái hiện tại của toàn hệ thống. Ví dụ, nếu cảm biến cổng vào phát hiện xe nhưng bãi đã đầy thì không được mở barrier (thanh chắn/barie). Nếu xe ở cổng ra nhưng biển số không tồn tại trong danh sách xe đang ở trong bãi thì cũng không được mở cổng ra.

Điểm quan trọng của khối điều khiển là nó giữ vai trò ra quyết định, không để camera (thiết bị thu hình), AI (trí tuệ nhân tạo) hoặc Arduino (bo mạch vi điều khiển) tự mở cổng. Camera (thiết bị thu hình) chỉ cung cấp ảnh, AI (trí tuệ nhân tạo) chỉ trả về biển số, Arduino (bo mạch vi điều khiển) chỉ thực thi lệnh phần cứng. Quyết định cuối cùng như cho vào, từ chối, cho ra hoặc giữ barrier (thanh chắn/barie) mở đều nằm ở bộ điều khiển trung tâm.

![Hình 2.4. Cơ chế an toàn khi đóng barrier](hinh_bao_cao/hinh_2_4_dong_barie_an_toan.svg)

**Hình 2.4** mô tả logic đóng barrier (thanh chắn/barie) an toàn. Các mũi tên thể hiện luồng kiểm tra lặp lại: nếu cảm biến còn phát hiện xe thì barrier (thanh chắn/barie) tiếp tục giữ mở; nếu cảm biến đã quang và duy trì đủ 2 giây thì hệ thống mới gửi lệnh đóng.

Barrier (thanh chắn/barie) không được đóng ngay khi có lệnh đóng nếu cảm biến vẫn đang phát hiện vật cản. Cơ chế an toàn được thiết kế như sau:

1. Khi barrier (thanh chắn/barie) đang mở, hệ thống theo dõi cảm biến tương ứng.
2. Nếu cảm biến còn phát hiện xe, hệ thống giữ barrier (thanh chắn/barie) ở trạng thái mở.
3. Khi cảm biến không còn phát hiện xe, hệ thống bắt đầu đếm thời gian.
4. Sau 2 giây không có vật cản, hệ thống mới gửi lệnh đóng barrier (thanh chắn/barie).

Cơ chế này giúp mô hình vận hành thực tế hơn, tránh trường hợp barrier (thanh chắn/barie) hạ quá sớm khi xe chưa đi qua hoàn toàn.

## 3.16. 2.4. Khối phần cứng và giao tiếp

Arduino (bo mạch vi điều khiển) đóng vai trò là bộ điều khiển phần cứng. Trong đề tài, Arduino nhận lệnh từ máy tính qua Serial (giao tiếp nối tiếp), điều khiển hai servo (động cơ điều khiển theo góc quay) và đọc trạng thái hai cảm biến LM393 (module cảm biến vật cản dùng IC so sánh LM393).

Arduino (bo mạch vi điều khiển) giúp tách phần điều khiển cơ khí khỏi phần mềm máy tính. Máy tính chỉ cần gửi lệnh mức cao như mở cổng vào hoặc đóng cổng ra, còn Arduino thực hiện điều khiển servo (động cơ điều khiển theo góc quay) ở mức tín hiệu.

Servo (động cơ điều khiển theo góc quay) là động cơ có khả năng quay đến một góc xác định. Trong mô hình, servo được dùng để nâng và hạ thanh barrier (thanh chắn/barie). Hệ thống quy ước:

- Góc đóng: barrier (thanh chắn/barie) nằm ngang, không cho xe qua.
- Góc mở: barrier (thanh chắn/barie) nâng lên, cho xe đi qua.

Để chuyển động thực tế hơn, servo (động cơ điều khiển theo góc quay) không quay tức thời từ góc đóng sang góc mở, mà được điều khiển từng bước nhỏ với độ trễ giữa các bước.

Cảm biến LM393 (module cảm biến vật cản dùng IC so sánh LM393) được dùng để phát hiện vật cản tại cổng vào và cổng ra. Khi có xe chắn vùng cảm biến, tín hiệu đầu ra thay đổi. Arduino (bo mạch vi điều khiển) đọc tín hiệu này và gửi trạng thái về máy tính.

Trong hệ thống, cảm biến không chỉ dùng để phát hiện xe xuất hiện mà còn dùng để quyết định thời điểm an toàn để đóng barrier (thanh chắn/barie).

![Hình 2.5. Giao thức Serial giữa máy tính và Arduino](hinh_bao_cao/hinh_2_5_giao_tiep_serial.svg)

**Hình 2.5** mô tả giao thức truyền nhận giữa máy tính và Arduino (bo mạch vi điều khiển). Mũi tên từ máy tính sang Arduino là luồng lệnh điều khiển; mũi tên từ Arduino về máy tính là luồng phản hồi trạng thái cảm biến và thông tin kiểm tra kết nối.

Máy tính và Arduino (bo mạch vi điều khiển) giao tiếp thông qua cổng Serial (giao tiếp nối tiếp). Giao thức được thiết kế đơn giản bằng chuỗi văn bản, giúp dễ kiểm tra bằng Serial Monitor (cửa sổ giám sát giao tiếp nối tiếp) và dễ mở rộng.

Một số lệnh từ máy tính gửi xuống Arduino (bo mạch vi điều khiển) được trình bày trong Bảng 2.1.

**Bảng 2.1. Giao thức lệnh gửi từ máy tính xuống Arduino (bo mạch vi điều khiển)**

| Lệnh | Ý nghĩa |
|---|---|
| `VAO_MO` | Mở barrier (thanh chắn/barie) cổng vào |
| `VAO_DONG` | Đóng barrier (thanh chắn/barie) cổng vào |
| `RA_MO` | Mở barrier (thanh chắn/barie) cổng ra |
| `RA_DONG` | Đóng barrier (thanh chắn/barie) cổng ra |
| `PING` | Kiểm tra phản hồi Arduino (bo mạch vi điều khiển) |
| `SERVO_TEST` | Kiểm tra hoạt động của hai servo (động cơ điều khiển theo góc quay) |

Dữ liệu Arduino (bo mạch vi điều khiển) gửi lên máy tính có dạng:

```text
CAM_BIEN:xe_vao=1,xe_ra=0
```

Trong đó `xe_vao` và `xe_ra` thể hiện trạng thái cảm biến tại hai cổng.

Kênh Serial (giao tiếp nối tiếp) là hai chiều. Chiều từ máy tính xuống Arduino (bo mạch vi điều khiển) là lệnh điều khiển như mở hoặc đóng barrier (thanh chắn/barie). Chiều từ Arduino lên máy tính là trạng thái cảm biến và thông tin phản hồi. Việc dùng chuỗi văn bản làm giao thức giúp quá trình kiểm tra khi ghép nối phần cứng trở nên đơn giản: có thể mở Serial Monitor (cửa sổ giám sát giao tiếp nối tiếp) để gửi thử `SERVO_TEST`, `PING` hoặc quan sát dòng `CAM_BIEN`.

## 3.17. 2.5. Khối lưu trữ dữ liệu

![Hình 2.6. Sơ đồ cơ sở dữ liệu](hinh_bao_cao/hinh_2_6_erd_csdl.svg)

**Hình 2.6** mô tả các nhóm dữ liệu chính trong hệ thống. Bảng `xe_trong_bai` thể hiện trạng thái hiện tại của bãi xe, còn bảng `lich_su_ra_vao` lưu lại các sự kiện đã xảy ra để phục vụ theo dõi.

SQLite (Structured Query Language Lite - hệ cơ sở dữ liệu nhúng dạng file) được sử dụng vì phù hợp với mô hình cục bộ, không cần cài đặt máy chủ cơ sở dữ liệu riêng. Cơ sở dữ liệu gồm bốn nhóm dữ liệu chính:

- **Cấu hình:** lưu sức chứa bãi xe.
- **Biển số hợp lệ:** lưu danh sách biển số được phép vào.
- **Xe trong bãi:** lưu các xe đang hiện diện trong bãi.
- **Lịch sử vào ra:** lưu nhật ký sự kiện phục vụ theo dõi và kiểm tra.

---

# CHƯƠNG 3. THIẾT KẾ VÀ ĐÁNH GIÁ HỆ THỐNG

## 3.18. Môi trường thực nghiệm

Hệ thống được thử nghiệm trên mô hình bãi xe quy mô nhỏ. Môi trường thực nghiệm gồm:

- Máy tính chạy phần mềm Python (ngôn ngữ lập trình Python) với giao diện Tkinter (thư viện giao diện đồ họa của Python).
- Camera USB/Full HD (camera dùng cổng USB, độ phân giải Full HD) dùng cho cổng vào và cổng ra.
- Arduino (bo mạch vi điều khiển) kết nối với máy tính qua cổng USB (Universal Serial Bus - chuẩn kết nối giữa máy tính và thiết bị).
- Hai servo (động cơ điều khiển theo góc quay) dùng để đóng/mở barrier (thanh chắn/barie).
- Hai cảm biến LM393 (module cảm biến vật cản dùng IC so sánh LM393) dùng để phát hiện xe tại cổng vào và cổng ra.
- Cơ sở dữ liệu SQLite (hệ cơ sở dữ liệu nhúng dạng file) lưu cục bộ trên máy tính.

Camera được căn chỉnh sao cho biển số nằm trong vùng quan sát, hạn chế bị cắt mất mép và giảm ảnh hưởng của ánh sáng chói.

## 3.19. Nguyên tắc thiết kế

Hệ thống được thiết kế theo hướng chia thành các khối chức năng độc lập. Mỗi khối đảm nhiệm một vai trò cụ thể, giúp quá trình kiểm tra, bảo trì và mở rộng dễ dàng hơn. Cách chia khối cũng giúp báo cáo và mô hình hóa hệ thống rõ ràng hơn.

Các nguyên tắc thiết kế chính:

- Tách biệt giao diện, xử lý logic, nhận diện biển số, lưu trữ dữ liệu và điều khiển phần cứng.
- Luồng camera (thiết bị thu hình) và luồng AI (Artificial Intelligence - trí tuệ nhân tạo) không làm treo giao diện.
- Mọi quyết định mở cổng đều phải đi qua bộ điều khiển trung tâm.
- Cơ sở dữ liệu là nguồn xác định trạng thái xe trong bãi.
- Barrier chỉ được đóng khi cảm biến xác nhận vùng cổng đã an toàn.

## 3.20. Kiến trúc phần mềm tổng thể

![Hình 3.1. Sơ đồ module phần mềm](hinh_bao_cao/hinh_3_1_module_phan_mem.svg)

**Hình 3.1** cho thấy bộ điều khiển trung tâm là điểm phối hợp chính giữa giao diện, camera (thiết bị thu hình), AI (trí tuệ nhân tạo), cơ sở dữ liệu và Arduino (bo mạch vi điều khiển). Các module (khối chức năng phần mềm) không tự quyết định mở cổng mà gửi dữ liệu về bộ điều khiển để xử lý thống nhất.

Hệ thống phần mềm gồm các khối sau:

- **Khối giao diện:** hiển thị thông tin và nhận thao tác người dùng.
- **Khối điều khiển trung tâm:** điều phối toàn bộ hoạt động của hệ thống.
- **Khối camera (thiết bị thu hình):** đọc hình ảnh từ camera (thiết bị thu hình) vào và camera ra.
- **Khối AI (Artificial Intelligence - trí tuệ nhân tạo) nhận diện:** xử lý ảnh và trả về biển số.
- **Khối cơ sở dữ liệu:** lưu trữ và truy vấn thông tin xe.
- **Khối giao tiếp Arduino (bo mạch vi điều khiển):** gửi lệnh và đọc trạng thái phần cứng.

Khối điều khiển trung tâm là nơi liên kết các khối còn lại. Camera (thiết bị thu hình), AI (trí tuệ nhân tạo), cơ sở dữ liệu và Arduino (bo mạch vi điều khiển) không tự quyết định mở barrier (thanh chắn/barie); mọi quyết định đều được đưa về khối điều khiển trung tâm để đảm bảo thống nhất logic.

## 3.21. Luồng dữ liệu trong hệ thống

![Hình 3.2. Luồng dữ liệu trong hệ thống](hinh_bao_cao/hinh_3_2_luong_du_lieu.svg)

**Hình 3.2** mô tả hướng di chuyển của dữ liệu giữa các khối. Dữ liệu ảnh đi từ camera (thiết bị thu hình) đến bộ điều khiển và AI (trí tuệ nhân tạo); dữ liệu biển số đi ngược về bộ điều khiển để kiểm tra cơ sở dữ liệu; lệnh điều khiển đi từ bộ điều khiển xuống Arduino (bo mạch vi điều khiển).

Luồng dữ liệu chính của hệ thống gồm:

1. Camera gửi khung hình mới nhất cho bộ điều khiển.
2. Khi có yêu cầu nhận diện, bộ điều khiển lấy khung hình và gửi vào hàng đợi AI (trí tuệ nhân tạo).
3. Khối AI (trí tuệ nhân tạo) trả về biển số và ảnh biển số đã xử lý để hiển thị.
4. Bộ điều khiển kiểm tra biển số với cơ sở dữ liệu.
5. Nếu đủ điều kiện, bộ điều khiển gửi lệnh mở barrier (thanh chắn/barie) cho Arduino (bo mạch vi điều khiển).
6. Arduino (bo mạch vi điều khiển) điều khiển servo (động cơ điều khiển theo góc quay) và gửi trạng thái cảm biến về máy tính.
7. Giao diện cập nhật trạng thái, nhật ký và kết quả nhận diện.

Việc tổ chức luồng dữ liệu theo hướng này giúp hạn chế xung đột giữa các tác vụ có tốc độ khác nhau. Camera (thiết bị thu hình) cần cập nhật liên tục, AI (trí tuệ nhân tạo) xử lý chậm hơn, còn giao diện cần phản hồi ổn định cho người dùng.

## 3.22. Thiết kế khối giao diện người dùng

Giao diện được thiết kế để người dùng quan sát và điều khiển toàn bộ hệ thống trên một màn hình. Các vùng chức năng chính gồm:

- Vùng chọn camera (thiết bị thu hình) cổng vào và cổng ra.
- Vùng hiển thị hình ảnh trực tiếp từ hai camera (thiết bị thu hình).
- Vùng hiển thị ảnh biển số sau xử lý của từng cổng.
- Vùng hiển thị chuỗi biển số nhận diện được.
- Vùng trạng thái bãi xe, gồm số xe hiện tại và sức chứa.
- Vùng chọn chế độ tự động hoặc thủ công.
- Vùng kết nối Arduino (bo mạch vi điều khiển) qua cổng COM (Communication Port - cổng giao tiếp nối tiếp).
- Vùng thêm/xóa biển số hợp lệ.
- Vùng nhật ký sự kiện.

Giao diện không trực tiếp xử lý nhận diện hay điều khiển phần cứng. Các thao tác từ giao diện được gửi đến bộ điều khiển trung tâm, sau đó bộ điều khiển quyết định bước xử lý tiếp theo.

## 3.23. Thiết kế khối camera (thiết bị thu hình)

Hệ thống sử dụng hai camera (thiết bị thu hình):

- **Camera cổng vào:** chụp biển số khi xe đi vào bãi.
- **Camera cổng ra:** chụp biển số khi xe rời bãi.

Mỗi camera (thiết bị thu hình) được đọc ở một luồng riêng để không ảnh hưởng lẫn nhau. Ảnh camera (thiết bị thu hình) dùng cho hai mục đích:

- Hiển thị trực tiếp trên giao diện.
- Cung cấp khung hình cho khối nhận diện khi có xe được cảm biến phát hiện.

Để đảm bảo nhận diện ổn định, camera (thiết bị thu hình) cần được lắp sao cho biển số nằm đủ trong khung hình, không bị cắt mất mép và không quá chói. Với mô hình đồ án, việc căn chỉnh camera (thiết bị thu hình) là một phần quan trọng để đảm bảo kết quả nhận diện.

## 3.24. Thiết kế khối nhận diện biển số

Khối nhận diện biển số trong hệ thống được thiết kế như một dịch vụ xử lý ảnh độc lập. Đầu vào của khối là một frame (khung hình) BGR (Blue - Green - Red - thứ tự kênh màu xanh dương, xanh lá, đỏ trong OpenCV) lấy từ camera (thiết bị thu hình) cổng vào hoặc cổng ra. Đầu ra gồm hai phần: chuỗi biển số đã chuẩn hóa để bộ điều khiển kiểm tra logic, và ảnh biển số đã xử lý để hiển thị cho người dùng quan sát. Cách tách đầu ra như vậy giúp hệ thống vừa có dữ liệu dạng text (văn bản) để xử lý tự động, vừa có hình ảnh minh họa để người vận hành biết AI (trí tuệ nhân tạo) đang đọc từ vùng nào.

Khi bắt đầu chương trình, mô hình YOLO (You Only Look Once - mô hình phát hiện đối tượng một giai đoạn) và PaddleOCR (bộ nhận dạng ký tự quang học) được nạp vào bộ nhớ. Việc nạp mô hình thường tốn thời gian ở lần đầu, nên hệ thống có bước warm-up (chạy khởi động) để tránh trường hợp xe đầu tiên bị xử lý chậm bất thường. Khi cảm biến phát hiện xe, bộ điều khiển không gửi toàn bộ luồng video sang AI (trí tuệ nhân tạo), mà chỉ lấy frame (khung hình) mới nhất tại thời điểm cần nhận diện. Cách làm này giảm tải cho CPU (Central Processing Unit - bộ xử lý trung tâm)/GPU (Graphics Processing Unit - bộ xử lý đồ họa) và phù hợp với bài toán bãi xe: chỉ cần nhận diện khi có xe ở cổng, không cần OCR (nhận dạng ký tự quang học) liên tục 30 khung hình mỗi giây.

Ở bước phát hiện vùng biển, YOLO (mô hình phát hiện đối tượng một giai đoạn) trả về danh sách hộp giới hạn kèm độ tin cậy. Hệ thống chọn vùng biển số có điểm tin cậy phù hợp rồi crop (cắt vùng ảnh) từ ảnh gốc. Nếu crop quá sát, OCR (nhận dạng ký tự quang học) có thể mất một phần ký tự ở mép; nếu crop quá rộng, OCR dễ đọc nhiễu từ nền. Vì vậy trong mô hình thực tế, camera (thiết bị thu hình) cần được đặt sao cho biển số nằm đủ trong khung và kích thước biển số không quá lớn so với ảnh. Đây là lý do phần lắp đặt camera có ảnh hưởng trực tiếp đến độ chính xác nhận diện.

Sau khi có ảnh vùng biển số, hệ thống tạo ba phiên bản ảnh cho OCR (nhận dạng ký tự quang học). Ảnh gốc được giữ lại vì trong thực nghiệm đây là phiên bản cho độ chính xác rất cao khi ánh sáng ổn định. Ảnh CLAHE (cân bằng lược đồ xám thích nghi có giới hạn tương phản) được tạo bằng cách cân bằng tương phản cục bộ, giúp làm rõ nét chữ trong vùng sáng tối không đều. Ảnh Otsu (ảnh nhị phân theo ngưỡng Otsu) được tạo bằng cách nhị phân hóa, có tác dụng tách chữ và nền trong trường hợp biển số có độ tương phản mạnh. Ba ảnh này không nhằm làm đẹp giao diện, mà nhằm tạo nhiều điều kiện đọc khác nhau cho OCR.

Kết quả PaddleOCR (bộ nhận dạng ký tự quang học) có thể gồm nhiều dòng, đặc biệt với biển số xe máy hai dòng. Hệ thống tạo nhiều ứng viên từ kết quả OCR (nhận dạng ký tự quang học): chuỗi ghép tất cả các dòng và từng dòng riêng lẻ. Mỗi ứng viên được chuẩn hóa bằng cách loại bỏ ký tự không phải chữ/số, viết hoa và sửa lỗi theo vị trí. Sau đó hệ thống chấm điểm ứng viên theo ba yếu tố: độ tin cậy trung bình do OCR trả về, mức độ khớp với định dạng biển số Việt Nam và độ dài chuỗi phù hợp. Ứng viên có điểm cao nhất được chọn làm kết quả cuối.

Vai trò của từng bước trong khối nhận diện được tóm tắt trong Bảng 3.1.

**Bảng 3.1. Vai trò các bước trong khối nhận diện biển số**

| Bước | Mục đích | Lý do cần thiết |
|---|---|---|
| YOLOv8 (You Only Look Once version 8 - mô hình phát hiện đối tượng phiên bản 8) phát hiện biển số | Tìm vùng biển số trong toàn ảnh | Giảm nhiễu nền trước khi OCR (nhận dạng ký tự quang học) |
| Crop (cắt vùng ảnh) vùng biển số | Tách vùng quan tâm | Tăng tốc và tăng độ chính xác OCR (nhận dạng ký tự quang học) |
| Tạo ảnh gốc/CLAHE/Otsu | Tạo nhiều điều kiện đọc | Ảnh thực tế thay đổi theo ánh sáng; CLAHE là cân bằng lược đồ xám thích nghi có giới hạn tương phản, Otsu là phương pháp tự động chọn ngưỡng nhị phân ảnh |
| PaddleOCR (bộ nhận dạng ký tự quang học) | Đọc ký tự từ ảnh | Không cần tự train (huấn luyện) bộ nhận dạng từng ký tự |
| Chuẩn hóa chuỗi | Đưa text về dạng thống nhất | Loại bỏ dấu, khoảng trắng, ký tự lạ |
| Sửa lỗi theo vị trí | Sửa nhầm lẫn chữ/số | Tận dụng cấu trúc biển số Việt Nam |
| Chấm điểm | Chọn ứng viên tốt nhất | Kết hợp confidence (độ tin cậy) OCR (nhận dạng ký tự quang học) và luật định dạng |

Ảnh nền đen/chữ trắng được tạo sau cùng để hiển thị trực quan trên giao diện. Ảnh này giúp người dùng thấy rõ vùng ký tự mà hệ thống đang xử lý, nhưng không phải là dữ liệu duy nhất quyết định kết quả OCR (nhận dạng ký tự quang học). Quyết định nhận diện dựa trên nhiều ứng viên từ ảnh gốc, CLAHE (cân bằng lược đồ xám thích nghi có giới hạn tương phản) và Otsu (phương pháp tự động chọn ngưỡng nhị phân ảnh).

## 3.25. Kết quả nhận diện biển số

Khối nhận diện được đánh giá theo hai lớp kết quả. Lớp thứ nhất là mô hình YOLOv8 (You Only Look Once version 8 - mô hình phát hiện đối tượng phiên bản 8) phát hiện vùng biển số; lớp này quyết định hệ thống có cắt đúng vùng biển để đưa sang OCR (Optical Character Recognition - nhận dạng ký tự quang học) hay không. Lớp thứ hai là OCR và hậu xử lý; lớp này quyết định chuỗi biển số cuối cùng có đúng hoàn toàn hay không.

Đối với mô hình YOLOv8 (mô hình phát hiện đối tượng phiên bản 8), kết quả huấn luyện sau 100 epochs (100 vòng huấn luyện) đạt các chỉ số trong Bảng 4.1.

**Bảng 4.1. Kết quả huấn luyện YOLOv8**

| Chỉ số YOLOv8 (mô hình phát hiện đối tượng phiên bản 8) | Kết quả |
|---|---:|
| Precision (độ chính xác dự đoán dương) | 99.18% |
| Recall (khả năng phát hiện đủ) | 99.43% |
| mAP50 (độ chính xác trung bình tại ngưỡng IoU 0.5) | 99.48% |
| mAP50-95 (mAP trung bình từ ngưỡng IoU 0.5 đến 0.95) | 72.74% |

Precision (độ chính xác dự đoán dương) và Recall (khả năng phát hiện đủ) cao cho thấy mô hình vừa ít phát hiện nhầm, vừa ít bỏ sót biển số. Trong bài toán này, mAP50 (độ chính xác trung bình tại ngưỡng IoU 0.5) là chỉ số quan trọng vì nhiệm vụ của YOLO (mô hình phát hiện đối tượng một giai đoạn) là khoanh vùng biển số đủ đúng để OCR (nhận dạng ký tự quang học) đọc được. mAP50-95 (mAP trung bình từ ngưỡng IoU 0.5 đến 0.95) thấp hơn mAP50 là bình thường vì chỉ số này yêu cầu hộp dự đoán trùng khít hơn ở nhiều ngưỡng IoU (Intersection over Union - tỷ lệ giao/hợp giữa hai hộp) cao hơn. Với mô hình đồ án, yêu cầu chính là crop (cắt vùng ảnh) được vùng biển số đủ tốt, không nhất thiết hộp phải trùng tuyệt đối từng mép.

Đối với OCR (nhận dạng ký tự quang học), tập đánh giá gồm 200 ảnh biển số đã gán nhãn thủ công. Accuracy (độ chính xác) cấp ký tự thể hiện tỷ lệ ký tự nhận diện đúng trên tổng số ký tự; accuracy (độ chính xác) cấp biển số yêu cầu toàn bộ chuỗi biển số phải đúng hoàn toàn. Vì vậy accuracy cấp biển số luôn khó đạt cao hơn accuracy cấp ký tự: chỉ cần sai một ký tự thì cả biển số bị tính là sai.

Kết quả đánh giá các phương pháp tiền xử lý ảnh được tổng hợp trong Bảng 4.2.

**Bảng 4.2. So sánh phương pháp tiền xử lý ảnh**

| Phương pháp | Accuracy ký tự | Accuracy biển số |
|---|---:|---:|
| Ảnh gốc | 99.62% | 97.00% |
| CLAHE (cân bằng lược đồ xám thích nghi có giới hạn tương phản) | 98.56% | 96.00% |
| Otsu (phương pháp tự động chọn ngưỡng nhị phân ảnh) | 99.19% | 93.50% |
| Kết hợp chọn tốt nhất | 99.69% | 97.50% |

Kết quả cho thấy ảnh gốc đã cho độ chính xác cao trong điều kiện camera (thiết bị thu hình) được căn chỉnh tốt. Tuy nhiên, phương pháp kết hợp nhiều biến thể ảnh và chọn kết quả tốt nhất vẫn đạt kết quả cao nhất, với độ chính xác ký tự 99.69% và độ chính xác biển số 97.50%. Trên tập 200 ảnh test (kiểm thử), tỷ lệ 97.50% tương ứng với 195 biển số được đọc đúng hoàn toàn. Điều này chứng minh việc thử nhiều phiên bản ảnh không làm hệ thống phức tạp một cách vô ích, mà giúp tăng khả năng chọn đúng kết quả trong các điều kiện ảnh khác nhau.

![Hình 4.1. So sánh tiền xử lý ảnh](hinh_bao_cao/hinh_4_1_so_sanh_tien_xu_ly.svg)

**Hình 4.1** trực quan hóa bảng so sánh các phương pháp tiền xử lý. Biểu đồ cho thấy phương pháp kết hợp chọn kết quả tốt nhất đạt độ chính xác cao nhất ở cả cấp ký tự và cấp biển số.

## 3.26. Kết quả hậu xử lý

Hậu xử lý theo định dạng biển số Việt Nam giúp sửa một số lỗi nhận dạng ký tự và chọn kết quả hợp lý hơn. Kết quả so sánh trước và sau hậu xử lý được trình bày trong Bảng 4.3.

**Bảng 4.3. So sánh trước và sau hậu xử lý**

| Chỉ số | Trước hậu xử lý | Sau hậu xử lý |
|---|---:|---:|
| Accuracy cấp ký tự | 99.44% | 99.69% |
| Accuracy cấp biển số | 95.00% | 97.50% |

Sau hậu xử lý, độ chính xác cấp biển số tăng từ 95.00% lên 97.50%. Điều này cho thấy việc áp dụng quy tắc định dạng biển số Việt Nam có tác dụng tích cực, đặc biệt trong các trường hợp OCR (nhận dạng ký tự quang học) đọc nhầm các ký tự có hình dạng gần giống nhau.

![Hình 4.2. So sánh trước và sau hậu xử lý](hinh_bao_cao/hinh_4_2_so_sanh_hau_xu_ly.svg)

**Hình 4.2** cho thấy hậu xử lý theo quy tắc biển số Việt Nam giúp tăng độ chính xác, đặc biệt ở cấp biển số hoàn chỉnh. Điều này chứng minh rằng việc kết hợp OCR (nhận dạng ký tự quang học) với luật định dạng thực tế là cần thiết.

## 3.27. Thiết kế luồng xe vào

![Hình 3.3. Lưu đồ xử lý xe vào](hinh_bao_cao/hinh_3_3_luu_do_xe_vao.svg)

**Hình 3.3** mô tả luồng xử lý xe vào theo hướng từ trên xuống. Các nhánh rẽ thể hiện trường hợp từ chối mở cổng khi không đọc được biển số, biển số không hợp lệ, xe đã có trong bãi hoặc bãi đã đầy.

Luồng xe vào được thiết kế như sau:

1. Xe tiến tới cổng vào.
2. Cảm biến cổng vào phát hiện vật cản.
3. Arduino (bo mạch vi điều khiển) gửi trạng thái cảm biến về máy tính.
4. Bộ điều khiển lấy ảnh mới nhất từ camera (thiết bị thu hình) vào.
5. Khối AI (trí tuệ nhân tạo) nhận diện biển số.
6. Bộ điều khiển kiểm tra các điều kiện:
   - Biển số có đọc được hay không.
   - Biển số có nằm trong danh sách hợp lệ hay không.
   - Xe đã có trong bãi hay chưa.
   - Bãi còn chỗ trống hay không.
7. Nếu hợp lệ, hệ thống ghi xe vào cơ sở dữ liệu.
8. Bộ điều khiển gửi lệnh mở barrier (thanh chắn/barie) vào.
9. Khi xe đi qua và cảm biến không còn phát hiện vật cản, hệ thống chờ 2 giây.
10. Bộ điều khiển gửi lệnh đóng barrier (thanh chắn/barie) vào.

Nếu một trong các điều kiện kiểm tra không đạt, hệ thống không mở barrier (thanh chắn/barie) và ghi thông báo vào nhật ký.

## 3.28. Thiết kế luồng xe ra

![Hình 3.4. Lưu đồ xử lý xe ra](hinh_bao_cao/hinh_3_4_luu_do_xe_ra.svg)

**Hình 3.4** mô tả luồng xử lý xe ra. Điểm khác biệt quan trọng là dữ liệu xe chỉ được xóa khỏi bảng xe trong bãi sau khi xe đã đi qua, cảm biến quang và barrier (thanh chắn/barie) đã đóng lại.

Luồng xe ra được thiết kế theo hướng chặt chẽ hơn so với việc chỉ giảm số lượng xe tự động. Hệ thống cần xác định biển số xe ra và kiểm tra xe đó có đang ở trong bãi hay không.

Các bước xử lý:

1. Xe tiến tới cổng ra.
2. Cảm biến cổng ra phát hiện vật cản.
3. Arduino (bo mạch vi điều khiển) gửi trạng thái cảm biến về máy tính.
4. Bộ điều khiển lấy ảnh từ camera (thiết bị thu hình) ra.
5. Khối AI (trí tuệ nhân tạo) nhận diện biển số xe ra.
6. Bộ điều khiển kiểm tra biển số có tồn tại trong danh sách xe đang ở trong bãi không.
7. Nếu có, hệ thống mở barrier (thanh chắn/barie) ra.
8. Xe đi qua cổng ra.
9. Khi cảm biến không còn phát hiện vật cản, hệ thống chờ 2 giây.
10. Bộ điều khiển đóng barrier (thanh chắn/barie) ra.
11. Sau khi đóng barrier (thanh chắn/barie), hệ thống mới xóa biển số khỏi danh sách xe trong bãi và ghi lịch sử ra.

Cách thiết kế này tránh lỗi xóa xe khỏi bãi quá sớm. Nếu barrier (thanh chắn/barie) mở nhưng xe chưa đi qua, dữ liệu vẫn chưa bị cập nhật sai.

## 3.29. Thiết kế khối cơ sở dữ liệu

Cơ sở dữ liệu gồm bốn bảng chính, được mô tả trong Bảng 3.2.

**Bảng 3.2. Thiết kế các bảng dữ liệu chính**

| Bảng | Chức năng |
|---|---|
| `cai_dat` | Lưu cấu hình hệ thống, ví dụ sức chứa bãi xe |
| `bien_so_hop_le` | Lưu danh sách biển số được phép vào bãi |
| `xe_trong_bai` | Lưu các xe đang có trong bãi |
| `lich_su_ra_vao` | Lưu lịch sử xe vào và xe ra |

Các thao tác chính với cơ sở dữ liệu:

- Thêm biển số hợp lệ.
- Xóa biển số hợp lệ.
- Kiểm tra biển số có hợp lệ không.
- Thêm xe vào danh sách xe trong bãi.
- Kiểm tra xe có đang trong bãi không.
- Xóa xe khỏi bãi khi xe ra.
- Đếm số xe hiện tại.
- Lấy lịch sử vào ra.

Trong hệ thống, dữ liệu xe trong bãi có vai trò quyết định. Xe chỉ được ra khi biển số được nhận diện tại cổng ra tồn tại trong bảng xe đang ở trong bãi.

## 3.30. Thiết kế khối giao tiếp Arduino (bo mạch vi điều khiển)

Khối giao tiếp Arduino (bo mạch vi điều khiển) có nhiệm vụ:

- Quét danh sách cổng COM (Communication Port - cổng giao tiếp nối tiếp).
- Kết nối với Arduino (bo mạch vi điều khiển).
- Kiểm tra phản hồi thông qua lệnh `PING`.
- Gửi lệnh mở/đóng barrier (thanh chắn/barie).
- Đọc trạng thái cảm biến.
- Nhận thông tin firmware (chương trình nạp vào vi điều khiển) để xác nhận Arduino (bo mạch vi điều khiển) đã nạp đúng chương trình.

Giao thức dạng chuỗi giúp quá trình kiểm tra đơn giản. Khi cần kiểm tra phần cứng, người dùng có thể mở Serial Monitor (cửa sổ giám sát giao tiếp nối tiếp) và gửi lệnh `SERVO_TEST` để xác nhận hai servo (động cơ điều khiển theo góc quay) hoạt động trước khi chạy toàn bộ hệ thống.

## 3.31. Thiết kế khối phần cứng barrier (thanh chắn/barie)

Khối phần cứng gồm:

- Arduino (bo mạch vi điều khiển).
- Hai servo (động cơ điều khiển theo góc quay): một cho cổng vào, một cho cổng ra.
- Hai cảm biến LM393 (module cảm biến vật cản dùng IC so sánh LM393): một ở cổng vào, một ở cổng ra.
- Nguồn cấp cho Arduino (bo mạch vi điều khiển) và servo (động cơ điều khiển theo góc quay).
- Kết nối USB (Universal Serial Bus - chuẩn kết nối giữa máy tính và thiết bị) giữa Arduino (bo mạch vi điều khiển) và máy tính.

![Hình 3.5. Sơ đồ đấu nối phần cứng Arduino - servo - cảm biến](hinh_bao_cao/hinh_3_6_so_do_dau_noi_phan_cung.svg)

**Hình 3.5** mô tả sơ đồ đấu nối phần cứng. Các mũi tên từ Arduino (bo mạch vi điều khiển) đến servo (động cơ điều khiển theo góc quay) là tín hiệu điều khiển PWM (Pulse Width Modulation - điều chế độ rộng xung) một chiều: Arduino phát xung điều khiển góc quay cho servo. Các mũi tên từ cảm biến LM393 (module cảm biến vật cản dùng IC so sánh LM393) về Arduino là tín hiệu số một chiều: cảm biến xuất mức logic tại chân DO (Digital Output - ngõ ra số), Arduino đọc tại các chân digital (chân số). Mũi tên giữa máy tính và Arduino là giao tiếp Serial (giao tiếp nối tiếp) hai chiều qua USB (chuẩn kết nối giữa máy tính và thiết bị): máy tính gửi lệnh, Arduino gửi trạng thái cảm biến và phản hồi.

Trong mô hình, servo (động cơ điều khiển theo góc quay) cổng vào nối chân tín hiệu với D9, servo cổng ra nối chân tín hiệu với D10. Cảm biến LM393 (module cảm biến vật cản dùng IC so sánh LM393) cổng vào nối DO (Digital Output - ngõ ra số) với D2, cảm biến LM393 cổng ra nối DO với D3. Hai cảm biến được cấp VCC (Voltage Common Collector - chân cấp nguồn dương) và GND (Ground - chân mass/đất chung) từ Arduino (bo mạch vi điều khiển). Nếu servo dùng nguồn 5V ngoài để tránh sụt áp, bắt buộc GND của nguồn servo phải nối chung với GND Arduino; nếu không, tín hiệu điều khiển từ Arduino sang servo sẽ không có cùng mốc điện áp và servo có thể rung hoặc không hoạt động đúng.

Nguyên lý hoạt động của phần cứng:

1. Arduino (bo mạch vi điều khiển) đọc trạng thái cảm biến theo chu kỳ.
2. Khi trạng thái cảm biến thay đổi hoặc đến chu kỳ gửi trạng thái, Arduino (bo mạch vi điều khiển) gửi dữ liệu lên máy tính.
3. Khi nhận lệnh mở hoặc đóng, Arduino điều khiển servo (động cơ điều khiển theo góc quay) quay đến góc tương ứng.
4. Servo (động cơ điều khiển theo góc quay) được điều khiển từng bước nhỏ để chuyển động mượt hơn.

Một số lưu ý khi lắp đặt phần cứng:

- Cảm biến LM393 (module cảm biến vật cản dùng IC so sánh LM393) cần được chỉnh biến trở để khoảng cách phát hiện phù hợp với kích thước mô hình.
- Vùng phát hiện của cảm biến nên đặt đúng vị trí xe đi qua barrier (thanh chắn/barie), không đặt quá xa khiến barrier đóng sai thời điểm.
- Servo SG90 (động cơ servo cỡ nhỏ SG90) có dòng khởi động tương đối lớn, nếu dùng nguồn USB (chuẩn kết nối giữa máy tính và thiết bị) yếu có thể làm Arduino (bo mạch vi điều khiển) reset hoặc servo giật.
- Dây tín hiệu servo nên cắm đúng chân điều khiển, dây đỏ là VCC (chân cấp nguồn dương), dây nâu/đen là GND (mass/đất chung), dây cam/vàng là tín hiệu.
- Khi thử phần cứng, nên dùng lệnh `SERVO_TEST` trước để kiểm tra hai servo (động cơ điều khiển theo góc quay) độc lập với giao diện.
- Barrier (thanh chắn/barie) cơ khí cần nhẹ và không kẹt trục để servo (động cơ điều khiển theo góc quay) không quá tải.

## 3.32. Đánh giá chức năng điều khiển barrier (thanh chắn/barie)

Khối điều khiển barrier (thanh chắn/barie) hoạt động theo đúng nguyên tắc:

- Khi có lệnh mở, servo (động cơ điều khiển theo góc quay) nâng barrier (thanh chắn/barie) lên.
- Khi xe đi qua, cảm biến chuyển từ trạng thái có vật cản sang không có vật cản.
- Hệ thống chờ 2 giây sau khi cảm biến không còn phát hiện vật cản.
- Sau thời gian chờ, Arduino (bo mạch vi điều khiển) nhận lệnh đóng barrier (thanh chắn/barie).

Việc điều khiển servo (động cơ điều khiển theo góc quay) theo từng bước nhỏ giúp chuyển động barrier (thanh chắn/barie) mềm hơn so với việc quay ngay lập tức đến góc đích. Cơ chế chờ sau khi cảm biến hết vật cản giúp mô hình vận hành sát thực tế hơn.

## 3.33. Thiết kế đa luồng

![Hình 3.6. Cơ chế đa luồng trong hệ thống](hinh_bao_cao/hinh_3_5_da_luong.svg)

**Hình 3.6** mô tả cách tách các tác vụ có thời gian xử lý khác nhau ra nhiều luồng. Camera (thiết bị thu hình), AI (trí tuệ nhân tạo) và cảm biến chạy tách khỏi luồng giao diện để giao diện không bị treo khi nhận diện hoặc đọc thiết bị.

Hệ thống có nhiều tác vụ diễn ra đồng thời:

- Đọc camera (thiết bị thu hình) liên tục.
- Chạy AI (trí tuệ nhân tạo) nhận diện biển số.
- Đọc trạng thái cảm biến từ Arduino (bo mạch vi điều khiển).
- Cập nhật giao diện.
- Truy vấn cơ sở dữ liệu.

Nếu tất cả tác vụ chạy trên cùng một luồng, giao diện có thể bị treo khi AI (trí tuệ nhân tạo) xử lý lâu hoặc khi camera (thiết bị thu hình) chậm phản hồi. Vì vậy hệ thống sử dụng cách tổ chức đa luồng: camera, AI và cảm biến được xử lý tách khỏi luồng giao diện. Giao diện chỉ lấy trạng thái mới nhất để hiển thị định kỳ.

---

## 3.34. Kết quả giao diện và vận hành

Giao diện hệ thống hiển thị được các thành phần chính:

- Hình ảnh camera (thiết bị thu hình) cổng vào.
- Hình ảnh camera (thiết bị thu hình) cổng ra.
- Ảnh biển số sau xử lý của từng cổng.
- Chuỗi biển số nhận diện được.
- Số lượng xe hiện tại và sức chứa bãi.
- Chế độ thủ công/tự động.
- Trạng thái kết nối Arduino (bo mạch vi điều khiển).
- Danh sách biển số hợp lệ.
- Nhật ký sự kiện.

Trong quá trình thử nghiệm, hệ thống thực hiện được các chức năng:

- Bật và tắt từng camera (thiết bị thu hình).
- Chuyển camera (thiết bị thu hình) cho từng cổng.
- Nhận diện biển số ở cổng vào.
- Nhận diện biển số ở cổng ra.
- Thêm và xóa biển số hợp lệ.
- Tự động mở barrier (thanh chắn/barie) khi xe đủ điều kiện.
- Không mở barrier (thanh chắn/barie) khi biển số không hợp lệ.
- Không cho xe vào khi bãi đã đầy.
- Không cho xe ra nếu xe không có trong bãi.
- Đóng barrier (thanh chắn/barie) sau khi cảm biến không còn phát hiện vật cản trong 2 giây.

## 3.35. Đánh giá ưu điểm

Hệ thống đạt được các ưu điểm chính:

- Có đủ hai luồng cổng vào và cổng ra.
- Mỗi cổng có camera (thiết bị thu hình) và vùng hiển thị biển số riêng.
- Có kiểm tra biển số hợp lệ trước khi cho xe vào.
- Có kiểm tra xe trong bãi trước khi cho xe ra.
- Không xóa xe khỏi bãi trước khi xe thật sự ra khỏi vùng cổng.
- Có chế độ tự động và thủ công.
- Có giao diện trực quan, dễ quan sát trạng thái.
- Cơ sở dữ liệu được tổ chức rõ ràng.
- Giao tiếp Arduino (bo mạch vi điều khiển) đơn giản, dễ kiểm tra và phân tích lỗi khi ghép nối phần cứng.
- Cơ chế đóng barrier (thanh chắn/barie) có xét trạng thái cảm biến, tăng tính an toàn.

## 3.36. Hạn chế

Bên cạnh các kết quả đạt được, hệ thống vẫn còn một số hạn chế:

- Độ chính xác nhận diện phụ thuộc vào góc đặt camera (thiết bị thu hình) và ánh sáng môi trường.
- Nếu biển số bị đưa quá sát camera (thiết bị thu hình) hoặc bị cắt mất mép, kết quả nhận diện có thể sai.
- Chưa có chức năng lưu ảnh xe vào/ra thành hồ sơ.
- Chưa có chức năng tính tiền gửi xe.
- Chưa có tài khoản quản trị và phân quyền người dùng.
- Mô hình mới dừng ở quy mô đồ án, chưa đánh giá trong môi trường bãi xe thực tế ngoài trời.

## 3.37. Hướng phát triển

Trong tương lai, hệ thống có thể được phát triển theo các hướng sau:

- Bổ sung chức năng tính phí theo thời gian gửi xe.
- Lưu ảnh xe vào và ảnh xe ra để đối chiếu.
- Thêm chức năng xuất báo cáo lịch sử vào/ra.
- Xây dựng giao diện web hoặc ứng dụng quản lý từ xa.
- Tối ưu nhận diện trong điều kiện thiếu sáng, ngược sáng hoặc biển số bị nghiêng.
- Bổ sung cơ chế cảnh báo khi mất kết nối Arduino (bo mạch vi điều khiển) hoặc camera (thiết bị thu hình).
- Cải tiến mô hình phần cứng để barrier (thanh chắn/barie) chắc chắn và ổn định hơn.

## 3.38. Kết luận

Đề tài đã xây dựng được mô hình hệ thống bãi đỗ xe tự động có sự kết hợp giữa xử lý ảnh, trí tuệ nhân tạo, cơ sở dữ liệu, giao diện người dùng và điều khiển phần cứng. Hệ thống có thể nhận diện biển số ở cả cổng vào và cổng ra, kiểm tra dữ liệu trước khi mở barrier (thanh chắn/barie), đồng thời cập nhật trạng thái xe trong bãi sau khi xe ra khỏi cổng.

Kết quả thực nghiệm cho thấy phương pháp kết hợp YOLOv8 (mô hình phát hiện đối tượng phiên bản 8), PaddleOCR (bộ nhận dạng ký tự quang học) và hậu xử lý theo quy tắc biển số Việt Nam đạt độ chính xác tốt trong điều kiện mô hình được căn chỉnh phù hợp. Hệ thống đáp ứng được mục tiêu của đồ án và có thể tiếp tục mở rộng để tiệm cận một hệ thống bãi xe thông minh hoàn chỉnh hơn.

