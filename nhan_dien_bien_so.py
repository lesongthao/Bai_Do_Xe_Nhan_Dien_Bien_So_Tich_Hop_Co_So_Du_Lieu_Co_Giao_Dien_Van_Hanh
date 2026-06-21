"""
Module nhan dien bien so xe.
Pipeline: YOLOv8 tim vung bien -> tien xu ly anh -> PaddleOCR doc ky tu -> hau xu ly VN.
"""

# Luu y: OMP_NUM_THREADS=1 duoc dat trong giao_dien_chinh.py (entry point)
# Khong can dat lai o day de tranh trung lap.

import os
import re
from pathlib import Path

MIN_PLATE_LENGTH = 7
MAX_PLATE_LENGTH = 10
_ONLY_ALNUM_RE = re.compile(r"[^A-Z0-9]+")

_TO_DIGIT = {
    "O": "0",
    "Q": "0",
    "D": "0",
    "I": "1",
    "L": "1",
    "A": "4",
    "T": "7",
    "Z": "2",
    "S": "5",
    "G": "6",
    "B": "8",
}

_TO_LETTER = {
    "0": "O",
    "1": "I",
    "4": "A",
    "7": "T",
    "2": "Z",
    "5": "S",
    "6": "G",
    "8": "B",
}


def chuan_hoa_bien_so(text: str | None) -> str:
    """Chuan hoa chuoi bien so ve dang A-Z0-9 lien nhau."""
    if text is None:
        return ""
    text = str(text).upper().strip()
    if not text:
        return ""
    return _ONLY_ALNUM_RE.sub("", text)


def la_bien_so_hop_cau_truc(bien_so: str | None) -> bool:
    """Kiem tra cau truc bien so da chot cho do an."""
    bs = chuan_hoa_bien_so(bien_so)
    if not (MIN_PLATE_LENGTH <= len(bs) <= MAX_PLATE_LENGTH):
        return False
    if not bs[:2].isdigit():
        return False
    if not (11 <= int(bs[:2]) <= 99):
        return False
    if not bs[2].isalpha():
        return False
    ky_tu_thu_4 = bs[3]
    if not ky_tu_thu_4.isalnum():
        return False
    return bs[4:].isdigit()


def _expects_letter(index: int) -> bool:
    return index == 2


def _expects_digit(index: int) -> bool:
    return index in (0, 1) or index >= 4


def sua_loi_theo_vi_tri_vn(bien_so: str | None) -> str:
    """Sua loi OCR pho bien theo vi tri ky tu cua cau truc do an."""
    src = chuan_hoa_bien_so(bien_so)
    if not src:
        return ""

    out = []
    for i, ch in enumerate(src):
        if _expects_letter(i):
            out.append(_TO_LETTER.get(ch, ch))
        elif _expects_digit(i):
            out.append(_TO_DIGIT.get(ch, ch))
        else:
            out.append(ch)
    return "".join(out)


def dem_so_ky_tu_da_sua(raw_text: str | None, fixed_text: str | None) -> int:
    raw = chuan_hoa_bien_so(raw_text)
    fixed = chuan_hoa_bien_so(fixed_text)
    shared = min(len(raw), len(fixed))
    diff = sum(1 for i in range(shared) if raw[i] != fixed[i])
    diff += abs(len(raw) - len(fixed))
    return diff


def dinh_dang_hien_thi(bien_so: str | None) -> str:
    bs = chuan_hoa_bien_so(bien_so)
    if not bs:
        return ""
    return bs

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
                # PaddleOCR 2.x dung show_log=False, 3.x da xoa tham so nay
                try:
                    self.ocr = PaddleOCR(use_angle_cls=False, lang="en", show_log=False)
                except TypeError:
                    # PaddleOCR 3.x: tat log bang logging module
                    import logging
                    logging.getLogger("ppocr").setLevel(logging.ERROR)
                    logging.getLogger("paddleocr").setLevel(logging.ERROR)
                    self.ocr = PaddleOCR(use_angle_cls=False, lang="en")
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
        """Tra ve anh YOLO crop goc de hien thi tren giao dien."""
        if anh is None or (hasattr(anh, 'size') and anh.size == 0):
            return anh
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

    def _thu_hang_ung_vien(self, valid, so_sua, so_lan, best_conf):
        """Thu hang ung vien theo quy tac da chot cho do an."""
        return (
            1 if valid else 0,
            -int(so_sua),
            int(so_lan),
            float(best_conf),
        )

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
        ung_vien = {}

        def thu_ocr(ds_anh, vung_goc):
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

                    # Moi anh tien xu ly chi sinh 1 ung vien dai dien
                    raw_text = "".join(texts)
                    normalized = chuan_hoa_bien_so(raw_text)
                    if not normalized:
                        continue

                    fixed = sua_loi_theo_vi_tri_vn(normalized)
                    if not fixed:
                        continue

                    valid = la_bien_so_hop_cau_truc(fixed)
                    so_sua = dem_so_ky_tu_da_sua(normalized, fixed)
                    anh_ocr = self._tao_anh_hien_thi_tu_ocr(vung_goc, kq[0])

                    info = ung_vien.get(fixed)
                    if info is None:
                        ung_vien[fixed] = {
                            "valid": valid,
                            "so_sua": so_sua,
                            "so_lan": 1,
                            "best_conf": avg_conf,
                            "anh": anh_ocr,
                        }
                    else:
                        info["valid"] = info["valid"] or valid
                        info["so_sua"] = min(int(info["so_sua"]), so_sua)
                        info["so_lan"] = int(info["so_lan"]) + 1
                        if avg_conf > float(info["best_conf"]):
                            info["best_conf"] = avg_conf
                            if anh_ocr is not None:
                                info["anh"] = anh_ocr
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

        if not ung_vien:
            return None, anh_hien_thi

        # Buoc 5: Chon bien so theo thu tu uu tien da chot
        bien_so, info = max(
            ung_vien.items(),
            key=lambda item: self._thu_hang_ung_vien(
                item[1]["valid"], item[1]["so_sua"], item[1]["so_lan"], item[1]["best_conf"]
            ),
        )
        if info.get("anh") is not None:
            anh_hien_thi = info["anh"]
        return bien_so, anh_hien_thi
