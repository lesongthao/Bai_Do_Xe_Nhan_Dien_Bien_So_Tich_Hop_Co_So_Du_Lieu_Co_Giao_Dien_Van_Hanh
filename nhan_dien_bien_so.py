"""
Module nhan dien bien so xe.
Pipeline: YOLOv8 tim vung bien â†’ Tien xu ly anh â†’ PaddleOCR doc ky tu â†’ Hau xu ly VN.
"""

# Luu y: OMP_NUM_THREADS=1 duoc dat trong giao_dien_chinh.py (entry point)
# Khong can dat lai o day de tranh trung lap.

import os
import re
from pathlib import Path

_LOCAL_ULTRALYTICS_CONFIG = Path(__file__).resolve().parent / ".ultralytics"
try:
    _LOCAL_ULTRALYTICS_CONFIG.mkdir(exist_ok=True)
    os.environ.setdefault("YOLO_CONFIG_DIR", str(_LOCAL_ULTRALYTICS_CONFIG))
except Exception:
    pass

try:
    import cv2
    import numpy as np
except Exception:
    cv2 = None
    np = None

try:
    from ultralytics import YOLO
except Exception:
    YOLO = None

try:
    from paddleocr import PaddleOCR
except Exception:
    PaddleOCR = None


# ============================================================
# HAM TIEN ICH
# ============================================================

def chuan_hoa_bien_so(bien_so):
    """Chuan hoa bien so: bo ky tu dac biet, viet hoa."""
    return re.sub(r"[^A-Za-z0-9]", "", (bien_so or "")).upper()


def dinh_dang_hien_thi(bien_so):
    """Dinh dang bien so de hien thi: bo dau, viet hoa, chi giu chu + so."""
    return chuan_hoa_bien_so(bien_so)


def sua_loi_theo_vi_tri_vn(bien_so):
    """Sua loi nham ky tu dua theo vi tri bien VN.

    Ho tro cac loai bien so:
    - O to:      2 so + 1 chu + 5 so         = 8 ky tu  (VD: 51H59531)
    - Xe may:    2 so + 1 chu + 6 so         = 9 ky tu  (VD: 36F504327)
    - Dac biet:  2 so + 2 chu + 5 so         = 9 ky tu  (VD: 80CD12345)
    - Xe may cu: 2 so + 1 chu + 1 so + 4 so  = 8 ky tu  (VD: 29N87258)
    """
    bs = chuan_hoa_bien_so(bien_so)

    if len(bs) < 7:
        return bs

    chu_sang_so = {"O": "0", "Q": "0", "I": "1", "L": "1",
                   "Z": "2", "S": "5", "B": "8", "G": "6"}
    so_sang_chu = {"0": "D", "1": "I", "2": "Z", "5": "S", "6": "G", "8": "B"}

    ky_tu = list(bs)

    # Vi tri 0, 1: phai la so (ma tinh/thanh pho)
    for i in (0, 1):
        if not ky_tu[i].isdigit():
            ky_tu[i] = chu_sang_so.get(ky_tu[i], ky_tu[i])

    # Vi tri 2: phai la chu (seri)
    if ky_tu[2].isdigit():
        ky_tu[2] = so_sang_chu.get(ky_tu[2], ky_tu[2])

    # Xac dinh vi tri bat dau cua phan so:
    # Truong hop 2 chu lien tiep o vi tri 2-3 (VD: 80CD12345)
    if len(ky_tu) >= 9 and ky_tu[3].isalpha():
        bat_dau_so = 4
    else:
        # O to (8 ky tu) hoac xe may (9 ky tu): vi tri 3+ la so
        bat_dau_so = 3

    # Phan con lai: uu tien la so
    for i in range(bat_dau_so, len(ky_tu)):
        if not ky_tu[i].isdigit():
            ky_tu[i] = chu_sang_so.get(ky_tu[i], ky_tu[i])

    return "".join(ky_tu)


# ============================================================
# LOP NHAN DIEN BIEN SO
# ============================================================

class NhanDienBienSo:
    """Nhan dien bien so xe: YOLOv8 + PaddleOCR + hau xu ly VN."""

    def __init__(self):
        self.yolo = None
        self.ocr = None
        self.trang_thai = "Dang khoi tao..."

        # Load YOLO model (neu co)
        model_path = Path(__file__).resolve().parent / "mo_hinh" / "bien_so_yolo.pt"
        if YOLO and model_path.exists():
            try:
                self.yolo = YOLO(str(model_path))
                self.trang_thai = "YOLO OK"
            except Exception as e:
                self.trang_thai = f"YOLO loi: {e}"
        else:
            self.trang_thai = "Chua co model YOLO"

        # Load PaddleOCR
        if PaddleOCR:
            try:
                self.ocr = PaddleOCR(use_angle_cls=False, lang="en", show_log=False)
                self.trang_thai += " | PaddleOCR OK"
            except Exception as e:
                self.trang_thai += f" | PaddleOCR loi: {e}"
        else:
            self.trang_thai += " | Chua cai PaddleOCR"

        # Warm-up: chay 1 lan voi anh trong de YOLO+OCR compile/cache
        # Lan dau luon cham (4-5s), sau warmup chi con ~0.3-0.5s
        if cv2 is not None and np is not None:
            _dummy = np.zeros((100, 200, 3), dtype=np.uint8)
            if self.yolo:
                try:
                    self.yolo.predict(source=_dummy, conf=0.25, imgsz=640,
                                      verbose=False, device="cpu")
                except Exception:
                    pass
            if self.ocr:
                try:
                    self.ocr.ocr(_dummy, cls=False)
                except Exception:
                    pass

    def _cat_vung_yolo(self, anh):
        """Dung YOLO de tim va cat vung bien so tu anh."""
        if not self.yolo or cv2 is None:
            return [anh]
        try:
            kq = self.yolo.predict(source=anh, conf=0.25, imgsz=640,
                                   verbose=False, device="cpu")
            if not kq or not kq[0].boxes or len(kq[0].boxes) == 0:
                return [anh]
            ds = []
            h, w = anh.shape[:2]
            for box in kq[0].boxes:
                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                if x2 <= x1 or y2 <= y1:
                    continue
                ds.append(anh[y1:y2, x1:x2])

            return ds if ds else [anh]
        except Exception:
            return [anh]

    def _tao_anh_hien_thi_xu_ly(self, anh):
        """Tao anh hien thi kieu demo: nen den, chu sang, de nhin ro bien so."""
        if cv2 is None or np is None or anh is None or anh.size == 0:
            return anh
        try:
            # Anh hien thi can sat tam bien so, khong lay ca dien thoai/tay/nen.
            vung = self._cat_vung_bien_sang(anh)
            if vung is None or vung.size == 0:
                vung = self._tinh_chinh_bien_so(anh)
                vung_sang = self._cat_vung_bien_sang(vung)
                if vung_sang is not None and vung_sang.size > 0:
                    vung = vung_sang
            if vung is None or vung.size == 0:
                vung = anh

            xam = cv2.cvtColor(vung, cv2.COLOR_BGR2GRAY) if len(vung.shape) == 3 else vung
            xam = cv2.GaussianBlur(xam, (3, 3), 0)
            xam = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(xam)

            # Adaptive threshold inverse: chu/duong vien toi -> trang, nen bien -> den.
            block = max(15, (min(xam.shape[:2]) // 4) | 1)
            nhi_phan = cv2.adaptiveThreshold(
                xam, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, block, 7
            )

            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            nhi_phan = cv2.morphologyEx(nhi_phan, cv2.MORPH_OPEN, kernel, iterations=1)
            nhi_phan = self._cat_sat_anh_hien_thi(nhi_phan)

            return cv2.cvtColor(nhi_phan, cv2.COLOR_GRAY2BGR)
        except Exception:
            return anh

    def _tao_anh_hien_thi_tu_ocr(self, anh, ocr_lines):
        """Cat anh theo vung chu OCR doc duoc roi tao anh nen den/chu trang.

        OCR da tim dung cac dong ky tu thi dung bbox cua OCR on dinh hon viec
        doan vung bien so bang nguong sang, nhat la khi bien so nam tren dien
        thoai, tay hoac nen co nhieu mang sang/toi.
        """
        if cv2 is None or np is None or anh is None or anh.size == 0 or not ocr_lines:
            return None
        h, w = anh.shape[:2]
        xs = []
        ys = []
        try:
            for dong in ocr_lines:
                if not dong or len(dong) < 2:
                    continue
                text = dong[1][0] if dong[1] else ""
                if not chuan_hoa_bien_so(text):
                    continue
                box = np.array(dong[0], dtype=np.float32)
                if box.size < 8:
                    continue
                xs.extend(box[:, 0].tolist())
                ys.extend(box[:, 1].tolist())

            if not xs or not ys:
                return None

            x1 = int(max(0, min(xs)))
            y1 = int(max(0, min(ys)))
            x2 = int(min(w, max(xs)))
            y2 = int(min(h, max(ys)))
            bw = x2 - x1
            bh = y2 - y1
            if bw < w * 0.12 or bh < h * 0.12:
                return None

            pad_x = max(8, int(bw * 0.28))
            pad_y = max(6, int(bh * 0.30))
            x1 = max(0, x1 - pad_x)
            y1 = max(0, y1 - pad_y)
            x2 = min(w, x2 + pad_x)
            y2 = min(h, y2 + pad_y)
            if x2 <= x1 or y2 <= y1:
                return None

            vung = anh[y1:y2, x1:x2]
            if vung.size == 0:
                return None
            return self._tao_anh_hien_thi_xu_ly(vung)
        except Exception:
            return None

    def _cat_vung_bien_sang(self, anh):
        """Tim tam bien so mau sang ben trong crop YOLO de anh hien thi gon hon."""
        if cv2 is None or np is None or anh is None or anh.size == 0:
            return None
        h, w = anh.shape[:2]
        if h < 30 or w < 30:
            return None

        try:
            xam = cv2.cvtColor(anh, cv2.COLOR_BGR2GRAY) if len(anh.shape) == 3 else anh.copy()
            xam = cv2.GaussianBlur(xam, (5, 5), 0)
            _, mask = cv2.threshold(xam, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            kx = max(5, (w // 45) | 1)
            ky = max(5, (h // 45) | 1)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kx, ky))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                return None

            total = h * w
            best = None
            best_score = -1.0
            for cnt in contours:
                x, y, bw, bh = cv2.boundingRect(cnt)
                if bw <= 0 or bh <= 0:
                    continue
                area = bw * bh
                area_ratio = area / total
                ratio = bw / max(1, bh)
                fill = cv2.contourArea(cnt) / max(1, area)

                if area_ratio < 0.035 or area_ratio > 0.82:
                    continue
                if bw < w * 0.22 or bh < h * 0.18:
                    continue
                if ratio < 0.65 or ratio > 4.8:
                    continue
                if fill < 0.38:
                    continue

                cx = (x + bw / 2) / w
                cy = (y + bh / 2) / h
                center_score = 1.0 - min(1.0, abs(cx - 0.5) + abs(cy - 0.5))
                bright_score = float(np.mean(xam[y:y + bh, x:x + bw])) / 255.0
                ratio_score = 1.0 - min(1.0, abs(ratio - 1.65) / 3.0)
                score = area_ratio * 2.0 + fill + center_score + bright_score + ratio_score
                if score > best_score:
                    best_score = score
                    best = (x, y, bw, bh)

            if best is None:
                return None

            x, y, bw, bh = best
            pad_x = max(2, int(bw * 0.035))
            pad_y = max(2, int(bh * 0.045))
            x1 = max(0, x - pad_x)
            y1 = max(0, y - pad_y)
            x2 = min(w, x + bw + pad_x)
            y2 = min(h, y + bh + pad_y)
            if x2 <= x1 or y2 <= y1:
                return None
            return anh[y1:y2, x1:x2]
        except Exception:
            return None

    def _cat_sat_anh_hien_thi(self, nhi_phan):
        """Cat sat vung ky tu sang de anh demo khong dinh nen/khung thua."""
        h, w = nhi_phan.shape[:2]
        if h < 20 or w < 20:
            return nhi_phan

        contours, _ = cv2.findContours(nhi_phan, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []
        dien_tich = h * w
        for cnt in contours:
            x, y, bw, bh = cv2.boundingRect(cnt)
            area = bw * bh
            if area < dien_tich * 0.001:
                continue
            if bw > w * 0.75 and bh < h * 0.16:
                continue
            if bh < h * 0.08 and bw < w * 0.08:
                continue
            if area > dien_tich * 0.55:
                continue
            boxes.append((x, y, x + bw, y + bh))

        if not boxes:
            pts = cv2.findNonZero(nhi_phan)
            if pts is None:
                return nhi_phan
            x, y, bw, bh = cv2.boundingRect(pts)
            boxes = [(x, y, x + bw, y + bh)]

        x1 = min(b[0] for b in boxes)
        y1 = min(b[1] for b in boxes)
        x2 = max(b[2] for b in boxes)
        y2 = max(b[3] for b in boxes)

        pad_x = max(4, int((x2 - x1) * 0.12))
        pad_y = max(4, int((y2 - y1) * 0.18))
        x1 = max(0, x1 - pad_x)
        y1 = max(0, y1 - pad_y)
        x2 = min(w, x2 + pad_x)
        y2 = min(h, y2 + pad_y)

        if x2 <= x1 or y2 <= y1:
            return nhi_phan
        if (x2 - x1) < w * 0.20 or (y2 - y1) < h * 0.20:
            return nhi_phan
        return nhi_phan[y1:y2, x1:x2]

    def _tinh_chinh_bien_so(self, anh):
        """Tim vung bien so trang ben trong YOLO crop, cat sat va xoay thang.

        Buoc:
        1. Chuyen xam, lam mo, nhi phan Otsu
        2. Tim contour lon nhat co dang hinh chu nhat
        3. Xoay thang (perspective transform)
        4. Tra ve anh bien so sach

        Neu khong tim thay contour phu hop -> tra ve anh goc.
        """
        if cv2 is None or np is None or anh is None or anh.size == 0:
            return anh

        h, w = anh.shape[:2]
        if h < 10 or w < 10:
            return anh

        try:
            xam = cv2.cvtColor(anh, cv2.COLOR_BGR2GRAY)
            xam = cv2.equalizeHist(xam)
            mo = cv2.GaussianBlur(xam, (5, 5), 0)
            canh = cv2.Canny(mo, 60, 180)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
            nhi_phan = cv2.morphologyEx(canh, cv2.MORPH_CLOSE, kernel, iterations=2)

            contours, _ = cv2.findContours(nhi_phan, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                return anh

            # Tim contour chu nhat phu hop bien so. Canny on dinh hon Otsu khi bi choi.
            best = None
            best_area = 0
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < h * w * 0.08:
                    continue
                rect = cv2.minAreaRect(cnt)
                rw, rh = rect[1]
                if rw == 0 or rh == 0:
                    continue
                ratio = max(rw, rh) / min(rw, rh)
                if 1.15 < ratio < 6.5 and area > best_area:
                    best = rect
                    best_area = area

            if best is None:
                return anh

            # Perspective transform de xoay thang
            box_pts = cv2.boxPoints(best)
            box_pts = np.intp(box_pts)

            # Sap xep 4 goc: trai-tren, phai-tren, phai-duoi, trai-duoi
            pts = box_pts.astype(np.float32)
            s = pts.sum(axis=1)
            d = np.diff(pts, axis=1)
            tl = pts[np.argmin(s)]
            br = pts[np.argmax(s)]
            tr = pts[np.argmin(d)]
            bl = pts[np.argmax(d)]
            src = np.array([tl, tr, br, bl], dtype=np.float32)

            # Kich thuoc dich
            rw = int(max(np.linalg.norm(tr - tl), np.linalg.norm(br - bl)))
            rh = int(max(np.linalg.norm(bl - tl), np.linalg.norm(br - tr)))
            if rw < 20 or rh < 10:
                return anh

            dst = np.array([[0, 0], [rw, 0], [rw, rh], [0, rh]], dtype=np.float32)
            M = cv2.getPerspectiveTransform(src, dst)
            warped = cv2.warpPerspective(anh, M, (rw, rh))

            # Kiem tra huong: neu dung (cao > ngang), xoay 90 do
            wh, ww = warped.shape[:2]
            if wh > ww:
                warped = cv2.rotate(warped, cv2.ROTATE_90_CLOCKWISE)

            return warped

        except Exception:
            return anh

    def _tien_xu_ly(self, anh):
        """Tao cac bien the OCR nhanh va da duoc do tot nhat: goc, CLAHE, Otsu."""
        if cv2 is None or np is None:
            return [anh]

        xam = cv2.cvtColor(anh, cv2.COLOR_BGR2GRAY) if len(anh.shape) == 3 else anh
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(xam)
        _, otsu = cv2.threshold(clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return [
            anh,
            cv2.cvtColor(clahe, cv2.COLOR_GRAY2BGR),
            cv2.cvtColor(otsu, cv2.COLOR_GRAY2BGR),
        ]

    def _diem_hop_le(self, bien_so):
        """Cham diem bien so theo format VN.

        Diem cao = dung format bien so Viet Nam.
        Day la phan TU VIET - dua tren quy tac bien so VN.

        Cac format hop le:
        - O to:      2 so + 1 chu + 5 so  = 8 ky tu  (51H59531)
        - Xe may:    2 so + 1 chu + 6 so  = 9 ky tu  (36F504327)
        - Dac biet:  2 so + 2 chu + 5 so  = 9 ky tu  (80CD12345)
        """
        bs = bien_so
        if re.fullmatch(r"\d{2}[A-Z]\d{5}", bs):
            return 1.0   # Hoan hao: o to (51H59531)
        if re.fullmatch(r"\d{2}[A-Z]\d{6}", bs):
            return 1.0   # Hoan hao: xe may (36F504327)
        if re.fullmatch(r"\d{2}[A-Z]{2}\d{5}", bs):
            return 1.0   # Hoan hao: bien dac biet (80CD12345)
        if re.fullmatch(r"\d{2}[A-Z]{1,2}\d{4,6}", bs):
            return 0.9   # Tot: bien hop le
        if re.fullmatch(r"[A-Z0-9]{7,10}", bs):
            return 0.5   # Chap nhan: dung do dai nhung khong ro format
        return 0.0

    def nhan_dien(self, anh):
        """Nhan dien bien so tu anh (numpy array BGR).

        Pipeline:
        1. YOLO cat vung bien so
        2. Tien xu ly 3 phien ban anh (tu viet)
        3. PaddleOCR doc ky tu
        4. Hau xu ly sua loi theo dac thu VN (tu viet)
        5. Chon ket qua tot nhat

        Tra ve: (bien_so, anh_vung_bien) hoac (None, None)
        """
        if anh is None or cv2 is None:
            return None, None
        if not self.ocr:
            return None, None

        # Buoc 1: YOLO cat vung
        ds_vung = self._cat_vung_yolo(anh)
        anh_hien_thi = None

        # Buoc 2+3+4: Tien xu ly + OCR + Hau xu ly
        diem_bs = {}  # {bien_so: diem}
        diem_hien_thi_tot_nhat = -1.0

        def thu_ocr(ds_anh, vung_goc):
            nonlocal anh_hien_thi, diem_hien_thi_tot_nhat
            co_ket_qua = False
            for img in ds_anh:
                try:
                    kq = self.ocr.ocr(img, cls=False)
                    if not kq or not kq[0]:
                        continue

                    # Thu thap tat ca cac text doc duoc trong anh
                    texts = []
                    avg_conf = 0.0
                    for dong in kq[0]:
                        if dong and dong[1]:
                            texts.append(dong[1][0])
                            avg_conf += float(dong[1][1])

                    if not texts:
                        continue
                    avg_conf /= len(texts)

                    # Noi tat ca cac dong lai
                    full_text = "".join(texts)

                    # Cac ung vien co the la toan bo chuoi noi lai, hoac tung dong rieng le
                    candidates = [full_text] + texts

                    for text in candidates:
                        bs = chuan_hoa_bien_so(text)
                        if len(bs) < 7 or len(bs) > 10:
                            continue
                        # Hau xu ly VN (tu viet)
                        bs = sua_loi_theo_vi_tri_vn(bs)
                        # Uu tien nhe ket qua 9 ky tu khi diem format/confidence ngang nhau,
                        # vi bien 2 dong xe may demo thuong bi mat 1 so khi crop sat mep.
                        length_bonus = 0.04 if len(bs) == 9 else (0.01 if len(bs) == 8 else 0.0)
                        diem = avg_conf + self._diem_hop_le(bs) + length_bonus
                        if diem > diem_bs.get(bs, -1):
                            diem_bs[bs] = diem
                            anh_ocr = self._tao_anh_hien_thi_tu_ocr(vung_goc, kq[0])
                            if anh_ocr is not None and diem > diem_hien_thi_tot_nhat:
                                anh_hien_thi = anh_ocr
                                diem_hien_thi_tot_nhat = diem
                            co_ket_qua = True
                except Exception:
                    continue
            return co_ket_qua

        for idx, vung in enumerate(ds_vung):
            if vung is None or vung.size == 0:
                continue
            if anh_hien_thi is None:
                anh_hien_thi = self._tao_anh_hien_thi_xu_ly(vung)

            thu_ocr(self._tien_xu_ly(vung), vung)

        if not diem_bs:
            return None, anh_hien_thi

        # Buoc 5: Chon bien so co diem cao nhat
        return max(diem_bs.items(), key=lambda x: x[1])[0], anh_hien_thi
