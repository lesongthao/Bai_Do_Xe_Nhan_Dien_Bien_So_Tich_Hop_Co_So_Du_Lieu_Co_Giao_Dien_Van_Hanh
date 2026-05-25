"""
Script danh gia chi tiet: So sanh cac phuong phap tien xu ly va hau xu ly.
Tao bang ket qua cho bao cao do an.
"""

import os
import sys
import re
import difflib
import cv2
import numpy as np

# Them duong dan hien tai
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from nhan_dien_bien_so import NhanDienBienSo, chuan_hoa_bien_so, sua_loi_theo_vi_tri_vn

THU_MUC_TEST = "dataset_test"
FILE_LABEL = "labels.txt"


def doc_labels():
    """Doc file labels.txt tra ve dict {ten_anh: bien_so_dung}."""
    labels = {}
    with open(FILE_LABEL, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",", 1)
            if len(parts) == 2:
                labels[parts[0].strip()] = parts[1].strip().upper()
    return labels


def ocr_tung_phuong_phap(ai, anh_vung, phuong_phap="goc"):
    """Chay OCR tren 1 phuong phap tien xu ly cu the.
    Tra ve (ket_qua_tho, ket_qua_hau_xu_ly)
    """
    if not ai.ocr:
        return "", ""

    # Tien xu ly
    if cv2 is None or np is None:
        return "", ""

    xam = cv2.cvtColor(anh_vung, cv2.COLOR_BGR2GRAY) if len(anh_vung.shape) == 3 else anh_vung

    if phuong_phap == "goc":
        img = anh_vung
    elif phuong_phap == "clahe":
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(xam)
        img = cv2.cvtColor(clahe, cv2.COLOR_GRAY2BGR)
    elif phuong_phap == "otsu":
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(xam)
        _, otsu = cv2.threshold(clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        img = cv2.cvtColor(otsu, cv2.COLOR_GRAY2BGR)
    else:
        img = anh_vung

    try:
        kq = ai.ocr.ocr(img, cls=False)
        if not kq or not kq[0]:
            return "", ""

        texts = []
        for dong in kq[0]:
            if dong and dong[1]:
                texts.append(dong[1][0])

        if not texts:
            return "", ""

        full_text = "".join(texts)
        bs_tho = chuan_hoa_bien_so(full_text)

        # Hau xu ly
        bs_hau = sua_loi_theo_vi_tri_vn(bs_tho)

        return bs_tho, bs_hau
    except Exception:
        return "", ""


def tinh_accuracy(labels, ket_qua):
    """Tinh accuracy cap bien so va cap ky tu."""
    dung_bien = 0
    tong_bien = 0
    dung_kytu = 0
    tong_kytu = 0

    for ten, true_label in labels.items():
        pred = ket_qua.get(ten, "")
        tong_bien += 1

        if true_label == pred:
            dung_bien += 1

        # Tinh cap ky tu
        matcher = difflib.SequenceMatcher(None, true_label, pred)
        for opcode, i1, i2, j1, j2 in matcher.get_opcodes():
            if opcode == 'equal':
                dung_kytu += (i2 - i1)
                tong_kytu += (i2 - i1)
            elif opcode == 'replace':
                length = min(i2 - i1, j2 - j1)
                tong_kytu += length
                # Dem so ky tu dung trong phan replace
                for k in range(length):
                    if true_label[i1 + k] == pred[j1 + k]:
                        dung_kytu += 1
            elif opcode == 'delete':
                tong_kytu += (i2 - i1)
            elif opcode == 'insert':
                pass  # Ky tu thua

    acc_bien = (dung_bien / tong_bien * 100) if tong_bien > 0 else 0
    acc_kytu = (dung_kytu / tong_kytu * 100) if tong_kytu > 0 else 0
    return acc_bien, acc_kytu, dung_bien, tong_bien


def main():
    print("=" * 60)
    print("DANH GIA CHI TIET - SO SANH PHUONG PHAP TIEN/HAU XU LY")
    print("=" * 60)

    # Doc labels
    labels = doc_labels()
    print(f"So anh test: {len(labels)}")

    # Load AI
    print("Dang tai mo hinh AI...")
    ai = NhanDienBienSo()
    print(f"Trang thai: {ai.trang_thai}")

    # Luu ket qua
    phuong_phap_list = ["goc", "clahe", "otsu"]
    ket_qua_tho = {pp: {} for pp in phuong_phap_list}      # Truoc hau xu ly
    ket_qua_hau = {pp: {} for pp in phuong_phap_list}      # Sau hau xu ly
    ket_qua_ket_hop = {}                                     # Ket hop chon tot nhat

    dem = 0
    for ten, true_label in labels.items():
        img_path = os.path.join(THU_MUC_TEST, ten)
        if not os.path.exists(img_path):
            continue

        anh = cv2.imread(img_path)
        if anh is None:
            continue

        dem += 1
        if dem % 20 == 0:
            print(f"  Dang xu ly: {dem}/{len(labels)}...")

        # YOLO cat vung bien so
        ds_vung = ai._cat_vung_yolo(anh)
        vung = ds_vung[0] if ds_vung else anh

        # Chay OCR tung phuong phap
        best_score = -1
        best_bs = ""

        for pp in phuong_phap_list:
            tho, hau = ocr_tung_phuong_phap(ai, vung, pp)
            ket_qua_tho[pp][ten] = tho
            ket_qua_hau[pp][ten] = hau

            # Tim ket qua tot nhat (dung cho ket hop)
            diem = ai._diem_hop_le(hau) if hau else 0
            if diem > best_score:
                best_score = diem
                best_bs = hau

        ket_qua_ket_hop[ten] = best_bs

    # ============================
    # IN KET QUA
    # ============================
    print(f"\nDa xu ly xong {dem} anh.")
    print("\n" + "=" * 70)
    print("BANG 1: SO SANH PHUONG PHAP TIEN XU LY (SAU HAU XU LY)")
    print("=" * 70)
    print(f"{'Phuong phap':<30} {'Acc ky tu':>12} {'Acc bien so':>12} {'Dung/Tong':>12}")
    print("-" * 70)

    for pp in phuong_phap_list:
        ten_pp = {"goc": "Anh goc", "clahe": "CLAHE", "otsu": "Otsu"}[pp]
        acc_b, acc_k, dung, tong = tinh_accuracy(labels, ket_qua_hau[pp])
        print(f"{ten_pp:<30} {acc_k:>11.2f}% {acc_b:>11.2f}% {dung:>5}/{tong}")

    # Ket hop
    acc_b, acc_k, dung, tong = tinh_accuracy(labels, ket_qua_ket_hop)
    print(f"{'Ket hop chon tot nhat':<30} {acc_k:>11.2f}% {acc_b:>11.2f}% {dung:>5}/{tong}")

    print("\n" + "=" * 70)
    print("BANG 2: SO SANH TRUOC VA SAU HAU XU LY (KET HOP)")
    print("=" * 70)

    # Truoc hau xu ly: lay ket qua tho tu phuong phap ket hop
    # (chon phuong phap co diem cao nhat nhung KHONG hau xu ly)
    ket_qua_truoc_hau = {}
    for ten in labels:
        best_raw = ""
        best_len = 0
        for pp in phuong_phap_list:
            raw = ket_qua_tho[pp].get(ten, "")
            if len(raw) > best_len:
                best_len = len(raw)
                best_raw = raw
        ket_qua_truoc_hau[ten] = best_raw

    acc_b_truoc, acc_k_truoc, dung_truoc, tong_truoc = tinh_accuracy(labels, ket_qua_truoc_hau)
    acc_b_sau, acc_k_sau, dung_sau, tong_sau = tinh_accuracy(labels, ket_qua_ket_hop)

    print(f"{'Chi so':<30} {'Truoc hau xu ly':>15} {'Sau hau xu ly':>15}")
    print("-" * 70)
    print(f"{'Accuracy cap ky tu':<30} {acc_k_truoc:>14.2f}% {acc_k_sau:>14.2f}%")
    print(f"{'Accuracy cap bien so':<30} {acc_b_truoc:>14.2f}% {acc_b_sau:>14.2f}%")
    print(f"{'So bien doc dung':<30} {dung_truoc:>14} {dung_sau:>14}")

    # Luu ket qua ra file
    with open("ket_qua_so_sanh.txt", "w", encoding="utf-8") as f:
        f.write("BANG 1: SO SANH PHUONG PHAP TIEN XU LY\n")
        f.write(f"{'Phuong phap':<30} {'Acc ky tu':>12} {'Acc bien so':>12}\n")
        f.write("-" * 60 + "\n")
        for pp in phuong_phap_list:
            ten_pp = {"goc": "Anh goc", "clahe": "CLAHE", "otsu": "Otsu"}[pp]
            acc_b, acc_k, dung, tong = tinh_accuracy(labels, ket_qua_hau[pp])
            f.write(f"{ten_pp:<30} {acc_k:>11.2f}% {acc_b:>11.2f}%\n")
        acc_b, acc_k, dung, tong = tinh_accuracy(labels, ket_qua_ket_hop)
        f.write(f"{'Ket hop chon tot nhat':<30} {acc_k:>11.2f}% {acc_b:>11.2f}%\n")

        f.write(f"\nBANG 2: SO SANH TRUOC VA SAU HAU XU LY\n")
        f.write(f"{'Chi so':<30} {'Truoc':>15} {'Sau':>15}\n")
        f.write("-" * 60 + "\n")
        f.write(f"{'Accuracy cap ky tu':<30} {acc_k_truoc:>14.2f}% {acc_k_sau:>14.2f}%\n")
        f.write(f"{'Accuracy cap bien so':<30} {acc_b_truoc:>14.2f}% {acc_b_sau:>14.2f}%\n")

    print("\n✅ Da luu ket qua vao 'ket_qua_so_sanh.txt'")
    print("   Copy vao thu muc bieu_do_bao_cao/ de dung cho bao cao!")


if __name__ == "__main__":
    main()
