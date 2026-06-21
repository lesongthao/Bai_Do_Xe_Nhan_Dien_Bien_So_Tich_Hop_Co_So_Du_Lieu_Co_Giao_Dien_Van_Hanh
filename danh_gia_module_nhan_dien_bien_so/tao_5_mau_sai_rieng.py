from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.font_manager import FontProperties


ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = ROOT / "danh_gia_module_nhan_dien_bien_so" / "dataset_danh_gia_200" / "images"
DATA_CSV = (
    ROOT
    / "danh_gia_module_nhan_dien_bien_so"
    / "ket_qua_danh_gia_200"
    / "du_lieu"
    / "mau_sai_tieu_bieu.csv"
)
OUTPUT_DIR = (
    ROOT
    / "danh_gia_module_nhan_dien_bien_so"
    / "ket_qua_danh_gia_200"
    / "anh_bao_cao"
    / "mau_sai_rieng"
)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FONT_PATH = Path("C:/Windows/Fonts/times.ttf")
FONT = FontProperties(fname=str(FONT_PATH), size=18) if FONT_PATH.exists() else FontProperties(size=18)

SHORT_ERROR = {
    "OCR không đọc ra ký tự": "OCR không đọc được",
    "OCR đọc thiếu ký tự": "OCR đọc thiếu ký tự",
    "Có ứng viên đúng nhưng chọn sai": "Chọn sai ứng viên",
}


def read_image_unicode(path: Path):
    data = np.fromfile(str(path), dtype=np.uint8)
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def main():
    for old_file in OUTPUT_DIR.glob("*.png"):
        old_file.unlink()

    rows = pd.read_csv(DATA_CSV, dtype=str, encoding="utf-8-sig").fillna("")
    rows = rows.sort_values("ten_anh")

    for index, row in enumerate(rows.itertuples(index=False), 1):
        image = read_image_unicode(IMAGE_DIR / row.ten_anh)
        if image is None:
            continue

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        prediction = row.du_doan_cuoi if row.du_doan_cuoi else "RỖNG"
        error = SHORT_ERROR.get(row.nhom_loi, row.nhom_loi)

        fig = plt.figure(figsize=(7.0, 6.3), facecolor="white")
        grid = fig.add_gridspec(2, 1, height_ratios=[5.0, 1.05], hspace=0.05)
        ax_image = fig.add_subplot(grid[0])
        ax_text = fig.add_subplot(grid[1])

        ax_image.imshow(image)
        ax_image.axis("off")
        ax_text.axis("off")

        note = f"Nhãn đúng: {row.ground_truth}\nDự đoán: {prediction}\nLỗi: {error}"
        ax_text.text(
            0.5,
            0.52,
            note,
            ha="center",
            va="center",
            color="black",
            fontproperties=FONT,
            linespacing=1.35,
        )

        out_path = OUTPUT_DIR / f"mau_sai_{index:02d}_{Path(row.ten_anh).stem}.png"
        fig.savefig(out_path, dpi=220, bbox_inches="tight", pad_inches=0.12)
        plt.close(fig)

    print("created_5_error_images")


if __name__ == "__main__":
    main()
