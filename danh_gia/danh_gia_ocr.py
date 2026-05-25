import os
import time
import difflib
import subprocess
import sys

# Tự động cài đặt thư viện để vẽ biểu đồ nếu chưa có
def install_libraries():
    required = {'matplotlib', 'seaborn', 'scikit-learn'}
    installed = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze']).decode('utf-8')
    missing = [pkg for pkg in required if pkg not in installed]
    if missing:
        print(f"Đang cài đặt các thư viện cần thiết để vẽ biểu đồ: {missing}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])
        print("Cài đặt xong!")

install_libraries()

import cv2
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report
sys.path.insert(0, os.path.abspath('..'))
from nhan_dien_bien_so import NhanDienBienSo

# ==========================================
# CẤU HÌNH
# ==========================================
THU_MOC_ANH = "dataset_test"
FILE_LABEL = "labels.txt"

def tao_thu_muc_mau():
    if not os.path.exists(THU_MOC_ANH):
        os.makedirs(THU_MOC_ANH)
    if not os.path.exists(FILE_LABEL):
        with open(FILE_LABEL, 'w', encoding='utf-8') as f:
            f.write("# Hãy điền tên ảnh và đáp án vào đây, cách nhau bằng dấu phẩy\n")
            f.write("# Ví dụ: anh_001.jpg, 51H59531\n")
        print(f"Đã tạo thư mục '{THU_MOC_ANH}' và file '{FILE_LABEL}'.")
        print("VUI LÒNG COPY 200 ẢNH VÀO THƯ MỤC VÀ ĐIỀN ĐÁP ÁN VÀO FILE TXT TRƯỚC KHI CHẠY TIẾP.")
        sys.exit()

def plot_confusion_matrix(y_true, y_pred):
    """Vẽ ma trận nhầm lẫn cấp độ ký tự"""
    # Lấy danh sách tất cả các ký tự xuất hiện (A-Z, 0-9)
    labels = sorted(list(set(y_true) | set(y_pred)))
    
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    
    plt.figure(figsize=(14, 10))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
    plt.title('Ma Trận Nhầm Lẫn (Confusion Matrix) Cấp Độ Ký Tự', fontsize=16, fontweight='bold')
    plt.ylabel('Ký Tự Thực Tế (Ground Truth)', fontsize=12)
    plt.xlabel('Ký Tự Nhận Diện Được (Predicted)', fontsize=12)
    plt.tight_layout()
    plt.savefig('confusion_matrix.png', dpi=300)
    print("\n✅ Đã lưu biểu đồ vào file 'confusion_matrix.png'!")

def main():
    tao_thu_muc_mau()
    
    print("Đang tải mô hình AI...")
    ai_module = NhanDienBienSo()
    
    # Đọc đáp án
    y_true_chars = []
    y_pred_chars = []
    
    so_anh_dung_hoan_toan = 0
    tong_so_anh = 0
    
    with open(FILE_LABEL, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        parts = line.split(',')
        if len(parts) != 2:
            continue
            
        img_name = parts[0].strip()
        true_label = parts[1].strip().upper()
        
        img_path = os.path.join(THU_MOC_ANH, img_name)
        if not os.path.exists(img_path):
            print(f"Không tìm thấy ảnh: {img_path}")
            continue
            
        # Đọc ảnh và nhận diện
        anh = cv2.imread(img_path)
        pred_label, _ = ai_module.nhan_dien(anh)
        
        if pred_label is None:
            pred_label = ""
        else:
            pred_label = pred_label
            
        tong_so_anh += 1
        if true_label == pred_label:
            so_anh_dung_hoan_toan += 1
            print(f"[{tong_so_anh}] {img_name} -> Nhận diện ĐÚNG: {true_label}")
        else:
            print(f"[{tong_so_anh}] {img_name} -> SAI | Thực tế: {true_label} | Nhận diện: {pred_label}")
            
        # Tách từng ký tự để làm Confusion Matrix
        # Sử dụng SequenceMatcher để map các ký tự giống/khác nhau
        matcher = difflib.SequenceMatcher(None, true_label, pred_label)
        for opcode, i1, i2, j1, j2 in matcher.get_opcodes():
            if opcode == 'equal':
                for k in range(i2 - i1):
                    y_true_chars.append(true_label[i1+k])
                    y_pred_chars.append(pred_label[j1+k])
            elif opcode == 'replace':
                length = min(i2-i1, j2-j1)
                for k in range(length):
                    y_true_chars.append(true_label[i1+k])
                    y_pred_chars.append(pred_label[j1+k])

    if tong_so_anh == 0:
        print("Chưa có dữ liệu test nào!")
        return
        
    print("\n================ TỔNG KẾT ================")
    print(f"Tổng số biển số đã Test: {tong_so_anh}")
    print(f"Số biển đọc đúng hoàn toàn 100%: {so_anh_dung_hoan_toan}")
    print(f"Độ chính xác cấp độ Biển số (Sequence Accuracy): {(so_anh_dung_hoan_toan/tong_so_anh)*100:.2f}%")
    
    so_ky_tu_dung = sum(1 for t, p in zip(y_true_chars, y_pred_chars) if t == p)
    tong_ky_tu = len(y_true_chars)
    if tong_ky_tu > 0:
        print(f"Độ chính xác cấp độ Ký tự (Character Accuracy): {(so_ky_tu_dung/tong_ky_tu)*100:.2f}%")
        
        print("\n================ BÁO CÁO PHÂN LOẠI (CLASSIFICATION REPORT) ================")
        # Lấy danh sách các nhãn xuất hiện thực tế
        labels = sorted(list(set(y_true_chars) | set(y_pred_chars)))
        report = classification_report(y_true_chars, y_pred_chars, labels=labels, zero_division=0)
        print(report)
        
        # Lưu report ra file text để copy vào báo cáo Word
        with open("classification_report.txt", "w", encoding="utf-8") as f:
            f.write(report)
        print("Đã lưu Classification Report ra file 'classification_report.txt'")
        
        plot_confusion_matrix(y_true_chars, y_pred_chars)

if __name__ == "__main__":
    main()
