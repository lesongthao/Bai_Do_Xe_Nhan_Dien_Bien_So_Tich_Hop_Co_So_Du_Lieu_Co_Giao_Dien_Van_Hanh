# Định Hướng Lại Đồ Án: Lấy Module Nhận Diện Biển Số Làm Chủ Đạo

## 1. Vấn đề hiện tại

Đồ án hiện tại đang ôm quá nhiều khối cùng lúc:

- Giao diện Tkinter
- Điều khiển bãi xe
- Giao tiếp Arduino
- Cảm biến vào/ra
- Nhận diện biển số
- Cơ sở dữ liệu whitelist
- Logic điều khiển barie

Nếu giữ toàn bộ các khối này làm trọng tâm, phần AI nhận diện biển số sẽ bị mỏng về mặt học thuật. Điều cô giáo góp ý là đúng: đồ án cần có **một lõi nghiên cứu chính**, và với đề tài này lõi hợp lý nhất là **nhận diện biển số xe**.

## 2. Hướng chuyển đề tài

Thay vì xem hệ thống bãi xe là sản phẩm chính, nên đổi góc nhìn:

**Đề tài chính:**
"Nghiên cứu và xây dựng mô hình nhận diện biển số xe theo pipeline nhiều giai đoạn"

**Hệ thống bãi xe tự động:**
chỉ nên giữ vai trò **môi trường minh họa ứng dụng**.

Nói ngắn gọn:

- Phần chính để viết báo cáo, thuyết trình, đánh giá: module nhận diện biển số
- Phần giao diện bãi xe, Arduino, barie: phần demo ứng dụng

## 3. Cấu trúc đồ án nên có

Đồ án nên được tách thành 4 bài toán con rõ ràng:

1. Phát hiện vùng chứa biển số trong ảnh xe
2. Tách ký tự từ vùng biển số
3. Nhận dạng từng ký tự
4. Đánh giá định lượng bằng tập train/test

Đây là hướng "bài bản từng bước" mà cô giáo đang yêu cầu.

## 4. Pipeline kỹ thuật nên theo

### Bước 1: Chuẩn bị dữ liệu

Chuẩn bị tối thiểu một bộ dữ liệu có nhãn rõ ràng:

- Ảnh xe hoặc ảnh chứa biển số
- Tọa độ vùng biển số
- Ảnh biển số đã crop
- Ảnh từng ký tự sau khi tách
- Nhãn ký tự tương ứng (`0-9`, `A-Z`)

Khuyến nghị tối thiểu cho bản đồ án:

- 200 mẫu để đánh giá
- Chia train/test rõ ràng
- Nếu đủ thời gian: train/val/test

Ví dụ chia:

- `train`: 140 mẫu
- `val`: 20 mẫu
- `test`: 40 mẫu

Hoặc nếu cô yêu cầu đúng 200 mẫu test/đánh giá thì cần ghi rõ:

- 200 ảnh tổng để kiểm thử cuối
- tập train riêng lớn hơn nếu có thể

Điểm này phải chốt sớm với cô: **200 mẫu là toàn bộ dữ liệu hay chỉ là tập test**.

### Bước 2: Phát hiện vùng biển số

Mục tiêu:

- nhận ảnh xe đầu vào
- trả về bounding box vùng biển số

Hướng làm phù hợp:

- dùng YOLO như hiện tại
- gán nhãn bounding box cho biển số
- train riêng bài toán detect

Đầu ra cần báo cáo:

- số lượng ảnh train/test
- loss trong quá trình train
- precision, recall, mAP
- một số ảnh minh họa detect đúng/sai

### Bước 3: Tách ký tự từ biển số

Mục tiêu:

- nhận ảnh biển số đã crop
- tách từng ký tự riêng lẻ

Có 2 hướng:

1. Cách cổ điển:
   - grayscale
   - tăng tương phản
   - threshold
   - morphology
   - tìm contour
   - lọc contour theo kích thước/tỉ lệ
   - sắp xếp ký tự từ trái sang phải hoặc theo 2 dòng

2. Cách học sâu:
   - detect từng ký tự bằng object detection

Với đồ án tốt nghiệp, hướng nên đi trước là **cách cổ điển**, vì:

- dễ giải thích
- thể hiện rõ từng bước xử lý ảnh
- dễ minh họa bằng hình ảnh trung gian
- phù hợp yêu cầu "phân tách vùng chứa biển số rồi phân tách ký tự"

Đầu ra cần báo cáo:

- số ký tự tách đúng / sai
- các trường hợp lỗi: dính ký tự, mất ký tự, nhiễu nền, biển 2 dòng

### Bước 4: Nhận dạng từng ký tự

Mục tiêu:

- nhận ảnh 1 ký tự
- dự đoán ký tự đó là gì

Hướng làm:

- xây bộ dữ liệu ảnh ký tự
- mỗi ảnh gắn nhãn một lớp trong `0-9, A-Z`
- train bộ phân loại ký tự

Mô hình có thể chọn:

- CNN đơn giản tự xây bằng Keras/PyTorch
- hoặc một mô hình nhỏ, dễ giải thích

Không nên phụ thuộc hoàn toàn vào OCR đóng gói sẵn nếu cô yêu cầu quy trình học thuật rõ ràng. PaddleOCR hiện tại phù hợp cho demo kỹ thuật, nhưng không phải phương án tốt nhất nếu cần chứng minh từng bước của bài toán.

Đầu ra cần báo cáo:

- accuracy
- precision / recall / F1 nếu cần
- confusion matrix
- các cặp dễ nhầm như `0/O`, `1/I`, `5/S`, `8/B`, `2/Z`

### Bước 5: Ghép lại thành biển số hoàn chỉnh

Sau khi có các ký tự đã nhận dạng:

- sắp xếp theo vị trí
- ghép thành chuỗi biển số
- nếu biển 2 dòng thì ghép theo quy tắc dòng trên, dòng dưới
- áp dụng hậu xử lý theo quy tắc biển số Việt Nam

Ví dụ:

- kiểm tra độ dài hợp lệ
- vị trí đầu là số tỉnh
- vị trí series là chữ
- vị trí cuối là số

Phần này chính là nơi có thể tái sử dụng heuristics hiện tại trong `nhan_dien_bien_so.py`.

## 5. Nên giữ lại gì từ dự án hiện tại

Không nên bỏ toàn bộ repo. Nên giữ lại các phần có giá trị:

- `nhan_dien_bien_so.py`: giữ ý tưởng pipeline và hậu xử lý
- `mo_hinh/bien_so_yolo.pt`: có thể tiếp tục dùng làm baseline
- notebook Colab hiện có: tận dụng để train thử nghiệm
- tài liệu phân tích hiện có: dùng làm nền rồi viết lại theo scope mới

Các phần nên hạ vai trò xuống phụ trợ:

- `giao_dien_chinh.py`
- `dieu_khien_he_thong.py`
- `giao_tiep_arduino.py`
- firmware Arduino
- SQLite whitelist

## 6. Nên bỏ bớt gì trong phần báo cáo

Nếu theo scope mới, báo cáo không nên dành quá nhiều trang cho:

- barie mở/đóng
- cảm biến LM393
- giao diện Tkinter
- whitelist xe hợp lệ
- logic bãi xe vào/ra

Các phần này chỉ nên viết ngắn:

- mục ứng dụng thực tế
- mục demo tích hợp
- mục mở rộng hệ thống

Phần phải viết sâu:

- dữ liệu
- gán nhãn
- tiền xử lý
- tách ký tự
- mô hình nhận dạng ký tự
- đánh giá định lượng

## 7. Cấu trúc repo nên chuyển dần về

Một cấu trúc dễ viết báo cáo và dễ code hơn:

```text
du_an_nhan_dien_bien_so/
├── data/
│   ├── raw/
│   ├── plates/
│   ├── chars/
│   ├── labels/
│   └── splits/
├── notebooks/
│   ├── 01_khao_sat_du_lieu.ipynb
│   ├── 02_train_detect_bien_so.ipynb
│   ├── 03_tach_ky_tu.ipynb
│   ├── 04_train_nhan_dang_ky_tu.ipynb
│   └── 05_danh_gia_he_thong.ipynb
├── src/
│   ├── detect_plate.py
│   ├── segment_characters.py
│   ├── recognize_characters.py
│   ├── assemble_plate.py
│   └── evaluate.py
├── models/
├── results/
│   ├── detect/
│   ├── segment/
│   ├── classify/
│   └── report_figures/
├── app/
│   └── demo_app.py
└── docs/
    └── bao_cao_do_an.md
```

## 8. Kế hoạch làm lại theo từng giai đoạn

### Giai đoạn 1: Chốt phạm vi

Mục tiêu:

- xác định đề tài chính là nhận diện biển số
- xem bãi xe là phần minh họa
- chốt yêu cầu với cô về dữ liệu và chỉ số đánh giá

Cần hỏi rõ:

- 200 mẫu là toàn bộ dữ liệu hay chỉ tập test?
- cô muốn train từ đầu hay được dùng pretrain + fine-tune?
- ma trận nhầm lẫn cần ở mức ký tự hay mức biển số hoàn chỉnh?

### Giai đoạn 2: Làm bộ dữ liệu

Mục tiêu:

- gom ảnh
- chia tập
- đặt tên chuẩn
- lưu nhãn rõ ràng

Kết quả cần có:

- file danh sách train/test
- bảng thống kê số ảnh
- vài ảnh minh họa dữ liệu

### Giai đoạn 3: Hoàn thiện detect biển số

Mục tiêu:

- train hoặc fine-tune model detect
- đánh giá khả năng cắt đúng vùng biển số

Kết quả cần có:

- biểu đồ train
- mAP
- ảnh detect đúng/sai

### Giai đoạn 4: Tách ký tự

Mục tiêu:

- xây module `segment_characters.py`
- lưu được từng ảnh ký tự

Kết quả cần có:

- hình minh họa từng bước xử lý
- tỉ lệ tách đúng
- phân tích lỗi

### Giai đoạn 5: Train nhận dạng ký tự

Mục tiêu:

- tạo tập dữ liệu ký tự
- train classifier
- sinh confusion matrix

Kết quả cần có:

- accuracy
- confusion matrix
- top lỗi nhầm phổ biến

### Giai đoạn 6: Đánh giá end-to-end

Mục tiêu:

- ghép toàn bộ pipeline
- đo độ chính xác cuối cùng trên biển số hoàn chỉnh

Chỉ số nên có:

- độ chính xác phát hiện biển số
- độ chính xác tách ký tự
- độ chính xác nhận dạng ký tự
- độ chính xác biển số hoàn chỉnh

## 9. Định hướng sửa code hiện tại

Thay vì tiếp tục đắp thêm vào `nhan_dien_bien_so.py`, nên tách file này thành các module nhỏ:

- `detect_plate.py`
- `segment_characters.py`
- `recognize_characters.py`
- `postprocess_plate.py`

Lợi ích:

- đúng với yêu cầu học thuật
- dễ test từng khâu
- dễ trình bày báo cáo
- dễ sinh hình minh họa trung gian

Pipeline mới nên là:

```text
Ảnh xe
-> detect vùng biển số
-> crop biển số
-> tiền xử lý
-> tách ký tự
-> nhận dạng từng ký tự
-> ghép biển số
-> đánh giá
```

## 10. Kết luận thực tế

Nếu mục tiêu là qua đồ án với chất lượng tốt, thì không nên cố bảo vệ toàn bộ hệ thống bãi xe như phần cốt lõi.

Cách an toàn và đúng hướng hơn là:

- thu gọn đề tài về nhận diện biển số
- làm rõ pipeline nhiều giai đoạn
- có dữ liệu train/test
- có đánh giá định lượng
- có confusion matrix và phân tích lỗi
- giữ phần bãi xe như demo ứng dụng sau cùng

Đây là hướng vừa đúng góp ý của cô, vừa tận dụng được phần anh đã làm thay vì bỏ đi toàn bộ.
