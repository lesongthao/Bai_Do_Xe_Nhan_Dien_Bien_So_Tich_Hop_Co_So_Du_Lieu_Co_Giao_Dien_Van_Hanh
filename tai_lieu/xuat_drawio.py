"""
Tao file .drawio: A4 doc, nen trang, chu den, Times New Roman, vien den, khong mau nen.
"""
import os, html

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'so_do')
os.makedirs(OUT, exist_ok=True)

def esc(s):
    return html.escape(s).replace('\n','&#xa;')

# A4 portrait: 827 x 1169 (at 96 DPI)
PW, PH = 827, 1169
FONT = "Times New Roman"

def drawio_wrap(cells_xml, page_name="Page-1"):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" type="device">
  <diagram id="d1" name="{esc(page_name)}">
    <mxGraphModel dx="1100" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{PW}" pageHeight="{PH}" background="#FFFFFF" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
{cells_xml}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''

# --- Styles ---
def S_BOX(fs=12):
    return f"rounded=1;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#000000;fontColor=#000000;fontFamily={FONT};fontStyle=0;fontSize={fs};strokeWidth=1.5;"

def S_BOX_BOLD(fs=12):
    return f"rounded=1;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#000000;fontColor=#000000;fontFamily={FONT};fontStyle=1;fontSize={fs};strokeWidth=1.5;"

S_DIA = f"rhombus;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#000000;fontColor=#000000;fontFa
<truncated 12379 bytes>
ồ CSDL (ERD)")

# ============================================================
# 8. CO CHE AN TOAN
# ============================================================
def an_toan():
    c = title_cell("tt","CƠ CHẾ AN TOÀN BARIE")
    c += cell("a1","Yêu cầu ĐÓNG barie\n(thủ công hoặc tự động)",S_BOX_BOLD(),250,80,280,55)
    c += cell("a2","Cảm biến tại cổng\ncòn phát hiện xe?",S_DIA,310,190,160,100)
    c += cell("a3","KHÔNG đóng\nĐánh dấu chờ đóng",S_BOX(),560,210,180,50)
    c += cell("a4","Kiểm tra lại\nmỗi 500ms",S_BOX(),560,310,180,50)
    c += cell("a5","Gửi lệnh ĐÓNG\nđến Arduino",S_BOX(),250,350,280,55)
    c += cell("a6","Servo đóng barie\nAn toàn!",S_BOX_BOLD(),250,455,280,55)
    c += edge("ea1","a1","a2")
    c += edge("ea2","a2","a3","Có xe")
    c += edge("ea3","a3","a4")
    c += edge("ea4","a4","a2","Lặp lại")
    c += edge("ea5","a2","a5","Không có xe")
    c += edge("ea6","a5","a6")
    return drawio_wrap(c, "Cơ chế an toàn barie")

# ============================================================
if __name__ == '__main__':
    diagrams = [
        ("01_so_do_tong_quan.drawio", tong_quan),
        ("02_luu_do_xe_vao.drawio", xe_vao),
        ("03_luu_do_xe_ra.drawio", xe_ra),
        ("04_pipeline_nhan_dien.drawio", pipeline),
        ("05_luong_du_lieu.drawio", luong_du_lieu),
        ("06_threading.drawio", threading_diagram),
        ("07_erd_csdl.drawio", erd),
        ("08_co_che_an_toan.drawio", an_toan),
    ]
    for fname, func in diagrams:
        path = os.path.join(OUT, fname)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(func())
        print(f"OK: {fname}")
    print(f"\nXuat {len(diagrams)} file .drawio vao {OUT}")
