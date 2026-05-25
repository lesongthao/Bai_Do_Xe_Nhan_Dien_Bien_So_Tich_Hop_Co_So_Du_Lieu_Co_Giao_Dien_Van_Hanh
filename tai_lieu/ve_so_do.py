"""
Script ve so do khoi, luu do thuat toan, luong du lieu cho do an.
Xuat ra thu muc so_do/ duoi dang anh PNG 16:9.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os, sys

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'so_do')
os.makedirs(OUT, exist_ok=True)

# --- Tien ich ---
def new_fig(title, w=16, h=9):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.patch.set_facecolor('#f8f9fa')
    ax.set_title(title, fontsize=20, fontweight='bold', pad=20, fontfamily='sans-serif')
    return fig, ax

def box(ax, x, y, w, h, text, color='#3498db', fc='#eaf2f8', fs=9, lw=2, style='round,pad=0.3'):
    b = FancyBboxPatch((x, y), w, h, boxstyle=style, facecolor=fc, edgecolor=color, linewidth=lw)
    ax.add_patch(b)
    ax.text(x+w/2, y+h/2, text, ha='center', va='center', fontsize=fs, fontweight='bold', wrap=True)
    return (x+w/2, y+h/2)

def diamond(ax, cx, cy, w, h, text, color='#e67e22', fc='#fef9e7', fs=8):
    pts = [(cx, cy+h/2), (cx+w/2, cy), (cx, cy-h/2), (cx-w/2, cy)]
    from matplotlib.patches import Polygon
    p = Polygon(pts, closed=True, facecolor=fc, edgecolor=color, linewidth=2)
    ax.add_patch(p)
    ax.text(cx, cy, text, ha='c
<truncated 11099 bytes>
 '06_threading.png'), dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    print('6/7 Threading')

# ============================================================
# 7. SO DO CSDL
# ============================================================
def ve_csdl():
    fig, ax = new_fig('SO DO CO SO DU LIEU (ERD)', 14, 9)
    ax.set_xlim(0, 14)
    tables = [
        ('bien_so_hop_le', ['PK bien_so TEXT','chu_xe TEXT','tao_luc TEXT'], 1, 4),
        ('xe_trong_bai', ['PK bien_so TEXT','vao_luc TEXT'], 5.5, 4),
        ('cai_dat', ['PK khoa TEXT','gia_tri TEXT'], 10, 4),
    ]
    tcolors = ['#27ae60','#3498db','#e67e22']
    tfcs = ['#d5f5e3','#d6eaf8','#fdebd0']
    for (name, fields, x, y), tc, tfc in zip(tables, tcolors, tfcs):
        h = 0.5 + len(fields)*0.5
        box(ax, x, y+h-0.1, 3, 0.7, name, tc, tc, 11)
        for j, f in enumerate(fields):
            box(ax, x, y+h-0.8-j*0.6, 3, 0.5, f, tc, tfc, 9, lw=1)
    # Relation
    arrow(ax, 4, 5.2, 5.5, 5.2, 'Xe hop le\nmoi duoc vao')
    ax.text(7, 2.5, 'SQLite - 3 bang doc lap\nKhoa chinh: TEXT (bien so / khoa cai dat)',
            ha='center', fontsize=11, fontstyle='italic', color='#7f8c8d',
            bbox=dict(boxstyle='round', facecolor='#fef9e7', edgecolor='#f39c12'))
    fig.savefig(os.path.join(OUT, '07_erd_csdl.png'), dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    print('7/7 ERD CSDL')

# ============================================================
if __name__ == '__main__':
    print(f'Xuat so do vao: {OUT}')
    ve_tong_quan()
    ve_xe_vao()
    ve_xe_ra()
    ve_pipeline()
    ve_luong_du_lieu()
    ve_threading()
    ve_csdl()
    print(f'\nHoan tat! {len(os.listdir(OUT))} file trong {OUT}')
