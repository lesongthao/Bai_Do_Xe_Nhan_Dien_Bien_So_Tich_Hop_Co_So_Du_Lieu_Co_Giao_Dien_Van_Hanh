"""
Script cat bien so bang YOLO tu anh test Roboflow,
hien thi cho nguoi dung go dap an.
Ket qua luu vao dataset_test/ va labels.txt
"""

import os
import sys
import cv2

# --- CAU HINH ---
THU_MUC_ANH_GOC = r"C:\Users\Admin\Downloads\vietnamese license plate.v1i.yolov8\test\images"
THU_MUC_TEST = "dataset_test"
FILE_LABEL = "labels.txt"
SO_ANH_CAN = 200


def tim_anh(thu_muc):
    """Tim tat ca file anh trong thu muc."""
    anh_list = []
    for f in sorted(os.listdir(thu_muc)):
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
            anh_list.append(os.path.join(thu_muc, f))
    return anh_list


def main():
    if not os.path.exists(THU_MUC_ANH_GOC):
        print(f"Khong tim thay thu muc anh: {THU_MUC_ANH_GOC}")
        sys.exit(1)

    anh_paths = tim_anh(THU_MUC_ANH_GOC)
    print(f"Tim thay {len(anh_paths)} anh trong thu muc test.")

    # Load YOLO
    print("Dang tai YOLO model...")
    from ultralytics import YOLO
    model = YOLO(os.path.join("..", "mo_hinh", "bien_so_yolo.pt"))
    print("YOLO OK!")

    # Tao thu muc output
    os.makedirs(THU_MUC_TEST, exist_ok=True)

    # Doc labels cu (neu co) de tiep tuc
    da_gan = {}
    if os.path.exists(FILE_LABEL):
        with open(FILE_LABEL, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(",", 1)
                if len(parts) == 2:
                    da_gan[parts[0].strip()] = parts[1].strip()

    print(f"Da co {len(da_gan)} anh da gan nhan truoc do.")
    print("=" * 50)
    print("HUONG DAN:")
    print("  - Nhin anh bien so hien len, go DUNG bien so")
    print("  - Bam Enter de xac nhan")
    print("  - Go 'skip' de bo qua anh khong ro")
    print("  - Go 'quit' de dung lai (du lieu da luu)")
    print("=" * 50)

    dem = len(da_gan)
    bo_qua = 0

    for i, anh_path in enumerate(anh_paths):
        if dem >= SO_ANH_CAN:
            break

        ten_file = f"test_{i+1:04d}.jpg"

        # Bo qua neu da gan nhan
        if ten_file in da_gan:
            continue

        # Doc anh
        anh = cv2.imread(anh_path)
        if anh is None:
            continue

        # Chay YOLO detect bien so
        results = model(anh, verbose=False)
        boxes = results[0].boxes

        if len(boxes) == 0:
            bo_qua += 1
            continue  # Khong phat hien bien so

        # Lay box confidence cao nhat
        best_idx = boxes.conf.argmax().item()
        x1, y1, x2, y2 = boxes.xyxy[best_idx].cpu().numpy().astype(int)
        conf = boxes.conf[best_idx].item()

        # Cat anh bien so
        crop = anh[max(0,y1):y2, max(0,x1):x2]
        if crop.size == 0:
            continue

        # Luu anh goc vao dataset_test
        dest = os.path.join(THU_MUC_TEST, ten_file)
        cv2.imwrite(dest, anh)

        # Phong to bien so de de nhin
        h, w = crop.shape[:2]
        scale = max(1, 400 // max(w, 1))
        big = cv2.resize(crop, (w * scale, h * scale), interpolation=cv2.INTER_LINEAR)

        window_name = "BIEN SO - Go dap an trong Terminal"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
        cv2.imshow(window_name, big)
        cv2.waitKey(500)

        # Hoi nguoi dung nhap dap an
        dap_an = input(f"[{dem+1}/{SO_ANH_CAN}] Go bien so (skip/quit): ").strip().upper()

        cv2.destroyAllWindows()

        if dap_an.lower() == "quit":
            print("Dung lai. Du lieu da luu!")
            break

        if dap_an.lower() == "skip" or dap_an == "":
            bo_qua += 1
            continue

        # Luu label
        da_gan[ten_file] = dap_an
        dem += 1

        # Ghi file ngay lap tuc (phong mat du lieu)
        with open(FILE_LABEL, "w", encoding="utf-8") as f:
            f.write("# ten_anh, bien_so_dung\n")
            for k, v in sorted(da_gan.items()):
                f.write(f"{k}, {v}\n")

        print(f"  -> Luu: {ten_file} = {dap_an} ({dem}/{SO_ANH_CAN})")

    cv2.destroyAllWindows()

    print(f"\n{'='*50}")
    print(f"TONG KET:")
    print(f"  Da gan nhan: {len(da_gan)} anh")
    print(f"  Bo qua:      {bo_qua} anh")
    print(f"  File label:  {FILE_LABEL}")
    print(f"  Thu muc anh: {THU_MUC_TEST}")
    print(f"\nBuoc tiep: chay 'python danh_gia_ocr.py' de tinh do chinh xac!")


if __name__ == "__main__":
    main()
