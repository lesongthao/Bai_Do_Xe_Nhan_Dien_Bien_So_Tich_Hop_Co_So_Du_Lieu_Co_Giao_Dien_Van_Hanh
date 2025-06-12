<img src="https://iili.io/FfYJOas.jpg" alt="Demo IMG" style="max-width: 100%; height: auto;" />

# 🚗 Hệ thống Nhận diện Biển số xe Việt Nam (Vietnamese License Plate Recognition System)
# API Nhận diện Biển số xe Việt Nam (Backend) 🚘📸

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green?logo=fastapi)](https://fastapi.tiangolo.com/)

Đây là phần **Backend API** của hệ thống nhận diện biển số xe Việt Nam, được xây dựng bằng **Python** và **FastAPI**. API này chịu trách nhiệm nhận ảnh từ Client (ví dụ như ứng dụng WinForms), xử lý ảnh để phát hiện và nhận dạng biển số xe, sau đó trả kết quả về cho Client.

**Repository Frontend (WinForms):** [https://github.com/PhucDaizz/LicensePlateRecognitionVN-](https://github.com/PhucDaizz/LicensePlateRecognitionVN-)

---

## Mục lục

- [Chức năng chính](#chức-năng-chính)
- [Các File Chính](#các-file-chính)
- [Công nghệ sử dụng](#công-nghệ-sử-dụng)
- [Chuẩn bị môi trường (Prerequisites)](#chuẩn-bị-môi-trường-prerequisites)
- [Cài đặt](#cài-đặt)
- [Chạy API Server](#chạy-api-server)
- [Chạy Script Mô phỏng (visualize_steps.py)](#chạy-script-mô-phỏng-visualizestepspy)
- [Thành viên nhóm](#thành-viên-nhóm)
- [License](#license)

---

## Chức năng chính

- **Endpoint `/recognize` (HTTP POST):** Nhận file ảnh từ Client để xử lý.
- **Phát hiện biển số:** Sử dụng mô hình YOLOv8 (file `best.pt`) để phát hiện vùng biển số trong ảnh.
- **Tiền xử lý ảnh:** Áp dụng các kỹ thuật (grayscale, CLAHE, sharpening, adaptive thresholding) để cải thiện chất lượng ảnh vùng chứa biển số (ROI).
- **Nhận dạng ký tự:** Sử dụng EasyOCR để đọc và nhận dạng ký tự từ ảnh đã tiền xử lý.
- **Định dạng kết quả:** Chuẩn hóa chuỗi ký tự thành định dạng biển số xe Việt Nam hợp lệ.
- **Trả kết quả:** Gửi danh sách biển số nhận diện được dưới dạng JSON.

---

## Các File Chính

- **`main_api.py`:**
  - File chính của ứng dụng FastAPI.
  - Định nghĩa instance FastAPI (`app`) và các endpoint.
  - Khởi tạo lớp `PlateRecognizer` với các phương thức:
    - `__init__()`: Tải model YOLO và khởi tạo EasyOCR reader.
    - `preprocess_plate()`: Thực hiện các bước tiền xử lý ảnh ROI.
    - `format_vietnam_plate()`: Định dạng chuỗi ký tự thành biển số Việt Nam.
    - `process_image()`: Toàn bộ quy trình xử lý ảnh (nhận bytes, dự đoán, crop, tiền xử lý, OCR, định dạng).
  - Khởi chạy Uvicorn khi file được thực thi trực tiếp.

- **`best.pt`:**
  - File chứa trọng số đã được huấn luyện của mô hình YOLOv8 dùng để phát hiện vùng biển số xe.

- **`requirements.txt`:**
  - Danh sách các thư viện Python cần thiết và phiên bản của chúng để chạy dự án.

- **`visualize_steps.py`:**
  - Script mô phỏng và trực quan hóa các bước xử lý ảnh của Backend (từ YOLO detection đến tiền xử lý và OCR) trên một ảnh mẫu.
  - Script hiển thị các bước trung gian bằng OpenCV (chỉ dùng cho mục đích kiểm thử, không bắt buộc khi API hoạt động).

---

## Công nghệ sử dụng

- **Ngôn ngữ:** Python 3.x
- **Framework API:** FastAPI
- **Server ASGI:** Uvicorn
- **Object Detection:** YOLOv8 (qua thư viện `ultralytics`)
- **OCR:** EasyOCR
- **Xử lý ảnh:** OpenCV-Python (`cv2`), Pillow (`PIL`)
- **Thư viện khác:** Numpy, Regex (`re`), Logging, IO

---

## Chuẩn bị môi trường (Prerequisites)

- **Python (3.8+):** Tải và cài đặt từ [python.org](https://www.python.org/). Đảm bảo chọn "Add Python to PATH" khi cài đặt.
- **Pip:** Trình quản lý gói Python (đi kèm cùng Python).
- **Git:** Để clone repository.
- **(Tùy chọn)** Card đồ họa NVIDIA với CUDA và cuDNN được cài đặt đúng nếu bạn muốn chạy các thư viện như YOLO hay EasyOCR trên GPU (hiện tại code đang cấu hình chạy trên CPU).

---

## Cài đặt

1. **Clone Repository:**

    ```bash
    git clone https://github.com/PhucDaizz/LicensePlateRecognitionVNAPI.git
    cd LicensePlateRecognitionVNAPI
    ```

2. **(Khuyến nghị) Tạo và kích hoạt môi trường ảo:**

    ```bash
    python -m venv venv
    # Windows:
    .\venv\Scripts\activate
    # macOS/Linux:
    source venv/bin/activate
    ```

3. **Cài đặt các thư viện:**

    ```bash
    pip install -r requirements.txt
    ```

    *Lưu ý:* Đảm bảo file `requirements.txt` chứa tất cả các dependencies cần thiết (bao gồm cả `torch` và `torchvision` nếu cần cho `ultralytics` hoặc `easyocr`).

4. **Model YOLO:** Đảm bảo file `best.pt` nằm trong thư mục gốc của dự án.

5. **Model EasyOCR:** Lần chạy đầu tiên, EasyOCR sẽ tự động tải các model ngôn ngữ cần thiết (như `vi`, `en`) về (yêu cầu kết nối Internet).

---

## Chạy API Server

1. Mở Terminal hoặc Command Prompt trong thư mục gốc của dự án (`LicensePlateRecognitionVNAPI`).
2. Kích hoạt môi trường ảo (nếu đã tạo).
3. Chạy lệnh sau:

    ```bash
    uvicorn main_api:app --reload --host 0.0.0.0 --port 5000
    ```

- Sau khi khởi chạy, API sẽ sẵn sàng tại:  
  `http://localhost:5000` hoặc `http://<Địa-chỉ-IP-của-máy>:5000`
- Truy cập `http://localhost:5000/docs` để xem tài liệu Swagger UI và thử nghiệm endpoint `/recognize`.

---

## Chạy Script Mô phỏng (visualize_steps.py)

Script này dùng để kiểm tra và trực quan hóa các bước xử lý ảnh, không cần thiết để API hoạt động.

1. Mở Terminal/Command Prompt trong thư mục dự án.
2. Kích hoạt môi trường ảo.
3. Chỉnh sửa biến `IMAGE_PATH` trong file `visualize_steps.py` thành đường dẫn đến ảnh mẫu bạn muốn kiểm tra.
4. Chạy script:

    ```bash
    python visualize_steps.py
    ```

5. Các cửa sổ OpenCV sẽ hiển thị kết quả của từng bước. Nhấn phím bất kỳ trên cửa sổ ảnh để chuyển sang bước tiếp theo.

---

## Thành viên nhóm

| STT | MSSV       | Họ và tên              |
|-----|------------|------------------------|
| 1   | 2251120339 | Nguyễn Phúc Đại        |
| 2   | 2251120340 | Nguyễn Cao Thành Đạt   |
| 3   | 2251120382 | Trần Văn Tài           |
| 4   | 2251120277 | Huỳnh Long Bảo Duy     |

---

## License

Dự án được sử dụng cho mục đích học tập và nghiên cứu. Mọi hành vi sao chép với mục đích thương mại cần có sự cho phép của nhóm phát triển.

