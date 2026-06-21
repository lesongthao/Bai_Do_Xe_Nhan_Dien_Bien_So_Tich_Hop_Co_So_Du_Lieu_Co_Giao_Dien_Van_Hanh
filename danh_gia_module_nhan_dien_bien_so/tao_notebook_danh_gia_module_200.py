from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import nbformat as nbf


ROOT = Path(__file__).resolve().parent
NOTEBOOK_PATH = ROOT / "danh_gia_module_200_anh.ipynb"


def md(text: str):
    return nbf.v4.new_markdown_cell(dedent(text).strip())


def code(text: str):
    return nbf.v4.new_code_cell(dedent(text).strip())


nb = nbf.v4.new_notebook()
nb.cells = [
    md(
        """
        # Đánh giá module nhận diện biển số trên 200 ảnh

        Notebook này đánh giá lại module nhận diện theo đúng luồng xử lý trong `nhan_dien_bien_so.py`. Mục tiêu không chỉ là đếm đúng/sai, mà còn chỉ ra ảnh sai nằm ở tầng nào: YOLO, OCR, hậu xử lý hay bước chọn ứng viên.

        Các tầng được ghi log:

        1. YOLOv8n phát hiện vùng biển số và trả về bounding box.
        2. OpenCV cắt vùng biển số, tạo ba biến thể ảnh: gốc, CLAHE, Otsu.
        3. PaddleOCR đọc ký tự trên từng biến thể ảnh.
        4. Hậu xử lý chuẩn hóa, sửa lỗi theo vị trí và kiểm tra cấu trúc.
        5. Gộp ứng viên và chọn kết quả cuối theo luật: hợp cấu trúc → ít sửa → xuất hiện nhiều hơn → OCR tự tin hơn.
        """
    ),
    code(
        r'''
        import sys
        from pathlib import Path
        from collections import Counter
        import math
        import textwrap
        import time

        import cv2
        import matplotlib as mpl
        import matplotlib.pyplot as plt
        from matplotlib import font_manager as fm
        import numpy as np
        import pandas as pd
        from IPython.display import display, Markdown

        ROOT = Path.cwd()
        if not (ROOT / "nhan_dien_bien_so.py").exists():
            ROOT = ROOT.parent
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))

        from nhan_dien_bien_so import (
            NhanDienBienSo,
            chuan_hoa_bien_so,
            sua_loi_theo_vi_tri_vn,
            la_bien_so_hop_cau_truc,
            dem_so_ky_tu_da_sua,
        )

        DATASET_DIR = ROOT / "danh_gia_module_nhan_dien_bien_so" / "dataset_danh_gia_200"
        IMAGE_DIR = DATASET_DIR / "images"
        LABEL_CSV = DATASET_DIR / "labels" / "nhan_bien_so.csv"

        RESULT_DIR = ROOT / "danh_gia_module_nhan_dien_bien_so" / "ket_qua_danh_gia_200"
        DATA_DIR = RESULT_DIR / "du_lieu"
        FIG_DIR = RESULT_DIR / "anh_bao_cao"
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        FIG_DIR.mkdir(parents=True, exist_ok=True)

        for path in list(DATA_DIR.glob("*.csv")) + list(FIG_DIR.glob("*.png")):
            path.unlink()

        font_names = {f.name for f in fm.fontManager.ttflist}
        for font_name in ["Times New Roman", "Arial", "Segoe UI", "DejaVu Sans"]:
            if font_name in font_names:
                break
        mpl.rcParams["font.family"] = font_name
        mpl.rcParams["axes.unicode_minus"] = False
        mpl.rcParams["figure.facecolor"] = "white"
        mpl.rcParams["axes.facecolor"] = "white"
        mpl.rcParams["savefig.facecolor"] = "white"

        BLUE = "#2563eb"
        GREEN = "#16a34a"
        ORANGE = "#ea580c"
        RED = "#dc2626"
        PURPLE = "#7c3aed"
        GRAY = "#475569"
        LIGHT = "#f8fafc"
        BORDER = "#cbd5e1"

        def wrap_vi(text, width=34):
            return "\n".join(textwrap.wrap(str(text), width=width, break_long_words=False))

        def save_fig(fig, name):
            fig.savefig(FIG_DIR / name, dpi=220, bbox_inches="tight")
            plt.close(fig)

        def read_image_unicode(path: Path):
            data = np.fromfile(str(path), dtype=np.uint8)
            if data.size == 0:
                return None
            return cv2.imdecode(data, cv2.IMREAD_COLOR)

        def levenshtein(a: str, b: str) -> int:
            a = a or ""
            b = b or ""
            if a == b:
                return 0
            if not a:
                return len(b)
            if not b:
                return len(a)
            prev = list(range(len(b) + 1))
            for i, ca in enumerate(a, 1):
                cur = [i]
                for j, cb in enumerate(b, 1):
                    cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
                prev = cur
            return prev[-1]

        def char_accuracy(gt: str, pred: str) -> float:
            gt = chuan_hoa_bien_so(gt)
            pred = chuan_hoa_bien_so(pred)
            if not gt:
                return 1.0 if not pred else 0.0
            return max(0.0, 1.0 - levenshtein(gt, pred) / len(gt))

        def write_csv(df, name):
            df.to_csv(DATA_DIR / name, index=False, encoding="utf-8-sig")

        labels = pd.read_csv(LABEL_CSV, dtype=str).fillna("")
        labels["ground_truth"] = labels["ground_truth"].map(chuan_hoa_bien_so)
        labels["duong_dan_anh"] = labels["ten_anh"].map(lambda x: str(IMAGE_DIR / x))

        assert len(labels) == 200, f"Tập đánh giá phải có 200 ảnh, hiện có {len(labels)}"
        missing = [p for p in labels["duong_dan_anh"] if not Path(p).exists()]
        assert not missing, f"Thiếu {len(missing)} ảnh, ví dụ: {missing[:3]}"

        display(Markdown(f"Đã nạp **{len(labels)} ảnh** và nhãn đúng từ `{LABEL_CSV}`."))
        '''
    ),
    md(
        """
        ## 1. Luồng xử lý thật của module

        Bảng dưới đây mô tả đúng vai trò của từng tầng trong module. YOLO chỉ phát hiện vùng biển số; PaddleOCR mới đọc ký tự; kết quả cuối do khối hậu xử lý và xếp hạng ứng viên quyết định.
        """
    ),
    code(
        r'''
        luong_xu_ly = pd.DataFrame([
            ["1", "YOLOv8n", "Phát hiện vùng biển số", "Bounding box vùng biển số hoặc dùng ảnh gốc dự phòng"],
            ["2", "OpenCV", "Cắt vùng biển số và tạo ảnh gốc, CLAHE, Otsu", "Ba biến thể ảnh đưa vào OCR"],
            ["3", "PaddleOCR", "Đọc ký tự trên từng biến thể ảnh", "Chuỗi OCR thô và độ tin cậy trung bình"],
            ["4", "Hậu xử lý", "Chuẩn hóa, sửa lỗi theo vị trí, kiểm tra cấu trúc", "Ứng viên biển số đã xử lý"],
            ["5", "Xếp hạng", "Gộp ứng viên và chọn theo luật ưu tiên", "Biển số cuối cùng"],
        ], columns=["Bước", "Tầng xử lý", "Nhiệm vụ", "Đầu ra"])
        write_csv(luong_xu_ly, "01_luong_xu_ly_module.csv")
        display(luong_xu_ly)
        '''
    ),
    md(
        """
        ## 2. Chạy suy luận và ghi log từng tầng

        Cell này chạy đúng pipeline nhận diện và ghi lại toàn bộ thông tin trung gian. Phần chạy có thể mất vài phút vì PaddleOCR phải đọc 200 ảnh với ba biến thể ảnh.
        """
    ),
    code(
        r'''
        recognizer = NhanDienBienSo()
        print("Trạng thái module:", recognizer.trang_thai)

        bien_the_names = ["Ảnh gốc", "Ảnh CLAHE", "Ảnh Otsu"]
        chi_tiet_kq = []
        chi_tiet_yolo = []
        chi_tiet_ocr = []
        chi_tiet_uv = []
        chi_tiet_chon = []

        def rank_tuple(valid, so_sua, so_lan, best_conf):
            return recognizer._thu_hang_ung_vien(valid, so_sua, so_lan, best_conf)

        def yolo_crop_with_log(anh):
            if not recognizer.yolo:
                return [{"crop_index": 0, "crop": anh, "fallback_anh_goc": True, "bbox": "", "conf": np.nan, "class_id": ""}]
            try:
                kq = recognizer.yolo.predict(source=anh, conf=0.25, imgsz=640, verbose=False, device="cpu")
                if not kq or not kq[0].boxes or len(kq[0].boxes) == 0:
                    return [{"crop_index": 0, "crop": anh, "fallback_anh_goc": True, "bbox": "", "conf": np.nan, "class_id": ""}]

                ds = []
                h, w = anh.shape[:2]
                for idx, box in enumerate(kq[0].boxes):
                    x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                    x1, y1 = max(0, x1), max(0, y1)
                    x2, y2 = min(w, x2), min(h, y2)
                    if x2 <= x1 or y2 <= y1:
                        continue
                    conf = float(box.conf[0].item()) if getattr(box, "conf", None) is not None else np.nan
                    cls = int(box.cls[0].item()) if getattr(box, "cls", None) is not None else ""
                    ds.append({
                        "crop_index": idx,
                        "crop": anh[y1:y2, x1:x2],
                        "fallback_anh_goc": False,
                        "bbox": f"{x1},{y1},{x2},{y2}",
                        "conf": conf,
                        "class_id": cls,
                    })
                return ds or [{"crop_index": 0, "crop": anh, "fallback_anh_goc": True, "bbox": "", "conf": np.nan, "class_id": ""}]
            except Exception as exc:
                return [{"crop_index": 0, "crop": anh, "fallback_anh_goc": True, "bbox": "", "conf": np.nan, "class_id": "", "yolo_error": str(exc)}]

        def parse_ocr_result(kq):
            if not kq or not kq[0]:
                return [], "", 0.0
            lines = []
            texts = []
            conf_sum = 0.0
            for dong in kq[0]:
                if dong and len(dong) > 1 and dong[1]:
                    text = str(dong[1][0])
                    conf = float(dong[1][1])
                    texts.append(text)
                    conf_sum += conf
                    lines.append({"text": text, "conf": conf})
            avg_conf = conf_sum / len(texts) if texts else 0.0
            return lines, "".join(texts), avg_conf

        def classify_error(row, ocr_rows, candidate_rows):
            if row["dung_bien_so"]:
                return "Đúng"
            gt = row["ground_truth"]
            pred = row["du_doan_cuoi"]
            has_any_ocr = any(chuan_hoa_bien_so(x.get("raw_text", "")) for x in ocr_rows)
            has_candidate = len(candidate_rows) > 0
            gt_in_candidates = any(x["ung_vien"] == gt for x in candidate_rows)
            raw_join = " ".join(chuan_hoa_bien_so(x.get("raw_text", "")) for x in ocr_rows)
            normalized_join = " ".join(x.get("normalized", "") for x in ocr_rows)

            if row["so_box_yolo"] == 0:
                return "YOLO không phát hiện vùng biển số"
            if not has_any_ocr:
                return "OCR không đọc ra ký tự"
            if not has_candidate:
                return "Không tạo được ứng viên sau hậu xử lý"
            if gt_in_candidates and pred != gt:
                return "Có ứng viên đúng nhưng chọn sai"
            if len(pred) < len(gt):
                return "OCR đọc thiếu ký tự"
            if normalized_join and levenshtein(normalized_join.replace(" ", ""), gt) < levenshtein(pred, gt):
                return "Hậu xử lý làm lệch kết quả"
            if raw_join:
                return "OCR nhầm ký tự hoặc ảnh khó"
            return "Không xác định rõ"

        start_all = time.perf_counter()
        for stt, item in labels.iterrows():
            ten_anh = item["ten_anh"]
            gt = item["ground_truth"]
            img_path = IMAGE_DIR / ten_anh
            anh = read_image_unicode(img_path)
            if anh is None:
                raise RuntimeError(f"Không đọc được ảnh: {img_path}")

            t0 = time.perf_counter()
            crops = yolo_crop_with_log(anh)
            ung_vien = {}
            ocr_rows_this = []

            for crop_info in crops:
                crop = crop_info["crop"]
                h_crop, w_crop = crop.shape[:2]
                chi_tiet_yolo.append({
                    "ten_anh": ten_anh,
                    "crop_index": crop_info["crop_index"],
                    "co_box_yolo": not crop_info["fallback_anh_goc"],
                    "fallback_anh_goc": crop_info["fallback_anh_goc"],
                    "bbox": crop_info.get("bbox", ""),
                    "yolo_conf": crop_info.get("conf", np.nan),
                    "class_id": crop_info.get("class_id", ""),
                    "crop_width": w_crop,
                    "crop_height": h_crop,
                    "yolo_error": crop_info.get("yolo_error", ""),
                })

                variants = recognizer._tien_xu_ly(crop)
                for bien_the_idx, bien_the in enumerate(variants):
                    bien_the_name = bien_the_names[bien_the_idx] if bien_the_idx < len(bien_the_names) else f"Biến thể {bien_the_idx + 1}"
                    try:
                        ocr_kq = recognizer.ocr.ocr(bien_the, cls=False)
                    except Exception as exc:
                        ocr_kq = None
                        ocr_error = str(exc)
                    else:
                        ocr_error = ""

                    lines, raw_text, avg_conf = parse_ocr_result(ocr_kq)
                    normalized = chuan_hoa_bien_so(raw_text)
                    fixed = sua_loi_theo_vi_tri_vn(normalized)
                    valid = la_bien_so_hop_cau_truc(fixed)
                    so_sua = dem_so_ky_tu_da_sua(normalized, fixed) if fixed else 0

                    ocr_row = {
                        "ten_anh": ten_anh,
                        "ground_truth": gt,
                        "crop_index": crop_info["crop_index"],
                        "bien_the": bien_the_name,
                        "so_dong_ocr": len(lines),
                        "texts": " | ".join(x["text"] for x in lines),
                        "raw_text": raw_text,
                        "avg_conf": avg_conf,
                        "normalized": normalized,
                        "fixed": fixed,
                        "hop_cau_truc": valid,
                        "so_ky_tu_da_sua": so_sua,
                        "ocr_error": ocr_error,
                    }
                    chi_tiet_ocr.append(ocr_row)
                    ocr_rows_this.append(ocr_row)

                    if not normalized or not fixed:
                        continue

                    info = ung_vien.get(fixed)
                    source_desc = f"crop {crop_info['crop_index']} - {bien_the_name}"
                    if info is None:
                        ung_vien[fixed] = {
                            "ung_vien": fixed,
                            "valid": valid,
                            "so_sua": so_sua,
                            "so_lan": 1,
                            "best_conf": avg_conf,
                            "nguon_tot_nhat": source_desc,
                        }
                    else:
                        info["valid"] = info["valid"] or valid
                        info["so_sua"] = min(int(info["so_sua"]), int(so_sua))
                        info["so_lan"] = int(info["so_lan"]) + 1
                        if avg_conf > float(info["best_conf"]):
                            info["best_conf"] = avg_conf
                            info["nguon_tot_nhat"] = source_desc

            candidate_rows_this = []
            for text, info in ung_vien.items():
                score = rank_tuple(info["valid"], info["so_sua"], info["so_lan"], info["best_conf"])
                uv_row = {
                    "ten_anh": ten_anh,
                    "ground_truth": gt,
                    "ung_vien": text,
                    "hop_cau_truc": bool(info["valid"]),
                    "so_ky_tu_da_sua_min": int(info["so_sua"]),
                    "so_lan_xuat_hien": int(info["so_lan"]),
                    "best_conf": float(info["best_conf"]),
                    "nguon_tot_nhat": info["nguon_tot_nhat"],
                    "rank_key": str(score),
                    "la_nhan_dung": text == gt,
                }
                candidate_rows_this.append(uv_row)
                chi_tiet_uv.append(uv_row)

            if candidate_rows_this:
                best = max(
                    candidate_rows_this,
                    key=lambda x: rank_tuple(x["hop_cau_truc"], x["so_ky_tu_da_sua_min"], x["so_lan_xuat_hien"], x["best_conf"])
                )
                pred = best["ung_vien"]
                ly_do_chon = (
                    f"Hợp cấu trúc={best['hop_cau_truc']}; "
                    f"sửa {best['so_ky_tu_da_sua_min']} ký tự; "
                    f"xuất hiện {best['so_lan_xuat_hien']} lần; "
                    f"OCR tin cậy {best['best_conf']:.3f}"
                )
            else:
                best = None
                pred = ""
                ly_do_chon = "Không có ứng viên sau OCR và hậu xử lý"

            runtime_ms = (time.perf_counter() - t0) * 1000
            module_pred, _ = recognizer.nhan_dien(anh)
            module_pred = chuan_hoa_bien_so(module_pred)
            row = {
                "stt": stt + 1,
                "ten_anh": ten_anh,
                "ground_truth": gt,
                "du_doan_cuoi": pred,
                "du_doan_module_goc": module_pred,
                "khop_voi_module_goc": pred == module_pred,
                "dung_bien_so": pred == gt,
                "accuracy_ky_tu": char_accuracy(gt, pred),
                "edit_distance": levenshtein(gt, pred),
                "hop_cau_truc_du_doan": la_bien_so_hop_cau_truc(pred),
                "so_box_yolo": sum(1 for c in crops if not c["fallback_anh_goc"]),
                "fallback_anh_goc": all(c["fallback_anh_goc"] for c in crops),
                "so_bien_the_co_text": sum(1 for r in ocr_rows_this if chuan_hoa_bien_so(r["raw_text"])),
                "so_ung_vien": len(candidate_rows_this),
                "co_ung_vien_dung": any(r["ung_vien"] == gt for r in candidate_rows_this),
                "ung_vien_thang_hop_cau_truc": bool(best["hop_cau_truc"]) if best else False,
                "ung_vien_thang_so_sua": int(best["so_ky_tu_da_sua_min"]) if best else np.nan,
                "ung_vien_thang_so_lan": int(best["so_lan_xuat_hien"]) if best else 0,
                "ung_vien_thang_conf": float(best["best_conf"]) if best else 0.0,
                "bien_the_thang": best["nguon_tot_nhat"] if best else "",
                "ly_do_chon": ly_do_chon,
                "thoi_gian_ms": runtime_ms,
            }
            row["nhom_loi"] = classify_error(row, ocr_rows_this, candidate_rows_this)
            chi_tiet_kq.append(row)
            chi_tiet_chon.append({
                "ten_anh": ten_anh,
                "ground_truth": gt,
                "ung_vien_duoc_chon": pred,
                "dung_bien_so": pred == gt,
                "co_ung_vien_dung": row["co_ung_vien_dung"],
                "ly_do_chon": ly_do_chon,
                "nhom_loi": row["nhom_loi"],
            })

            if (stt + 1) % 20 == 0:
                print(f"Đã xử lý {stt + 1}/200 ảnh")

        df_kq = pd.DataFrame(chi_tiet_kq)
        df_yolo = pd.DataFrame(chi_tiet_yolo)
        df_ocr = pd.DataFrame(chi_tiet_ocr)
        df_uv = pd.DataFrame(chi_tiet_uv)
        df_chon = pd.DataFrame(chi_tiet_chon)

        total_runtime = time.perf_counter() - start_all
        print(f"Hoàn tất đánh giá trong {total_runtime/60:.1f} phút")
        display(df_kq.head())
        '''
    ),
    md(
        """
        ## 3. Tính chỉ số và xuất CSV
        """
    ),
    code(
        r'''
        tong_anh = len(df_kq)
        dung = int(df_kq["dung_bien_so"].sum())
        sai = tong_anh - dung
        acc_bien_so = dung / tong_anh
        tong_ky_tu_nhan = int(df_kq["ground_truth"].astype(str).str.len().sum())
        tong_ky_tu_sai = int(df_kq["edit_distance"].sum())
        cer = tong_ky_tu_sai / tong_ky_tu_nhan if tong_ky_tu_nhan else 0.0
        char_acc = 1 - cer
        yolo_detect = float((df_kq["so_box_yolo"] > 0).mean())
        ocr_read = float((df_kq["so_bien_the_co_text"] > 0).mean())
        has_candidate = float((df_kq["so_ung_vien"] > 0).mean())
        has_correct_candidate = float(df_kq["co_ung_vien_dung"].mean())
        chose_correct_when_exists = float(df_kq.loc[df_kq["co_ung_vien_dung"], "dung_bien_so"].mean()) if df_kq["co_ung_vien_dung"].any() else 0.0
        valid_final = float(df_kq["hop_cau_truc_du_doan"].mean())
        avg_time = float(df_kq["thoi_gian_ms"].mean())
        med_time = float(df_kq["thoi_gian_ms"].median())
        mismatch = int((~df_kq["khop_voi_module_goc"]).sum())

        kpi_rows = [
            ["Tổng số ảnh", tong_anh, ""],
            ["Đúng hoàn toàn", dung, f"{acc_bien_so*100:.2f}%"],
            ["Sai", sai, f"{sai/tong_anh*100:.2f}%"],
            ["Accuracy cấp biển số", acc_bien_so, f"{acc_bien_so*100:.2f}%"],
            ["Accuracy cấp ký tự", char_acc, f"{char_acc*100:.2f}%"],
            ["CER", cer, f"{cer*100:.2f}%"],
            ["Tổng ký tự nhãn đúng", tong_ky_tu_nhan, str(tong_ky_tu_nhan)],
            ["Tổng lỗi ký tự", tong_ky_tu_sai, str(tong_ky_tu_sai)],
            ["YOLO phát hiện vùng biển số", yolo_detect, f"{yolo_detect*100:.2f}%"],
            ["OCR đọc được ít nhất một chuỗi", ocr_read, f"{ocr_read*100:.2f}%"],
            ["Tạo được ứng viên", has_candidate, f"{has_candidate*100:.2f}%"],
            ["Có ứng viên đúng trong danh sách", has_correct_candidate, f"{has_correct_candidate*100:.2f}%"],
            ["Chọn đúng khi ứng viên đúng tồn tại", chose_correct_when_exists, f"{chose_correct_when_exists*100:.2f}%"],
            ["Kết quả cuối hợp cấu trúc", valid_final, f"{valid_final*100:.2f}%"],
            ["Thời gian trung bình", avg_time, f"{avg_time:.0f} ms"],
            ["Thời gian trung vị", med_time, f"{med_time:.0f} ms"],
            ["Số ảnh lệch với hàm nhan_dien() gốc", mismatch, str(mismatch)],
        ]
        df_kpi = pd.DataFrame(kpi_rows, columns=["chi_so", "gia_tri", "hien_thi"])

        error_counts = df_kq["nhom_loi"].value_counts().reset_index()
        error_counts.columns = ["nhom_loi", "so_anh"]
        error_counts["ty_le"] = error_counts["so_anh"] / tong_anh * 100
        order = ["Đúng", "YOLO không phát hiện vùng biển số", "OCR không đọc ra ký tự", "Không tạo được ứng viên sau hậu xử lý", "OCR đọc thiếu ký tự", "OCR nhầm ký tự hoặc ảnh khó", "Hậu xử lý làm lệch kết quả", "Có ứng viên đúng nhưng chọn sai", "Không xác định rõ"]
        error_counts["thu_tu"] = error_counts["nhom_loi"].map({v: i for i, v in enumerate(order)}).fillna(99)
        error_counts = error_counts.sort_values(["thu_tu", "nhom_loi"]).drop(columns=["thu_tu"])

        wrong_examples = df_kq.loc[~df_kq["dung_bien_so"]].copy()

        write_csv(df_kpi, "tong_hop_chi_so.csv")
        write_csv(df_kq, "ket_qua_chi_tiet.csv")
        write_csv(df_yolo, "chi_tiet_yolo.csv")
        write_csv(df_ocr, "chi_tiet_ocr_theo_bien_the.csv")
        write_csv(df_uv, "chi_tiet_ung_vien.csv")
        write_csv(df_chon, "danh_gia_chon_ung_vien.csv")
        write_csv(error_counts, "phan_tich_loi.csv")
        write_csv(wrong_examples, "mau_sai_tieu_bieu.csv")

        display(df_kpi)
        display(error_counts)
        '''
    ),
    md(
        """
        ## 4. Trực quan hóa kết quả
        """
    ),
    code(
        r'''
        # 01. Dashboard KPI
        dashboard = [
            ("Đúng biển số", f"{dung}/{tong_anh}", f"{acc_bien_so*100:.2f}%"),
            ("Accuracy ký tự", f"{char_acc*100:.2f}%", "Tính theo CER"),
            ("CER", f"{cer*100:.2f}%", "Càng thấp càng tốt"),
            ("YOLO phát hiện", f"{yolo_detect*100:.2f}%", "Có bounding box"),
            ("OCR đọc được", f"{ocr_read*100:.2f}%", "Ít nhất một chuỗi"),
            ("Có ứng viên đúng", f"{has_correct_candidate*100:.2f}%", "Sau hậu xử lý"),
        ]
        fig, axes = plt.subplots(2, 3, figsize=(13.5, 6.6))
        colors = [GREEN, BLUE, ORANGE, PURPLE, BLUE, GREEN]
        for ax, (title, value, subtitle), color in zip(axes.flat, dashboard, colors):
            ax.axis("off")
            ax.add_patch(plt.Rectangle((0.02, 0.08), 0.96, 0.84, transform=ax.transAxes, facecolor=LIGHT, edgecolor=BORDER, linewidth=1.4))
            ax.text(0.5, 0.63, value, ha="center", va="center", fontsize=25, fontweight="bold", color=color)
            ax.text(0.5, 0.38, title, ha="center", va="center", fontsize=13.5, fontweight="bold", color="#111827")
            ax.text(0.5, 0.22, subtitle, ha="center", va="center", fontsize=10.5, color=GRAY)
        fig.suptitle("Tổng quan kết quả đánh giá module nhận diện biển số", fontsize=17, fontweight="bold", y=0.98)
        fig.tight_layout(rect=[0, 0, 1, 0.93])
        save_fig(fig, "01_dashboard_kpi.png")

        # 02. Pipeline tỷ lệ đạt
        pipeline = pd.DataFrame([
            ["YOLO phát hiện vùng biển số", yolo_detect],
            ["OCR đọc được chuỗi", ocr_read],
            ["Tạo được ứng viên", has_candidate],
            ["Có ứng viên đúng", has_correct_candidate],
            ["Kết quả cuối đúng", acc_bien_so],
        ], columns=["Tầng xử lý", "Tỷ lệ"])
        fig, ax = plt.subplots(figsize=(11, 5.2))
        bars = ax.barh(pipeline["Tầng xử lý"], pipeline["Tỷ lệ"] * 100, color=[BLUE, BLUE, PURPLE, ORANGE, GREEN])
        ax.invert_yaxis()
        ax.set_xlim(0, 105)
        ax.set_xlabel("Tỷ lệ đạt (%)")
        ax.set_title("Tỷ lệ đạt theo từng tầng xử lý", fontsize=15, fontweight="bold", pad=12)
        ax.grid(axis="x", linestyle="--", alpha=0.25)
        ax.spines[["top", "right"]].set_visible(False)
        for bar in bars:
            ax.text(bar.get_width() + 1.0, bar.get_y() + bar.get_height() / 2, f"{bar.get_width():.2f}%", va="center", fontsize=10.5, fontweight="bold")
        fig.tight_layout()
        save_fig(fig, "02_pipeline_ty_le_dat.png")

        # 03. Phân loại lỗi
        err_plot = error_counts[error_counts["nhom_loi"] != "Đúng"].copy()
        if err_plot.empty:
            err_plot = pd.DataFrame([{"nhom_loi": "Không có ảnh sai", "so_anh": 0, "ty_le": 0.0}])
        fig, ax = plt.subplots(figsize=(11, 4.8))
        bars = ax.barh(err_plot["nhom_loi"], err_plot["so_anh"], color=[RED, ORANGE, PURPLE, BLUE, GREEN, GRAY][:len(err_plot)])
        ax.invert_yaxis()
        ax.set_xlabel("Số ảnh")
        ax.set_title("Phân loại ảnh sai theo tầng xử lý", fontsize=15, fontweight="bold", pad=12)
        ax.grid(axis="x", linestyle="--", alpha=0.25)
        ax.spines[["top", "right"]].set_visible(False)
        for bar, pct in zip(bars, err_plot["ty_le"]):
            ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2, f"{int(bar.get_width())} ảnh | {pct:.1f}%", va="center", fontsize=10.5, fontweight="bold")
        fig.tight_layout()
        save_fig(fig, "03_phan_loai_loi_theo_tang.png")

        # 04. Hiệu quả biến thể OCR
        variant_stats = df_ocr.groupby("bien_the").agg(
            so_luot=("ten_anh", "count"),
            co_text=("raw_text", lambda s: sum(bool(chuan_hoa_bien_so(x)) for x in s)),
            hop_cau_truc=("hop_cau_truc", "sum"),
            avg_conf=("avg_conf", "mean"),
        ).reset_index()
        variant_stats["ty_le_co_text"] = variant_stats["co_text"] / variant_stats["so_luot"] * 100
        variant_stats["ty_le_hop_cau_truc"] = variant_stats["hop_cau_truc"] / variant_stats["so_luot"] * 100
        write_csv(variant_stats, "hieu_qua_bien_the_ocr.csv")
        fig, ax = plt.subplots(figsize=(10.5, 5.2))
        x = np.arange(len(variant_stats))
        width = 0.36
        b1 = ax.bar(x - width/2, variant_stats["ty_le_co_text"], width, label="OCR đọc được chuỗi", color=BLUE)
        b2 = ax.bar(x + width/2, variant_stats["ty_le_hop_cau_truc"], width, label="Sau xử lý hợp cấu trúc", color=GREEN)
        ax.set_xticks(x, variant_stats["bien_the"])
        ax.set_ylim(0, 105)
        ax.set_ylabel("Tỷ lệ (%)")
        ax.set_title("Hiệu quả OCR theo từng biến thể ảnh", fontsize=15, fontweight="bold", pad=12)
        ax.legend(frameon=False)
        ax.grid(axis="y", linestyle="--", alpha=0.25)
        ax.spines[["top", "right"]].set_visible(False)
        for bars in [b1, b2]:
            for bar in bars:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f"{bar.get_height():.1f}%", ha="center", fontsize=9.5)
        fig.tight_layout()
        save_fig(fig, "04_hieu_qua_bien_the_ocr.png")

        # 05. Phân bố số ứng viên
        cand_dist = df_kq["so_ung_vien"].value_counts().sort_index()
        fig, ax = plt.subplots(figsize=(9.5, 4.8))
        bars = ax.bar(cand_dist.index.astype(str), cand_dist.values, color=PURPLE)
        ax.set_xlabel("Số ứng viên sau gộp")
        ax.set_ylabel("Số ảnh")
        ax.set_title("Phân bố số ứng viên biển số sau hậu xử lý", fontsize=15, fontweight="bold", pad=12)
        ax.grid(axis="y", linestyle="--", alpha=0.25)
        ax.spines[["top", "right"]].set_visible(False)
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.6, str(int(bar.get_height())), ha="center", fontsize=10.5, fontweight="bold")
        fig.tight_layout()
        save_fig(fig, "05_phan_bo_so_ung_vien.png")

        # 06. Mẫu sai tiêu biểu
        wrong_plot = df_kq.loc[~df_kq["dung_bien_so"]].copy().sort_values(["nhom_loi", "ten_anh"]).head(6)
        cols = 3
        rows_plot = max(1, math.ceil(len(wrong_plot) / cols))
        fig, axes = plt.subplots(rows_plot, cols, figsize=(15, 4.9 * rows_plot))
        axes = np.array(axes).reshape(rows_plot, cols)
        for ax in axes.flat:
            ax.axis("off")
        for ax, row in zip(axes.flat, wrong_plot.itertuples(index=False)):
            img = read_image_unicode(IMAGE_DIR / row.ten_anh)
            if img is not None:
                ax.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            ax.set_title(f"Mẫu {row.ten_anh}", fontsize=12.5, fontweight="bold", pad=10)
            pred_show = row.du_doan_cuoi if row.du_doan_cuoi else "RỖNG"
            note = f"Nhãn đúng: {row.ground_truth}\nHệ thống đọc: {pred_show}\nNguyên nhân: {row.nhom_loi}"
            ax.text(
                0.5, -0.08, wrap_vi(note, 32),
                transform=ax.transAxes,
                ha="center", va="top",
                fontsize=9.6, color="#111827",
                bbox=dict(boxstyle="round,pad=0.45", fc="white", ec=BORDER),
            )
        fig.suptitle("Các mẫu sai tiêu biểu và nguyên nhân theo tầng xử lý", fontsize=16, fontweight="bold", y=0.98)
        fig.tight_layout(rect=[0, 0.02, 1, 0.95], h_pad=3.2)
        save_fig(fig, "06_mau_sai_tieu_bieu.png")
        '''
    ),
    md(
        """
        ## 5. Kiểm tra khớp với hàm nhận diện gốc
        """
    ),
    code(
        r'''
        mismatch_count = int((~df_kq["khop_voi_module_goc"]).sum())
        display(Markdown(
            f"""
            - Số ảnh đánh giá: **{len(df_kq)}**
            - Số ảnh notebook suy luận khác `NhanDienBienSo.nhan_dien()`: **{mismatch_count}**
            - Kết quả đúng biển số: **{dung}/{tong_anh} ({acc_bien_so*100:.2f}%)**
            - CER: **{cer*100:.2f}%**
            """
        ))

        if mismatch_count:
            display(df_kq.loc[~df_kq["khop_voi_module_goc"], ["ten_anh", "du_doan_cuoi", "du_doan_module_goc", "ground_truth"]])
        else:
            display(Markdown("**Kết luận:** luồng đánh giá chi tiết khớp với kết quả module gốc trên toàn bộ tập 200 ảnh."))
        '''
    ),
]

nb.metadata["kernelspec"] = {
    "display_name": "Python 3",
    "language": "python",
    "name": "python3",
}
nb.metadata["language_info"] = {
    "name": "python",
    "version": "3",
}

NOTEBOOK_PATH.write_text(nbf.writes(nb), encoding="utf-8")
print("Notebook created: danh_gia_module_nhan_dien_bien_so/danh_gia_module_200_anh.ipynb")
