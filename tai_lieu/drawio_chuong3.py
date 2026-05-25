"""Tao drawio Chuong 3: Hinh 3.1 - 3.16"""
import os, html
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'so_do')
os.makedirs(OUT, exist_ok=True)
def esc(s): return html.escape(s).replace('\n','&#xa;')
PW,PH=1280,720
F="Times New Roman"
SB=f"rounded=1;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#000000;fontColor=#000000;fontFamily={F};fontStyle=1;fontSize=12;strokeWidth=1.5;"
SN=f"rounded=1;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#000000;fontColor=#000000;fontFamily={F};fontStyle=0;fontSize=11;strokeWidth=1.5;"
SD=f"rhombus;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#000000;fontColor=#000000;fontFamily={F};fontStyle=0;fontSize=11;strokeWidth=1.5;"
SG=f"rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#000000;fontColor=#000000;fontFamily={F};fontStyle=1;fontSize=13;verticalAlign=top;align=center;spacingTop=5;dashed=1;strokeWidth=1.5;"
SE=f"edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;strokeColor=#000000;fontColor=#000000;fontFamily={F};fontSize=10;strokeWidth=1.5;endArrow=block;endFill=1;"
ST=f"text;html=1;align=center;verticalAlign=middle;resizable=0;points=[];autosize=1;strokeColor=none;fillColor=none;fontColor=#000000;fontFamily={F};fontStyle=1;fontSize=14;"
SL=f"rounded=1;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#000000;fontColor=#000000;fontFamily={F};fontStyle=2;fontSize=10;dashed=1;strokeWidth=1;"
SR=f"rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#000000;
<truncated 13597 bytes>
400,280,250,SN)
    o+=c("result","Vung ket qua\n\nBien so nhan dien\nAnh bien so",880,400,280,250,SN)
    return wrap(o,"Hinh 3.15")

def h316():
    o=tt("t","Hinh 3.16. Cac vung chuc nang tren giao dien phan mem",180)
    o+=c("a","[A] Camera\nHien thi video\ntruc tiep",100,80,200,100,SB)
    o+=c("b","[B] Dieu khien\nChon camera\nBat/Tat/Chup",400,80,200,100,SB)
    o+=c("cc","[C] Barie\nMo/Dong thu cong\nTrang thai",700,80,200,100,SB)
    o+=c("d","[D] Quan ly BS\nDanh sach hop le\nThem/Xoa",100,280,200,100,SB)
    o+=c("ee","[E] Log\nLich su hoat dong\nThoi gian thuc",400,280,200,100,SB)
    o+=c("f","[F] Ket qua\nBien so nhan dien\nAnh bien so",700,280,200,100,SB)
    o+=c("g","[G] Thanh trang thai\nSo xe / Suc chua\nKet noi Arduino",300,480,500,60,SB)
    o+=e("e1","a","b","Anh chup")
    o+=e("e2","b","cc","Lenh barie")
    o+=e("e3","b","f","Ket qua AI")
    o+=e("e4","d","ee","Cap nhat")
    return wrap(o,"Hinh 3.16")

if __name__=='__main__':
    fns=[("Hinh_3.01_module_phan_mem.drawio",h31),("Hinh_3.02_luu_do_tong_quat.drawio",h32),
         ("Hinh_3.03_xe_vao_tu_dong.drawio",h33),("Hinh_3.04_xe_ra.drawio",h34),
         ("Hinh_3.05_thu_cong.drawio",h35),("Hinh_3.06_dong_barie_an_toan.drawio",h36),
         ("Hinh_3.07_yolov8.drawio",h37),("Hinh_3.08_tien_xu_ly.drawio",h38),
         ("Hinh_3.09_paddleocr.drawio",h39),("Hinh_3.10_hau_xu_ly.drawio",h310),
         ("Hinh_3.11_chon_ket_qua.drawio",h311),("Hinh_3.12_erd.drawio",h312),
         ("Hinh_3.13_serial.drawio",h313),("Hinh_3.14_arduino_ket_noi.drawio",h314),
         ("Hinh_3.15_giao_dien.drawio",h315),("Hinh_3.16_vung_chuc_nang.drawio",h316)]
    for name,fn in fns:
        with open(os.path.join(OUT,name),'w',encoding='utf-8') as f: f.write(fn())
        print(f"OK: {name}")
    print("Xong Chuong 3!")
