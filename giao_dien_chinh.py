"""
Giao dien he thong bai do xe.
Chay: python giao_dien_chinh.py
"""

import os
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

try:
    import cv2
except Exception:
    cv2 = None

try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None

from dieu_khien_he_thong import DieuKhienHeThong
from nhan_dien_bien_so import dinh_dang_hien_thi

APP_BG = "#dbeafe"
HEADER_BG = "#6fd9ea"
HEADER_TEXT = "#0f2b4d"
CARD_BG = "#eaf4ff"
TEXT = "#1b2a41"
MUTED = "#6a7890"
INPUT_BG = "#f0f8ff"
CAM_BG = "#ffffff"
PLATE_BG = "#ffffff"
ORANGE_BORDER = "#111111"
BTN_CYAN = "#74d7e4"
BTN_GREEN = "#89e8ad"
BTN_RED = "#f29aa2"
BTN_YELLOW = "#f4c542"
BTN_PINK = "#f7b1b5"
BTN_BLUE = "#59c7db"
BTN_PEACH = "#f2d2b3"
BTN_MUTED = "#d8e0ea"
BTN_MUTED_TEXT = "#66748a"
BTN_MANUAL_ACTIVE = BTN_YELLOW
BTN_AUTO_ACTIVE = BTN_YELLOW
BTN_GATE_CLOSED = "#f2a0aa"
BTN_GATE_OPEN = "#83e6a7"
BTN_DISABLED = "#cbd5e1"
BTN_DISABLED_TEXT = "#64748b"
DELETE_PLACEHOLDER = "Xem danh s\u00e1ch"
CAM_VIEW_W = 308
CAM_VIEW_H = 174
PROC_VIEW_W = 260
PROC_VIEW_H = 112
PROC_PANEL_H = 138
PROC_MAX_W = 300
PROC_MAX_H = 126
PLATE_TEXT_H = 72


class GiaoDienBaiXe:
    def __init__(self):
        self.root = tk.Tk()
        current_scaling = float(self.root.tk.call("tk", "scaling"))
        self.root.tk.call("tk", "scaling", current_scaling * 0.9)
        self.root.title("Giao di\u1ec7n qu\u1ea3n l\u00fd b\u00e3i xe")
        self.root.geometry("1220x680")
        self.root.minsize(1120, 640)
        self.root.configure(bg=APP_BG)
        self.root.protocol("WM_DELETE_WINDOW", self._thoat)

        self._photo_cam = {"vao": None, "ra": None}
        self._photo_plate = {"vao": None, "ra": None}
        self._poll_after_id = None
        self.var_cam_vao = tk.StringVar(value="Cam 0")
        self.var_cam_ra = tk.StringVar(value="Cam 1")
        self.var_plate = tk.StringVar(value=DELETE_PLACEHOLDER)
        self.var_com = tk.StringVar(value="Chon cong COM")
        self._plate_display_to_raw = {}
        self._last_camera_choices = None
        self._last_plate_keys = None
        self._last_latest_rgb_id = {"vao": None, "ra": None}

        self.controller = DieuKhienHeThong(
            on_log=self._log,
            on_state_change=self._refresh_ui,
            on_plate_result=self._on_plate_result,
            on_messagebox=lambda title, msg: messagebox.askyesno(title, msg),
        )

        self._build_ui()
        self._quet_camera(show_error=False)
        self._refresh_ui()

    def _build_ui(self):
        header = tk.Frame(self.root, bg=HEADER_BG, height=70, bd=0, relief=tk.SOLID,
                          highlightbackground=ORANGE_BORDER, highlightcolor=ORANGE_BORDER, highlightthickness=3)
        header.pack(fill=tk.X, padx=6, pady=(6, 4))
        header.pack_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)
        header.grid_columnconfigure(2, weight=1)

        tk.Label(
            header,
            text="GIAO DI\u1ec6N QU\u1ea2N L\u00dd B\u00c3I XE",
            bg=HEADER_BG,
            fg=HEADER_TEXT,
            font=("Segoe UI", 23, "bold"),
        ).place(relx=0.5, rely=0.5, anchor="center")

        tk.Button(header, text="RELOAD", command=self._reload,
                  **self._btn_style(BTN_YELLOW, padx=16, pady=8)).pack(side=tk.RIGHT, padx=(0, 8))
        tk.Button(header, text="THO\u00c1T", command=self._thoat,
                  **self._btn_style(BTN_PINK, fg="#3d2430", padx=20, pady=8)).pack(side=tk.RIGHT, padx=10)

        body = tk.Frame(self.root, bg=APP_BG)
        body.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))
        body.grid_columnconfigure(0, weight=7, minsize=710)
        body.grid_columnconfigure(1, weight=4, minsize=390)
        body.grid_rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=APP_BG, bd=0, relief=tk.SOLID,
                        highlightbackground=ORANGE_BORDER, highlightcolor=ORANGE_BORDER, highlightthickness=3)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left.grid_columnconfigure(0, weight=1)

        right = tk.Frame(body, bg=APP_BG, bd=0, relief=tk.SOLID,
                         highlightbackground=ORANGE_BORDER, highlightcolor=ORANGE_BORDER, highlightthickness=3)
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        right.grid_rowconfigure(2, weight=1)
        right.grid_rowconfigure(3, weight=1)
        right.grid_columnconfigure(0, weight=1)

        # Left pane
        cam_source_row = tk.Frame(left, bg=APP_BG)
        cam_source_row.pack(fill=tk.X, padx=12, pady=(8, 6))
        for i in range(6):
            cam_source_row.grid_columnconfigure(i, weight=1 if i == 5 else 0)

        tk.Label(cam_source_row, text="V\u00e0o", bg=APP_BG, fg=TEXT, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=(0, 4))
        self.opt_cam_vao = ttk.Combobox(cam_source_row, textvariable=self.var_cam_vao, state="readonly",
                                        font=("Segoe UI", 10), width=10)
        self.opt_cam_vao.bind("<<ComboboxSelected>>", lambda _e: self._chon_camera("vao", self.var_cam_vao.get()))
        self.opt_cam_vao.grid(row=0, column=1, sticky="w", padx=(0, 8), ipady=1)
        tk.Button(cam_source_row, text="B\u1eadt", command=lambda: self._bat_cam("vao"), **self._btn_style(BTN_GREEN, padx=8)).grid(row=0, column=2, sticky="ew", padx=2)
        tk.Button(cam_source_row, text="T\u1eaft", command=lambda: self._tat_cam("vao"), **self._btn_style(BTN_RED, padx=8)).grid(row=0, column=3, sticky="ew", padx=2)
        tk.Button(cam_source_row, text="Ch\u1ee5p", command=lambda: self._chup("vao"), **self._btn_style(BTN_YELLOW, padx=8)).grid(row=0, column=4, sticky="ew", padx=2)

        tk.Label(cam_source_row, text="Ra", bg=APP_BG, fg=TEXT, font=("Segoe UI", 10, "bold")).grid(row=1, column=0, padx=(0, 4), pady=(4, 0))
        self.opt_cam_ra = ttk.Combobox(cam_source_row, textvariable=self.var_cam_ra, state="readonly",
                                       font=("Segoe UI", 10), width=10)
        self.opt_cam_ra.bind("<<ComboboxSelected>>", lambda _e: self._chon_camera("ra", self.var_cam_ra.get()))
        self.opt_cam_ra.grid(row=1, column=1, sticky="w", padx=(0, 8), pady=(4, 0), ipady=1)
        tk.Button(cam_source_row, text="B\u1eadt", command=lambda: self._bat_cam("ra"), **self._btn_style(BTN_GREEN, padx=8)).grid(row=1, column=2, sticky="ew", padx=2, pady=(4, 0))
        tk.Button(cam_source_row, text="T\u1eaft", command=lambda: self._tat_cam("ra"), **self._btn_style(BTN_RED, padx=8)).grid(row=1, column=3, sticky="ew", padx=2, pady=(4, 0))
        tk.Button(cam_source_row, text="Ch\u1ee5p", command=lambda: self._chup("ra"), **self._btn_style(BTN_YELLOW, padx=8)).grid(row=1, column=4, sticky="ew", padx=2, pady=(4, 0))

        status_compact = tk.Frame(
            cam_source_row, bg=CARD_BG, bd=0, relief=tk.SOLID,
            highlightbackground=ORANGE_BORDER, highlightcolor=ORANGE_BORDER, highlightthickness=3,
        )
        status_compact.grid(row=0, column=5, rowspan=2, sticky="nsew", padx=(18, 0), pady=(0, 0))
        status_compact.grid_columnconfigure(0, weight=1)
        status_compact.grid_rowconfigure(0, weight=1)
        status_compact.grid_rowconfigure(1, weight=1)
        self.lbl_status = tk.Label(
            status_compact,
            text="C\u00d2N CH\u1ed6 TR\u1ed0NG",
            bg=BTN_GREEN,
            fg=TEXT,
            font=("Segoe UI", 13, "bold"),
            padx=18,
            pady=4,
            highlightbackground=ORANGE_BORDER,
            highlightcolor=ORANGE_BORDER,
            highlightthickness=2,
        )
        self.lbl_status.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 3))
        self.lbl_slot = tk.Label(
            status_compact,
            text="0/3",
            bg=BTN_GREEN,
            fg=TEXT,
            font=("Segoe UI", 15, "bold"),
            padx=18,
            pady=2,
            highlightbackground=ORANGE_BORDER,
            highlightcolor=ORANGE_BORDER,
            highlightthickness=2,
        )
        self.lbl_slot.grid(row=1, column=0, pady=(0, 6))

        cam_preview_row = tk.Frame(left, bg=APP_BG, height=CAM_VIEW_H + 22)
        cam_preview_row.pack(fill=tk.X, padx=12, pady=(0, 6))
        cam_preview_row.pack_propagate(False)
        cam_preview_row.grid_columnconfigure(0, weight=1, minsize=CAM_VIEW_W + 8)
        cam_preview_row.grid_columnconfigure(1, weight=1, minsize=CAM_VIEW_W + 8)
        cam_preview_row.grid_rowconfigure(1, minsize=CAM_VIEW_H + 2)

        tk.Label(cam_preview_row, text="C\u1ed4NG V\u00c0O", bg=APP_BG, fg=TEXT,
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 4), pady=(0, 1))
        tk.Label(cam_preview_row, text="C\u1ed4NG RA", bg=APP_BG, fg=TEXT,
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=1, sticky="w", padx=(4, 0), pady=(0, 1))

        self.cam_wrap_vao = tk.Frame(cam_preview_row, bg=CAM_BG, width=CAM_VIEW_W, height=CAM_VIEW_H, bd=0, relief=tk.SOLID,
                                      highlightbackground=ORANGE_BORDER, highlightcolor=ORANGE_BORDER, highlightthickness=3)
        self.cam_wrap_vao.grid(row=1, column=0, padx=(0, 4), sticky="n")
        self.cam_wrap_vao.pack_propagate(False)
        self.cam_wrap_vao.grid_propagate(False)
        self.lbl_cam_vao = tk.Label(self.cam_wrap_vao, text="Camera v\u00e0o", bg=CAM_BG, fg=TEXT, font=("Segoe UI", 11))
        self.lbl_cam_vao.pack(fill=tk.BOTH, expand=True)

        self.cam_wrap_ra = tk.Frame(cam_preview_row, bg=CAM_BG, width=CAM_VIEW_W, height=CAM_VIEW_H, bd=0, relief=tk.SOLID,
                                     highlightbackground=ORANGE_BORDER, highlightcolor=ORANGE_BORDER, highlightthickness=3)
        self.cam_wrap_ra.grid(row=1, column=1, padx=(4, 0), sticky="n")
        self.cam_wrap_ra.pack_propagate(False)
        self.cam_wrap_ra.grid_propagate(False)
        self.lbl_cam_ra = tk.Label(self.cam_wrap_ra, text="Camera ra", bg=CAM_BG, fg=TEXT, font=("Segoe UI", 11))
        self.lbl_cam_ra.pack(fill=tk.BOTH, expand=True)

        plate_panel = tk.Frame(left, bg=APP_BG)
        plate_panel.pack(fill=tk.X, padx=12, pady=(4, 0))
        plate_panel.grid_columnconfigure(0, weight=1)
        plate_panel.grid_columnconfigure(1, weight=1)
        self.plate_image_wrap = {}
        self.lbl_plate_image = {}
        self.lbl_plate_text = {}

        for col, cong, title in ((0, "vao", "Bi\u1ec3n s\u1ed1 v\u00e0o"), (1, "ra", "Bi\u1ec3n s\u1ed1 ra")):
            result_col = tk.Frame(plate_panel, bg=APP_BG)
            result_col.grid(row=0, column=col, sticky="nsew", padx=(0, 4) if cong == "vao" else (4, 0))
            result_col.grid_columnconfigure(0, weight=1)

            tk.Label(result_col, text=title, bg=APP_BG, fg=TEXT,
                     font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 2))

            image_panel = tk.Frame(result_col, bg=APP_BG, height=PROC_PANEL_H, bd=0, relief=tk.SOLID,
                                   highlightbackground=ORANGE_BORDER, highlightcolor=ORANGE_BORDER, highlightthickness=3)
            image_panel.grid(row=1, column=0, sticky="ew", pady=(0, 4))
            image_panel.grid_propagate(False)
            image_panel.grid_columnconfigure(0, weight=1)
            image_panel.grid_rowconfigure(0, weight=1)

            self.plate_image_wrap[cong] = tk.Frame(image_panel, bg=PLATE_BG, width=PROC_VIEW_W, height=PROC_VIEW_H, bd=0, relief=tk.SOLID,
                                                   highlightbackground=ORANGE_BORDER, highlightcolor=ORANGE_BORDER, highlightthickness=3)
            self.plate_image_wrap[cong].grid(row=0, column=0, padx=6, pady=6, sticky="")
            self.plate_image_wrap[cong].pack_propagate(False)
            self.plate_image_wrap[cong].grid_propagate(False)
            self.lbl_plate_image[cong] = tk.Label(
                self.plate_image_wrap[cong],
                text="--\n----",
                bg=PLATE_BG,
                fg=TEXT,
                font=("Consolas", 18, "bold"),
            )
            self.lbl_plate_image[cong].pack(fill=tk.BOTH, expand=True)

            text_panel = tk.Frame(result_col, bg=APP_BG, height=PLATE_TEXT_H + 12, bd=0, relief=tk.SOLID,
                                  highlightbackground=ORANGE_BORDER, highlightcolor=ORANGE_BORDER, highlightthickness=3)
            text_panel.grid(row=2, column=0, sticky="ew", pady=(0, 4))
            text_panel.grid_propagate(False)
            text_panel.grid_columnconfigure(0, weight=1)
            text_panel.grid_rowconfigure(0, weight=1)

            result_wrap = tk.Frame(text_panel, bg="white", bd=0, relief=tk.SOLID, width=PROC_MAX_W, height=PLATE_TEXT_H,
                                   highlightbackground=ORANGE_BORDER, highlightcolor=ORANGE_BORDER, highlightthickness=3)
            result_wrap.grid(row=0, column=0, sticky="", padx=6, pady=6)
            result_wrap.grid_propagate(False)
            result_wrap.pack_propagate(False)
            self.lbl_plate_text[cong] = tk.Label(
                result_wrap,
                text="---",
                bg="white",
                fg="#101010",
                font=("Consolas", 23, "bold"),
            )
            self.lbl_plate_text[cong].pack(fill=tk.BOTH, expand=True)

        # Right pane
        mode_card = self._card(right)
        mode_card.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        mode_grid = tk.Frame(mode_card, bg=CARD_BG)
        mode_grid.pack(fill=tk.X, padx=8, pady=8)
        mode_grid.grid_columnconfigure(0, weight=1)
        mode_grid.grid_columnconfigure(1, weight=1)
        self.btn_manual = tk.Button(mode_grid, text="TH\u1ee6 C\u00d4NG", command=lambda: self.controller.mode("thu_cong", schedule=lambda ms, fn: self.root.after(ms, fn)), **self._btn_style(BTN_RED))
        self.btn_manual.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.btn_auto = tk.Button(mode_grid, text="T\u1ef0 \u0110\u1ed8NG", command=lambda: self.controller.mode("tu_dong", schedule=lambda ms, fn: self.root.after(ms, fn)), **self._btn_style(BTN_GREEN))
        self.btn_auto.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        self.btn_gate_in = tk.Button(mode_grid, text="C\u1ed5ng v\u00e0o", command=lambda: self.controller.barie_click("vao", schedule=lambda ms, fn: self.root.after(ms, fn)), **self._btn_style(BTN_PINK))
        self.btn_gate_in.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=(4, 0))
        self.btn_gate_out = tk.Button(mode_grid, text="C\u1ed5ng ra", command=lambda: self.controller.barie_click("ra", schedule=lambda ms, fn: self.root.after(ms, fn)), **self._btn_style(BTN_RED))
        self.btn_gate_out.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(4, 0))

        # --- COM Port selector ---
        com_frame = tk.Frame(mode_card, bg=CARD_BG)
        com_frame.pack(fill=tk.X, padx=8, pady=(6, 8))
        com_frame.grid_columnconfigure(0, weight=1)
        com_frame.grid_columnconfigure(1, weight=0)
        com_frame.grid_columnconfigure(2, weight=0)

        self.cmb_com = ttk.Combobox(com_frame, textvariable=self.var_com, state="readonly",
                                    font=("Segoe UI", 10), width=12)
        self.cmb_com["values"] = ["Chon cong COM"]
        self.cmb_com.grid(row=0, column=0, sticky="ew", padx=(0, 4), ipady=2)

        tk.Button(com_frame, text="\u21bb", command=self._quet_com,
                  font=("Segoe UI", 11, "bold"), bg=BTN_BLUE, fg="#21344e",
                  relief=tk.FLAT, bd=0, cursor="hand2", padx=8, pady=4
        ).grid(row=0, column=1, padx=2)

        self.btn_com_connect = tk.Button(com_frame, text="K\u1ebft n\u1ed1i",
                                         command=self._ket_noi_com, **self._btn_style(BTN_GREEN))
        self.btn_com_connect.grid(row=0, column=2, padx=(2, 0))

        self.lbl_com_status = tk.Label(com_frame, text="Ch\u01b0a k\u1ebft n\u1ed1i",
                                       bg=CARD_BG, fg=MUTED, font=("Segoe UI", 9))
        self.lbl_com_status.grid(row=1, column=0, columnspan=3, sticky="w", pady=(2, 0))

        # Quet COM ports khi khoi dong
        self._quet_com()

        plate_card = self._card(right)
        plate_card.grid(row=1, column=0, sticky="ew", padx=10, pady=(4, 2))
        plate_card.grid_columnconfigure(0, weight=1)
        plate_card.grid_columnconfigure(1, weight=0)
        plate_card.grid_rowconfigure(0, weight=1, uniform="plate_row")
        plate_card.grid_rowconfigure(1, weight=1, uniform="plate_row")

        self.ent_plate = tk.Entry(plate_card, font=("Segoe UI", 10), bg="white", fg=TEXT, relief=tk.SOLID, bd=1)
        self.ent_plate.grid(row=0, column=0, sticky="ew", padx=(6, 4), pady=(4, 2), ipady=2)
        tk.Button(plate_card, text="TH\u00caM", command=self._add_plate, **self._btn_style(BTN_GREEN, padx=8, pady=3)).grid(row=0, column=1, sticky="nsew", padx=(0, 6), pady=(4, 2))

        self.cmb_plate = ttk.Combobox(plate_card, textvariable=self.var_plate, state="readonly", font=("Segoe UI", 10))
        self.cmb_plate.grid(row=1, column=0, sticky="ew", padx=(6, 4), pady=(2, 4), ipady=2)
        self.cmb_plate["values"] = [DELETE_PLACEHOLDER]
        self.cmb_plate.set(DELETE_PLACEHOLDER)
        self.cmb_plate.bind("<<ComboboxSelected>>", lambda _e: self._refresh_delete_placeholder_style())
        tk.Button(plate_card, text="X\u00d3A", command=self._del_plate, **self._btn_style(BTN_RED, padx=8, pady=3)).grid(row=1, column=1, sticky="nsew", padx=(0, 6), pady=(2, 4))
        self._refresh_delete_placeholder_style()

        # === NHAT KY HE THONG (tren) ===
        log_sys_card = self._card(right)
        log_sys_card.grid(row=2, column=0, sticky="nsew", padx=10, pady=(6, 3))
        tk.Label(log_sys_card, text="H\u1ec7 th\u1ed1ng", bg=HEADER_TEXT, fg="white", font=("Segoe UI", 10, "bold"), padx=8, pady=2).pack(fill=tk.X, padx=6, pady=(6, 0))
        self.txt_log_sys = tk.Text(
            log_sys_card, height=3, state=tk.DISABLED,
            font=("Consolas", 9, "bold"), bg="#0f172a", fg="#e5f3ff",
            insertbackground="#e5f3ff", relief=tk.SOLID, bd=2, padx=8, pady=4,
        )
        self.txt_log_sys.pack(fill=tk.BOTH, expand=True, padx=6, pady=(4, 6))

        # === NHAT KY CONG VAO / CONG RA (duoi, chia doi) ===
        log_gate_card = self._card(right)
        log_gate_card.grid(row=3, column=0, sticky="nsew", padx=10, pady=(3, 10))
        log_gate_card.grid_columnconfigure(0, weight=1)
        log_gate_card.grid_columnconfigure(1, weight=1)
        log_gate_card.grid_rowconfigure(1, weight=1)

        tk.Label(log_gate_card, text="C\u1ed5ng v\u00e0o", bg="#1a5276", fg="white", font=("Segoe UI", 10, "bold"), padx=8, pady=2).grid(row=0, column=0, sticky="ew", padx=(6, 3), pady=(6, 0))
        tk.Label(log_gate_card, text="C\u1ed5ng ra", bg="#7b241c", fg="white", font=("Segoe UI", 10, "bold"), padx=8, pady=2).grid(row=0, column=1, sticky="ew", padx=(3, 6), pady=(6, 0))

        self.txt_log_vao = tk.Text(
            log_gate_card, height=3, state=tk.DISABLED,
            font=("Consolas", 9, "bold"), bg="#0c1a2e", fg="#a8d8ff",
            insertbackground="#a8d8ff", relief=tk.SOLID, bd=2, padx=8, pady=4,
        )
        self.txt_log_vao.grid(row=1, column=0, sticky="nsew", padx=(6, 3), pady=(4, 6))

        self.txt_log_ra = tk.Text(
            log_gate_card, height=3, state=tk.DISABLED,
            font=("Consolas", 9, "bold"), bg="#2a0c0c", fg="#ffb8b8",
            insertbackground="#ffb8b8", relief=tk.SOLID, bd=2, padx=8, pady=4,
        )
        self.txt_log_ra.grid(row=1, column=1, sticky="nsew", padx=(3, 6), pady=(4, 6))

    def _card(self, parent):
        return tk.Frame(parent, bg=CARD_BG, bd=0, relief=tk.SOLID,
                        highlightbackground=ORANGE_BORDER, highlightcolor=ORANGE_BORDER, highlightthickness=3)

    def _btn_style(self, bg, fg="#21344e", padx=10, pady=7):
        return {"font": ("Segoe UI", 11, "bold"), "bg": bg, "fg": fg,
                "activebackground": bg, "activeforeground": fg,
                "relief": tk.SOLID, "bd": 1, "cursor": "hand2",
                "highlightbackground": ORANGE_BORDER,
                "highlightcolor": ORANGE_BORDER,
                "highlightthickness": 1,
                "padx": padx, "pady": pady}

    def _refresh_delete_placeholder_style(self):
        color = "#99a5b7" if self.var_plate.get() == DELETE_PLACEHOLDER else TEXT
        self.cmb_plate.configure(foreground=color)

    def _log(self, msg, cong=None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {msg}\n"

        if cong == "vao":
            widget = self.txt_log_vao
        elif cong == "ra":
            widget = self.txt_log_ra
        else:
            widget = self.txt_log_sys

        widget.config(state=tk.NORMAL)
        widget.insert(tk.END, line)
        widget.see(tk.END)
        line_count = int(widget.index("end-1c").split(".")[0])
        if line_count > 500:
            widget.delete("1.0", f"{line_count - 500}.0")
        widget.config(state=tk.DISABLED)

    def _set_plate_image(self, cong, image):
        wrap = self.plate_image_wrap[cong]
        label = self.lbl_plate_image[cong]
        if image is None or cv2 is None or Image is None or ImageTk is None:
            label.config(image="", text="--\n----", bg=PLATE_BG, fg=TEXT)
            self._photo_plate[cong] = None
            return

        h, w = image.shape[:2]
        # Fit toan bo bien so vao gioi han hien thi, frame co theo anh de khong du nen.
        scale = min(PROC_MAX_W / max(w, 1), PROC_MAX_H / max(h, 1))
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        interpolation = cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC
        preview = cv2.resize(image, (new_w, new_h), interpolation=interpolation)

        if len(preview.shape) == 2:
            preview = cv2.cvtColor(preview, cv2.COLOR_GRAY2RGB)
        elif preview.shape[2] == 4:
            preview = cv2.cvtColor(preview, cv2.COLOR_BGRA2RGBA)
        else:
            preview = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)

        img = Image.fromarray(preview)

        wrap.configure(width=img.width, height=img.height)
        self._photo_plate[cong] = ImageTk.PhotoImage(img)
        label.config(image=self._photo_plate[cong], text="", bg=PLATE_BG)

    def _on_plate_result(self, cong, bs, image):
        cong = cong if cong in ("vao", "ra") else "vao"
        if isinstance(image, str) and image == "processing":
            self.lbl_plate_image[cong].config(image="", text="\u0110ang x\u1eed l\u00fd...", fg=TEXT, bg=PLATE_BG)
            self.lbl_plate_text[cong].config(text="\u0110ang x\u1eed l\u00fd...")
            return
        self._set_plate_image(cong, image if not isinstance(image, str) else None)
        plate_text = bs.strip() if isinstance(bs, str) else ""
        self.lbl_plate_text[cong].config(text=dinh_dang_hien_thi(plate_text) if plate_text else "---")

    def _refresh_plate_menu(self, plates):
        values = [dinh_dang_hien_thi(item["bien_so"]) for item in plates]
        self._plate_display_to_raw = {dinh_dang_hien_thi(item["bien_so"]): item["bien_so"] for item in plates}
        self.cmb_plate["values"] = [DELETE_PLACEHOLDER] + values
        current = self.var_plate.get()
        if current not in self.cmb_plate["values"]:
            self.var_plate.set(DELETE_PLACEHOLDER)
        self._refresh_delete_placeholder_style()

    def _refresh_camera_menu(self, choices):
        labels = [f"Cam {item}" for item in choices]
        self.opt_cam_vao["values"] = labels
        self.opt_cam_ra["values"] = labels
        if self.var_cam_vao.get() not in labels:
            self.var_cam_vao.set(labels[0] if labels else "Cam 0")
        if self.var_cam_ra.get() not in labels:
            self.var_cam_ra.set(labels[1] if len(labels) > 1 else (labels[0] if labels else "Cam 0"))

    def _chon_camera(self, cong, value):
        var = self.var_cam_vao if cong == "vao" else self.var_cam_ra
        label = value if str(value).startswith("Cam ") else f"Cam {value}"
        var.set(label)
        if self.controller.cameras.get(cong) is not None:
            self._bat_cam(cong)

    def _refresh_camera_preview(self, cong, rgb):
        label = self.lbl_cam_vao if cong == "vao" else self.lbl_cam_ra
        if rgb is None or Image is None or ImageTk is None:
            label.config(image="", text="Camera v\u00e0o" if cong == "vao" else "Camera ra", fg=TEXT, bg=CAM_BG)
            self._photo_cam[cong] = None
            return

        target_w = CAM_VIEW_W - 2
        target_h = CAM_VIEW_H - 2
        img = Image.fromarray(rgb)
        src_w, src_h = img.size
        # Hien thi tron frame camera de nguoi dung canh bien so dung voi anh AI nhan.
        scale = min(target_w / src_w, target_h / src_h)
        new_w = max(1, int(src_w * scale))
        new_h = max(1, int(src_h * scale))
        resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        cropped = Image.new("RGB", (target_w, target_h), (255, 255, 255))
        left = (target_w - new_w) // 2
        top = (target_h - new_h) // 2
        cropped.paste(resized, (left, top))

        self._photo_cam[cong] = ImageTk.PhotoImage(cropped)
        label.config(image=self._photo_cam[cong], text="", bg=CAM_BG)

    def _refresh_ui(self):
        state = self.controller.get_ui_state()
        so_xe = state["so_xe"]
        suc_chua = state["suc_chua"]
        self.lbl_slot.config(text=f"{so_xe}/{suc_chua}")

        if so_xe < suc_chua:
            self.lbl_status.config(text="C\u00d2N CH\u1ed6 TR\u1ed0NG", bg=BTN_GREEN, fg=TEXT)
            self.lbl_slot.config(bg=BTN_GREEN, fg=TEXT)
        else:
            self.lbl_status.config(text="H\u1ebeT CH\u1ed6", bg=BTN_RED, fg=TEXT)
            self.lbl_slot.config(bg=BTN_RED, fg=TEXT)

        # Che do dang chon duoc to mau noi bat, che do con lai lam mo.
        if state["che_do"] == "tu_dong":
            self.btn_auto.config(bg=BTN_AUTO_ACTIVE, fg=TEXT, activebackground=BTN_AUTO_ACTIVE,
                                 activeforeground=TEXT, relief=tk.SOLID)
            self.btn_manual.config(bg=BTN_MUTED, fg=BTN_MUTED_TEXT, activebackground=BTN_MUTED,
                                   activeforeground=BTN_MUTED_TEXT, relief=tk.SOLID)
            gate_state = tk.DISABLED
        else:
            self.btn_auto.config(bg=BTN_MUTED, fg=BTN_MUTED_TEXT, activebackground=BTN_MUTED,
                                 activeforeground=BTN_MUTED_TEXT, relief=tk.SOLID)
            self.btn_manual.config(bg=BTN_MANUAL_ACTIVE, fg=TEXT, activebackground=BTN_MANUAL_ACTIVE,
                                   activeforeground=TEXT, relief=tk.SOLID)
            gate_state = tk.NORMAL

        for cong, btn in (("vao", self.btn_gate_in), ("ra", self.btn_gate_out)):
            ten = "C\u1ed5ng v\u00e0o" if cong == "vao" else "C\u1ed5ng ra"
            if gate_state == tk.DISABLED:
                btn.config(state=tk.DISABLED, text=ten, bg=BTN_DISABLED,
                           fg=BTN_DISABLED_TEXT, disabledforeground=BTN_DISABLED_TEXT,
                           activebackground=BTN_DISABLED, activeforeground=BTN_DISABLED_TEXT)
            else:
                mo = state["barie"][cong] == "mo"
                btn.config(state=tk.NORMAL, text=f"{ten}: M\u1edf" if mo else f"{ten}: \u0110\u00f3ng",
                           fg=TEXT,
                           bg=BTN_GATE_OPEN if mo else BTN_GATE_CLOSED,
                           activebackground=BTN_GATE_OPEN if mo else BTN_GATE_CLOSED,
                           activeforeground=TEXT,
                           disabledforeground=BTN_DISABLED_TEXT)

        camera_choices_key = tuple(state["camera_choices"])
        if camera_choices_key != self._last_camera_choices:
            self._refresh_camera_menu(state["camera_choices"])
            self._last_camera_choices = camera_choices_key

        plate_keys = tuple((item.get("bien_so"), item.get("chu_xe")) for item in state["plates"])
        if plate_keys != self._last_plate_keys:
            self._refresh_plate_menu(state["plates"])
            self._last_plate_keys = plate_keys

        latest_rgb = state["latest_rgb"]
        for cong in ("vao", "ra"):
            rgb = latest_rgb.get(cong) if isinstance(latest_rgb, dict) else None
            latest_rgb_id = id(rgb)
            if latest_rgb_id != self._last_latest_rgb_id[cong]:
                self._refresh_camera_preview(cong, rgb)
                self._last_latest_rgb_id[cong] = latest_rgb_id

        # Cap nhat trang thai COM port
        if self.controller.ard_connected:
            self.btn_com_connect.config(text="Ng\u1eaft", bg=BTN_RED, state=tk.NORMAL)
            self.lbl_com_status.config(text="\u2713 \u0110\u00e3 k\u1ebft n\u1ed1i Arduino", fg="#27ae60")
        else:
            self.btn_com_connect.config(text="K\u1ebft n\u1ed1i", bg=BTN_GREEN, state=tk.NORMAL)
            if self.lbl_com_status.cget("text").startswith("\u0110ang"):
                pass  # Giu nguyen text "Dang ket noi..."
            elif self.lbl_com_status.cget("text") == "\u2713 \u0110\u00e3 k\u1ebft n\u1ed1i Arduino":
                self.lbl_com_status.config(text="Ch\u01b0a k\u1ebft n\u1ed1i", fg=MUTED)

    def _quet_camera(self, show_error=True):
        try:
            self.controller.quet_camera()
        except RuntimeError as exc:
            if show_error:
                messagebox.showerror("L\u1ed7i", str(exc))
            else:
                self._log(str(exc))

    def _bat_cam(self, cong):
        try:
            var = self.var_cam_vao if cong == "vao" else self.var_cam_ra
            self.controller.bat_cam(cong, var.get())
        except RuntimeError as exc:
            messagebox.showerror("L\u1ed7i", str(exc))

    def _tat_cam(self, cong):
        self.controller.tat_cam(cong)

    def _chup(self, cong):
        self.controller.chup(cong)

    def _add_plate(self):
        try:
            text = self.ent_plate.get().strip()
            self.controller.add_plate(text)
            self.ent_plate.delete(0, tk.END)
        except ValueError as exc:
            messagebox.showwarning("L\u1ed7i", str(exc))

    def _del_plate(self):
        selected = self.var_plate.get()
        if selected == DELETE_PLACEHOLDER:
            return
        raw = self._plate_display_to_raw.get(selected, selected)
        self.controller.delete_plate(raw)
        self.var_plate.set(DELETE_PLACEHOLDER)
        self._refresh_delete_placeholder_style()

    def _quet_com(self):
        """Quet va cap nhat danh sach cong COM."""
        ds = self.controller.danh_sach_cong_com()
        if ds:
            self.cmb_com["values"] = ds
            if self.var_com.get() not in ds:
                self.var_com.set(ds[0])
        else:
            self.cmb_com["values"] = ["Khong co cong"]
            self.var_com.set("Khong co cong")

    def _ket_noi_com(self):
        """Ket noi hoac ngat Arduino theo cong COM da chon."""
        if self.controller.ard_connected:
            self.controller.ngat_arduino()
            self.btn_com_connect.config(text="K\u1ebft n\u1ed1i", bg=BTN_GREEN)
            self.lbl_com_status.config(text="\u0110\u00e3 ng\u1eaft", fg="#c0392b")
            return
        port = self.var_com.get()
        if not port or port in ("Chon cong COM", "Khong co cong"):
            self._log("Hay chon cong COM truoc")
            return
        self.btn_com_connect.config(text="\u0110ang k\u1ebft n\u1ed1i...", bg=BTN_PEACH, state=tk.DISABLED)
        self.lbl_com_status.config(text=f"\u0110ang k\u1ebft n\u1ed1i {port}...", fg=MUTED)
        self.controller.ket_noi_arduino(port)

    def _poll(self):
        if not self.controller.dang_chay:
            self._poll_after_id = None
            return
        try:
            self.controller.poll_messages(schedule=lambda ms, fn: self.root.after(ms, fn))
            self.controller.poll(schedule=lambda ms, fn: self.root.after(ms, fn))
            self.controller.set_cam_size("vao", CAM_VIEW_W - 2, CAM_VIEW_H - 2)
            self.controller.set_cam_size("ra", CAM_VIEW_W - 2, CAM_VIEW_H - 2)
        except Exception as exc:
            self._log(f"Loi vong lap UI: {exc}")
        self._poll_after_id = self.root.after(50, self._poll)

    def _thoat(self):
        if self._poll_after_id is not None:
            self.root.after_cancel(self._poll_after_id)
            self._poll_after_id = None
        self.controller.stop()
        self.root.destroy()

    def _reload(self):
        if self._poll_after_id is not None:
            self.root.after_cancel(self._poll_after_id)
            self._poll_after_id = None
        self.controller.stop()
        self._photo_cam = {"vao": None, "ra": None}
        self._photo_plate = {"vao": None, "ra": None}
        self._last_camera_choices = None
        self._last_plate_keys = None
        self._last_latest_rgb_id = {"vao": None, "ra": None}
        self.var_cam_vao.set("Cam 0")
        self.var_cam_ra.set("Cam 1")
        self.var_plate.set(DELETE_PLACEHOLDER)
        self._plate_display_to_raw = {}
        self.ent_plate.delete(0, tk.END)
        self.lbl_cam_vao.config(image="", text="Camera v\u00e0o", fg=TEXT, bg=CAM_BG)
        self.lbl_cam_ra.config(image="", text="Camera ra", fg=TEXT, bg=CAM_BG)
        for cong in ("vao", "ra"):
            self._set_plate_image(cong, None)
            self.lbl_plate_text[cong].config(text="---", bg="white", fg="#101010")

        self.controller = DieuKhienHeThong(
            on_log=self._log,
            on_state_change=self._refresh_ui,
            on_plate_result=self._on_plate_result,
            on_messagebox=lambda title, msg: messagebox.askyesno(title, msg),
        )
        self._refresh_ui()
        self._quet_camera(show_error=False)
        self._quet_com()
        self.lbl_com_status.config(text="Ch\u01b0a k\u1ebft n\u1ed1i", fg=MUTED)
        self.controller.start()
        self._poll()

    def chay(self):
        self.controller.start()
        self._poll()
        self.root.mainloop()


if __name__ == "__main__":
    GiaoDienBaiXe().chay()
