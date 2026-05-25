from pathlib import Path
from xml.sax.saxutils import escape


OUT_DIR = Path(__file__).resolve().parent / "hinh_bao_cao"
OUT_DIR.mkdir(exist_ok=True)

COLORS = {
    "bg": "#f7fafc",
    "ink": "#18324a",
    "muted": "#5b6b7c",
    "blue": "#d9ecff",
    "blue2": "#9bd0ff",
    "green": "#dff7e6",
    "green2": "#88df9e",
    "yellow": "#fff3c4",
    "yellow2": "#f5ca57",
    "red": "#ffe3e3",
    "red2": "#f19191",
    "purple": "#eadfff",
    "purple2": "#bca0ff",
    "gray": "#e9eef5",
    "dark": "#102033",
    "line": "#39566f",
}


def svg_start(w, h):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
    <path d="M 0 0 L 10 5 L 0 10 z" fill="{COLORS['line']}"/>
  </marker>
  <filter id="shadow" x="-10%" y="-10%" width="120%" height="130%">
    <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#18324a" flood-opacity="0.18"/>
  </filter>
</defs>
<rect width="100%" height="100%" fill="{COLORS['bg']}"/>
"""


def svg_end():
    return "</svg>\n"


def text(x, y, s, size=16, weight="500", fill=None, anchor="middle", leading=20):
    fill = fill or COLORS["ink"]
    lines = str(s).split("\n")
    out = [f'<text x="{x}" y="{y}" text-anchor="{an
<truncated 25830 bytes>
        ("Biển số", 95.00, 97.50),
    ]
    base_y = 460
    max_h = 300
    s += '<line x1="100" y1="460" x2="800" y2="460" stroke="#39566f" stroke-width="2"/>'
    s += '<line x1="100" y1="140" x2="100" y2="460" stroke="#39566f" stroke-width="2"/>'
    s += text(230, 115, "Trước hậu xử lý", size=13, weight="700", fill="#d95f5f")
    s += text(380, 115, "Sau hậu xử lý", size=13, weight="700", fill="#2ca02c")
    for i, (name, before, after) in enumerate(data):
        x = 220 + i * 310
        before_h = (before - 90) / 10 * max_h
        after_h = (after - 90) / 10 * max_h
        s += f'<rect x="{x}" y="{base_y-before_h:.1f}" width="80" height="{before_h:.1f}" fill="#f19191" stroke="#39566f"/>'
        s += f'<rect x="{x+100}" y="{base_y-after_h:.1f}" width="80" height="{after_h:.1f}" fill="#88df9e" stroke="#39566f"/>'
        s += text(x + 40, base_y - before_h - 10, f"{before:.2f}%", size=12, weight="700")
        s += text(x + 140, base_y - after_h - 10, f"{after:.2f}%", size=12, weight="700")
        s += text(x + 90, 500, name, size=14, weight="700")
    s += text(450, 535, "Hậu xử lý giúp chọn kết quả phù hợp định dạng biển số và sửa lỗi chữ/số thường gặp.", size=13, weight="600", fill=COLORS["muted"])
    write("hinh_4_2_so_sanh_hau_xu_ly.svg", s + svg_end())


if __name__ == "__main__":
    overview()
    model_layout()
    pipeline()
    yolo_training()
    ocr_postprocess_detail()
    safe_close()
    serial()
    erd()
    modules()
    data_flow()
    flow_in()
    flow_out()
    threading_diagram()
    hardware_wiring()
    bar_chart_preprocess()
    bar_chart_postprocess()
    print(f"Da tao {len(list(OUT_DIR.glob('*.svg')))} hinh trong thu muc tai_lieu/hinh_bao_cao")
