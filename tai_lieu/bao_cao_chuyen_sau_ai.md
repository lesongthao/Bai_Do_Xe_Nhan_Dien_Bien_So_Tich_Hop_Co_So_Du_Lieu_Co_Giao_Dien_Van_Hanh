# BÁO CÁO CHUYÊN SÂU: LÝ THUYẾT VÀ KIẾN TRÚC MÔ HÌNH TRÍ TUỆ NHÂN TẠO

*(Đoạn văn bản này được thiết kế để bạn chèn vào **Chương 2 (Cơ sở lý thuyết)** và **Chương 3 (Xây dựng thuật toán)** trong quyển báo cáo đồ án Word, sử dụng ngôn ngữ chuẩn học thuật).*

---

## 1. Phân tách vùng chứa biển số bằng mạng nơ-ron YOLOv8

Để trích xuất chính xác vị trí của biển số xe trên khung hình tổng thể, đề tài ứng dụng kiến trúc mạng nơ-ron chập (CNN) **YOLOv8** (You Only Look Once phiên bản 8). YOLOv8 là đại diện tiên tiến nhất thuộc họ mạng phát hiện vật thể một giai đoạn (Single-stage Object Detector).

### 1.1 Kiến trúc cốt lõi của YOLOv8
Kiến trúc của YOLOv8 được chia thành 3 phần chính:
- **Backbone (Mạng xương sống):** Sử dụng cấu trúc CSPNet (Cross Stage Partial Network) cải tiến để trích xuất đặc trưng (Feature Extraction) từ ảnh đầu vào. Backbone có khả năng nắm bắt từ các chi tiết hình học đơn giản (cạnh, góc của biển số) đến các cấu trúc phức tạp (bối cảnh đuôi xe, đầu xe) với chi phí tính toán thấp.
- **Neck (Cổ mạng):** Sử dụng cấu trúc PANet (Path Aggregation Network), giúp kết hợp các đặc trưng ở nhiều độ phân giải khác nhau. Điều này cực kỳ quan trọng đối với đồ án, giúp mạng nhận diện được biển số bất kể xe đậu gần (biển số lớn) hay đậu xa (biển số nhỏ) so với camera.
- **Head (Đầu ra):** Điểm khác biệt lớn nhất của YOLOv8 so với các thế hệ trước là kiến trúc **Anchor-Free** (Không sử dụng hộp neo lưới định trước) và **Decoupled Head** (Tách rời đầu dự đoán). Nó tách biệt việc dự đoán tọa độ khung bounding-box (Box Regression) và dự đoán nhãn lớp (Classification). Cơ chế này giúp giảm lượng tham số tính toán và bám sát chính xác vào các vật thể nhỏ, hẹp như biển số xe.

### 1.2 Quá trình thực thi (Inference) tại đồ án
- Ảnh màu từ camera được reshape về kích thước `320x320` pixel để tối ưu tốc độ xử lý trên CPU.
- Mạng nơ-ron tiến hành lan truyền tiến (forward pass) và trả về một ma trận chứa tọa độ `[x_min, y_min, x_max, y_max]` cùng với điểm tự tin (Confidence Score).
- Hệ thống áp dụng thuật toán **NMS (Non-Maximum Suppression)** để loại bỏ các hộp dự đoán trùng lặp, giữ lại vùng Bounding Box có điểm tự tin cao nhất và tiến hành cắt (crop) khung ảnh nhỏ chỉ chứa biển số để truyền sang giai đoạn hai.

---

## 2. Nhận dạng ký tự quang học với kiến trúc CRNN và hàm suy hao CTC

Trong xử lý ảnh truyền thống, để đọc được chữ, người ta bắt buộc phải sử dụng các thuật toán xử lý hình thái học (Morphological), vẽ các đường chiếu ngang/dọc (Projection Profile) để cắt rời từng ký tự ra thành các ảnh con (Character Segmentation), sau đó mới đem đi nhận dạng. Phương pháp truyền thống này rất mỏng manh và dễ thất bại nếu biển số bị ngược sáng, chói lóa đèn pha, ốc vít che khuất hoặc các chữ số viết dính liền vào nhau.

Để khắc phục nhược điểm này và nâng cao tính học thuật, đề tài sử dụng phương pháp **Phân tách ký tự ngầm (Implicit Segmentation)** thông qua kiến trúc mô hình **CRNN (Convolutional Recurrent Neural Network)** kết hợp hàm suy hao **CTC (Connectionist Temporal Classification)** của engine PaddleOCR.

### 2.1 Mạng trích xuất đặc trưng hình ảnh (CNN)
Ảnh biển số sau khi được YOLOv8 cắt ra sẽ được đẩy qua một mạng nơ-ron chập (như MobileNetV3 hoặc ResNet). Lớp CNN này đóng vai trò trích xuất đặc trưng (Feature Maps). Nó biến đổi bức ảnh 2 chiều thành một chuỗi các khối đặc trưng tuần tự (Feature Sequence) dọc theo chiều ngang của biển số.

### 2.2 Mạng học ngữ cảnh tuần tự (RNN / BiLSTM)
Vì các chữ số và chữ cái trên biển số có mối quan hệ ngữ cảnh tuyến tính từ trái qua phải, chuỗi đặc trưng ngang từ mạng CNN được đưa vào mạng nơ-ron hồi quy hai chiều **BiLSTM (Bidirectional Long Short-Term Memory)**. 
Mạng BiLSTM có khả năng "ghi nhớ" ngữ cảnh cả chiều xuôi và chiều ngược. Ví dụ, nếu phía trước là mã tỉnh "51" thì hệ thống có thể phán đoán ký tự tiếp theo có xác suất cao là một Chữ cái (A-Z) thay vì một con số. Điều này giúp sửa sai đáng kể đối với các ký tự bị mờ.

### 2.3 Quá trình "Phân tách ngầm" bằng CTC Loss
Đầu ra của mạng BiLSTM là một ma trận xác suất dự đoán các ký tự tại **mỗi một bước thời gian (time-step)** trên chiều ngang của ảnh. Do bề ngang của ảnh lớn hơn số lượng ký tự thực tế (ví dụ: ảnh phân bố làm 24 bước thời gian, nhưng biển số chỉ có 8 ký tự), đầu ra sẽ có rất nhiều ký tự trùng lặp liên tiếp hoặc khoảng trắng rỗng (Blank). Ví dụ: `555_11_H__55_999_55_3_11`.

Hàm **CTC (Connectionist Temporal Classification)** đóng vai trò là một thuật toán giải mã (Decoding) tuyệt vời. Nó hoạt động theo 2 quy tắc:
1. Gộp các ký tự giống nhau đứng liền kề lại thành một ký tự duy nhất (VD: `555` -> `5`).
2. Loại bỏ các khoảng trắng rỗng (Blank `_`).

Kết quả cuối cùng thu được là chuỗi gốc: `51H59531`. 

**Bình luận khoa học:** Nhờ cơ chế giải mã đường dẫn của CTC, mạng nơ-ron có thể gán nhãn cho một chuỗi hình ảnh mà **không cần ranh giới phân mảnh (alignment/segmentation boundaries)** vật lý. Đây chính là bước tiến lớn của AI, giải quyết triệt để yêu cầu "phân tách ký tự" một cách thanh lịch bằng toán học thay vì cắt ảnh thủ công thô sơ.

---

## 3. Hệ thống Hậu xử lý (Heuristics Post-Processing)

Mặc dù CRNN + CTC rất mạnh mẽ, sự tương đồng về hình dáng giữa một số chữ cái và con số (đặc biệt trong font chữ biển số giao thông) vẫn có thể gây ra sai số. Theo đánh giá thực nghiệm sơ bộ, mô hình dễ nhầm lẫn giữa: `8` và `B`, `5` và `S`, `0` và `O/D`.

Để triệt tiêu sai số này, đề tài xây dựng một bộ luật hậu xử lý (Rule-based Heuristics) dựa trên **Thông tư quy định về biển số xe cơ giới của Việt Nam**. Chuỗi ký tự (mảng Index từ 0 đến N) sẽ bị ép kiểu bắt buộc:
- **Index 0, 1 (Mã vùng):** Ép bắt buộc kiểu Số (Integer). Nếu OCR đọc là `S1`, hệ thống tự động sửa thành `51`.
- **Index 2 (Seri 1):** Ép bắt buộc kiểu Chữ cái (Char). Nếu OCR đọc là `8`, hệ thống tự động sửa thành `B`.
- Phân biệt độ dài chuỗi: Nếu chuỗi >= 9 ký tự và Index 3 là Chữ, hệ thống nhận dạng đây là Xe máy (2 seri chữ), Index thứ 4 trở đi bị ép thành Số. Còn lại là Ô tô, Index thứ 3 trở đi bị ép thành Số.

Sự kết hợp giữa Sức mạnh của Deep Learning (YOLO + CRNN) và Logic định dạng cứng (Heuristics) tạo nên một Pipeline Nhận diện khép kín có độ tin cậy cực cao trong thực tế.
