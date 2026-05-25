# HƯỚNG DẪN TỰ TRAIN MÔ HÌNH YOLOV8 TRÊN GOOGLE COLAB

Việc train mô hình AI yêu cầu máy tính phải có Card đồ họa (GPU) mạnh. Do đó, chúng ta sẽ "mượn" máy chủ miễn phí của Google để làm việc này. Cuối quá trình, bạn sẽ nhận được file `best.pt` của riêng bạn và các hình ảnh **Biểu đồ Loss** để dán vào báo cáo đồ án.

## Bước 1: Lấy đoạn code tải Dataset chuẩn (Biển số xe Việt Nam)
Để AI học được, bạn cần một bộ ảnh biển số xe máy và ô tô của Việt Nam (biển trắng, biển vàng, biển xanh) đã được vẽ sẵn khung chữ nhật.
1. Truy cập vào trang web: [Roboflow Universe - VN License Plate](https://universe.roboflow.com/search?q=vietnamese%20license%20plate)
2. Hãy chọn dự án có tên **"Vietnamese License Plate"** hoặc **"VN-License-Plate"** có số lượng ảnh lớn (từ **1000 - 3000 ảnh**). Đừng chọn các dataset quá ít ảnh vì train sẽ không chính xác.
3. Bấm vào nút **Download Dataset** ở góc trên bên phải.
4. Chọn Format (Định dạng) là **YOLOv8**.
5. Đánh dấu chọn **"Show download code"** và bấm Continue.
6. Trang web sẽ hiện ra một đoạn code Python (chứa API Key bí mật của bạn). Hãy copy toàn bộ đoạn code đó để dành cho Bước 3.

## Bước 2: Khởi tạo máy chủ Google Colab
1. Truy cập: [Google Colab](https://colab.research.google.com/) và đăng nhập bằng tài khoản Gmail của bạn.
2. Bấm **Tạo Sổ tay mới (New Notebook)**.
3. Ở menu trên cùng, chọn **Thời gian chạy (Runtime) -> Thay đổi loại thời gian chạy (Change runtime type)**.
4. Ở phần "Phần cứng", chọn **T4 GPU** và bấm Lưu. (Đây là card đồ họa xịn của Google cấp cho bạn xài tạm).

## Bước 3: Chạy code Training
Trong Colab, giao diện bao gồm các khối code (Cell). Bạn chỉ cần dán code vào từng ô và bấm nút **Play** (nút tam giác) để chạy lần lượt từ trên xuống dưới.

### Ô code 1: Cài đặt thư viện YOLOv8
Dán đoạn này vào ô đầu tiên và bấm Play:
```bash
!pip install ultralytics
import ultralytics
ultralytics.checks()
```

### Ô code 2: Tải Dataset
Bấm dấu **+ Mã (+ Code)** để thêm ô thứ 2. Dán đoạn lệnh `curl` mà bạn vừa lấy được vào đây. (Nhớ thêm dấu chấm than `!` ở đầu để Colab hiểu đây là lệnh hệ thống nhé).
*(Đoạn lệnh sẽ trông như thế này)*:
```bash
!curl -L "https://universe.roboflow.com/ds/uByG0YJ7aO?key=BfQmPsB2hM" > roboflow.zip; unzip roboflow.zip; rm roboflow.zip
```

### Ô code 3: Tiến hành Huấn Luyện (Train) và Lưu Lên Drive
Sau khi tải xong dataset, thêm ô code số 3. Dán đoạn mã dưới đây vào và bấm Play. Đoạn code này được cài đặt để **LƯU KẾT QUẢ THẲNG VÀO GOOGLE DRIVE CỦA BẠN**.
```python
from ultralytics import YOLO
import glob

# 1. Tự động quét tìm đường dẫn file data.yaml
try:
    data_path = glob.glob('/content/**/data.yaml', recursive=True)[0]
    print(f"✅ Đã tìm thấy file Dataset tại: {data_path}")
except IndexError:
    print("❌ LỖI: Không tìm thấy file data.yaml! Hãy kiểm tra lại phần tải ảnh.")
    data_path = ''

# 2. Khởi tạo mô hình
model = YOLO('yolov8n.pt') 

# 3. Bắt đầu quá trình huấn luyện
if data_path:
    results = model.train(
        data=data_path,            
        epochs=100,                
        imgsz=640,                 
        batch=16,                  
        optimizer='auto',          
        lr0=0.01,                  
        patience=50,               
        device=0,                  
        project='/content/drive/MyDrive/Do_An_Tot_Nghiep',  # LƯU KẾT QUẢ VÀO THƯ MỤC NÀY TRÊN DRIVE
        name='NhanDienBienSo_YOLOv8'                        # Tên thư mục con chứa kết quả
    )
```

## Bước 4: Thu Hoạch Thành Quả
Quá trình Training kết thúc! Toàn bộ file trọng số (model `best.pt`) và các biểu đồ mAP đã được hệ thống lưu thẳng vào tài khoản Google Drive của bạn.

**Bạn chỉ cần mở trang Google Drive (bằng trình duyệt hoặc điện thoại), tìm thư mục `Do_An_Tot_Nghiep` -> `NhanDienBienSo_YOLOv8`. Tất cả kho báu của bạn đều nằm an toàn trong đó!** Tải file `best.pt` trong thư mục `weights` về bỏ vào thư mục code là xong!

## Bước 5: Tích hợp vào đồ án
Sau khi tải file `ket_qua_yolo.zip` về máy và giải nén ra, bạn sẽ thấy rất nhiều thứ tuyệt vời:
1. File **`weights/best.pt`**: Đây chính là trí tuệ nhân tạo của bạn! Hãy đổi tên nó thành `bien_so_yolo.pt` và chép đè vào thư mục `mo_hinh/` trong đồ án của bạn.
2. File **`results.png`**: Biểu đồ Loss giảm dần (Màu đẹp, độ phân giải cao).
3. File **`confusion_matrix.png`**: Ma trận nhầm lẫn của mô hình nhận diện khung chữ nhật.

Chỉ cần copy 2 file hình ảnh đó dán vào File Word đồ án, cô giáo sẽ không bao giờ hỏi vặn bạn mô hình ở đâu ra nữa!
