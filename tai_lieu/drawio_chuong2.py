"""Tao drawio Chuong 2: Hinh 2.1 - 2.8"""
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
def wrap(cells,name):
    return f'''<?xml version="1.0" encoding="UTF
<truncated 7523 bytes>
n-->",200,220,180,40,SL)
    o+=c("sv2","Servo barie\nRA",650,130,130,50,SN)
    o+=c("cb2","Cam bien\nhong ngoai RA",810,130,130,50,SN)
    o+=c("car2","Huong xe ra\n-->",700,220,180,40,SL)
    o+=c("cam","Camera\n(dat tai cong vao)",250,310,200,50,SN)
    o+=c("ard","Arduino Uno\n(dieu khien chung)",400,430,200,50,SB)
    o+=e("e1","sv1","ard")
    o+=e("e2","cb1","ard")
    o+=e("e3","sv2","ard")
    o+=e("e4","cb2","ard")
    o+=e("e5","cam","ard","USB")
    o+=c("note","Cam bien dat TRUOC barie\nde phat hien xe den truoc khi mo",550,530,350,40,SL)
    return wrap(o,"Hinh 2.7")

def h28():
    o=tt("t","Hinh 2.8. Nguyen ly co che an toan khi dong barie",200)
    o+=c("a1","Yeu cau DONG barie",450,70,300,50,SB)
    o+=c("a2","Cam bien tai cong\ncon phat hien xe?",480,180,240,100,SD)
    o+=c("a3","KHONG dong\nDanh dau cho dong",800,200,200,50,SN)
    o+=c("a4","Kiem tra lai\nmoi 500ms",800,310,200,50,SN)
    o+=c("a5","Gui lenh DONG\nden Arduino",450,360,300,50,SN)
    o+=c("a6","Servo dong barie\nAN TOAN",450,470,300,50,SB)
    o+=e("ea1","a1","a2")
    o+=e("ea2","a2","a3","Co xe")
    o+=e("ea3","a3","a4")
    o+=e("ea4","a4","a2","Lap lai")
    o+=e("ea5","a2","a5","Khong co xe")
    o+=e("ea6","a5","a6")
    return wrap(o,"Hinh 2.8")

if __name__=='__main__':
    for name,fn in [("Hinh_2.1_so_do_tong_the.drawio",h21),("Hinh_2.2_kien_truc.drawio",h22),
        ("Hinh_2.3_pipeline.drawio",h23),("Hinh_2.4_dieu_khien.drawio",h24),
        ("Hinh_2.5_luong_du_lieu.drawio",h25),("Hinh_2.6_giao_tiep_serial.drawio",h26),
        ("Hinh_2.7_bo_tri_cam_bien.drawio",h27),("Hinh_2.8_an_toan_barie.drawio",h28)]:
        with open(os.path.join(OUT,name),'w',encoding='utf-8') as f: f.write(fn())
        print(f"OK: {name}")
    print("Xong Chuong 2!")
