"""
Logic dieu khien cho he thong bai xe.
UI chi can goi cac ham cua lop nay va doc state de hien thi.
"""

import os
import queue
import threading
import time

_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    import cv2
except Exception:
    cv2 = None

from giao_tiep_arduino import KetNoiArduino
from nhan_dien_bien_so import NhanDienBienSo, chuan_hoa_bien_so, dinh_dang_hien_thi
from quan_ly_du_lieu import CSDLBaiXe


class DieuKhienHeThong:
    def __init__(self, on_log=None, on_state_change=None, on_plate_result=None, on_messagebox=None):
        self.on_log = on_log or (lambda msg: None)
        self.on_state_change = on_state_change or (lambda: None)
        self.on_plate_result = on_plate_result or (lambda cong, bs, image: None)
        self.on_messagebox = on_messagebox or (lambda title, message: False)

        self.db = CSDLBaiXe(os.path.join(_DIR, "co_so_du_lieu_bai_xe.db"))
        self.arduino = KetNoiArduino()
        self.ai = None

        self.dang_chay = True
        self.che_do = "tu_dong"
        self.cameras = {"vao": None, "ra": None}
        self.camera_index = {"vao": 0, "ra": 1}
        self.camera_choices = ["0"]
        self.latest_frame = {"vao": None, "ra": None}
        self.latest_rgb = {"vao": None, "ra": None}
        self.camera_capture_size = (1280, 720)
        self.cam_size = {"vao": (480, 270), "ra": (480, 270)}
        self.camera_target_fps = 20.0
        self._last_preview_notify = {"vao": 0.0, "ra": 0.0}
        self.dang_nhan_dien = False
        self.ai_cong_hien_tai = None
        self.ard_connected = False
        self.ai_started_at = 0.0
        self.ai_timeout_sec = 8.0
        self.ai_ready = False

        self.barie = {"vao": "dong", "ra": "dong"}
        self.cam_bien = {"xe_vao": False, "xe_ra": False}
        self.cho_dong = {"vao": False, "ra": False}
        self.cho_dong_sau_khi_quang_ms = 2000
        self.cam_bien_quang_tu = {"vao": None, "ra": None}
        self.cam_bien_da_gap_vat_can = {"vao": False, "ra": False}
        self.cam_bien_edge_ts = {"vao": 0.0, "ra": 0.0}  # debounce: thoi diem canh len gan nhat
        self.cam_bien_debounce_ms = 800  # bo qua canh len trong khoang nay (ms)
        self.bien_so_cho_ra = None
        self.retry_ai_after_ms = 1500
        self.retry_ai_dang_cho = {"vao": False, "ra": False}
        self.retry_ai_count = {"vao": 0, "ra": 0}
        self.retry_ai_max = 3  # toi da 3 lan thu lai khi bi tu choi
        self.bien_so_cuoi = ""

        self.q_ai = queue.Queue(maxsize=1)
        self.q_sensor = queue.Queue()
        self.q_msg = queue.Queue()
        self._state_dirty = threading.Event()

        self._cache_lock = threading.Lock()
        self._db_cache_dirty = True
        self._cached_so_xe = 0
        self._cached_suc_chua = 3
        self._cached_plates = []

    def get_ui_state(self):
        self._ensure_db_cache()
        return {
            "so_xe": self._cached_so_xe,
            "suc_chua": self._cached_suc_chua,
            "che_do": self.che_do,
            "barie": dict(self.barie),
            "bien_so_cuoi": self.bien_so_cuoi,
            "camera_choices": list(self.camera_choices),
            "camera_index": dict(self.camera_index),
            "plates": list(self._cached_plates),
            "latest_rgb": dict(self.latest_rgb),
        }

    def _invalidate_db_cache(self):
        with self._cache_lock:
            self._db_cache_dirty = True

    def _ensure_db_cache(self):
        with self._cache_lock:
            if not self._db_cache_dirty:
                return
            self._cached_so_xe = self.db.so_xe()
            self._cached_suc_chua = self.db.lay_suc_chua()
            self._cached_plates = self.db.ds_bien_so()
            self._db_cache_dirty = False

    def set_cam_size(self, cong, width, height):
        if cong in self.cam_size:
            self.cam_size[cong] = (max(1, width), max(1, height))

    def notify(self):
        self._state_dirty.set()

    def _emit_state_change(self):
        if not self._state_dirty.is_set():
            return
        self._state_dirty.clear()
        self.on_state_change()

    def log(self, message):
        self.on_log(message)

    def start(self):
        self.log("He thong san sang")
        self.log("Dang tai module AI")
        threading.Thread(target=self._ai_worker, daemon=True).start()
        self.log("Chon cong COM va bam Ket noi de ket noi Arduino")

    def stop(self):
        self.dang_chay = False
        self.ai_ready = False
        self.tat_cam("vao", log_message=False)
        self.tat_cam("ra", log_message=False)
        self.arduino.ngat()

    def mode(self, mode):
        self.che_do = mode
        self.bien_so_cho_ra = None
        self.log("Che do: Tu dong" if mode == "tu_dong" else "Che do: Thu cong")
        self.notify()

    def add_plate(self, text):
        bs = chuan_hoa_bien_so(text)
        if not bs:
            raise ValueError("Nhap bien so")
        self.db.them_bien_so(bs)
        self._invalidate_db_cache()
        self.log(f"Them bien so: {dinh_dang_hien_thi(bs)}")
        self.notify()

    def delete_plate(self, bs):
        if not bs:
            return
        self.db.xoa_bien_so(bs)
        self._invalidate_db_cache()
        self.log(f"Xoa bien so: {dinh_dang_hien_thi(bs)}")
        self.notify()

    def barie_click(self, cong, schedule=None):
        if self.che_do != "thu_cong":
            return
        if self.barie[cong] == "dong":
            self.barie[cong] = "mo"
            self.cho_dong[cong] = False
            self.cam_bien_quang_tu[cong] = None
            sensor_key = "xe_vao" if cong == "vao" else "xe_ra"
            self.cam_bien_da_gap_vat_can[cong] = self.cam_bien.get(sensor_key, False)
            self.arduino.gui_lenh("VAO_MO" if cong == "vao" else "RA_MO")
            self.log("Mo cong vao" if cong == "vao" else "Mo cong ra")
        else:
            sensor_key = "xe_vao" if cong == "vao" else "xe_ra"
            if self.cam_bien.get(sensor_key, False):
                self.cho_dong[cong] = True
                self.log("Xe con trong vung cam bien, doi dong an toan")
                self.auto_close(cong, schedule=schedule)
                return
            self.auto_close(cong, schedule=schedule)
        self.notify()

    def quet_camera(self):
        if cv2 is None:
            raise RuntimeError("Chua cai OpenCV")
        self.tat_cam("vao", log_message=False)
        self.tat_cam("ra", log_message=False)
        found = []
        for index in range(5):
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            try:
                if cap.isOpened():
                    found.append(str(index))
            finally:
                cap.release()
        self.camera_choices = found or ["0"]
        self.camera_index["vao"] = int(self.camera_choices[0])
        self.camera_index["ra"] = int(self.camera_choices[1] if len(self.camera_choices) > 1 else self.camera_choices[0])
        self.log(f"Tim thay {len(found)} camera" if found else "Khong tim thay camera")
        self.notify()

    def bat_cam(self, cong, camera_value):
        if cv2 is None:
            raise RuntimeError("Thieu OpenCV/Pillow")
        if cong not in self.cameras:
            raise RuntimeError("Cong camera khong hop le")
        try:
            new_index = int(str(camera_value).replace("Cam", "").strip())
        except Exception:
            new_index = 0
        cong_khac = "ra" if cong == "vao" else "vao"
        if self.cameras.get(cong_khac) is not None and self.camera_index.get(cong_khac) == new_index:
            raise RuntimeError("Camera nay dang duoc dung cho cong " + ("ra" if cong_khac == "ra" else "vao"))
        if self.cameras[cong] is not None and new_index == self.camera_index[cong]:
            return
        if self.cameras[cong] is not None:
            self.tat_cam(cong, log_message=False)
        self.camera_index[cong] = new_index
        camera = cv2.VideoCapture(self.camera_index[cong], cv2.CAP_DSHOW)
        if not camera.isOpened():
            raise RuntimeError(f"Khong mo duoc camera {self.camera_index[cong]}")
        try:
            camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        except Exception:
            pass
        req_w, req_h = self.camera_capture_size
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, req_w)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, req_h)
        camera.set(cv2.CAP_PROP_FPS, 30)
        try:
            camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass
        self.cameras[cong] = camera
        self.latest_frame[cong] = None
        self.latest_rgb[cong] = None
        self._last_preview_notify[cong] = 0.0
        actual_w = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        actual_h = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        actual_fps = camera.get(cv2.CAP_PROP_FPS) or 0
        ten_cong = "vao" if cong == "vao" else "ra"
        self.log(f"Bat camera {ten_cong} {self.camera_index[cong]}: {actual_w}x{actual_h} @ {actual_fps:.0f}fps")
        threading.Thread(target=self._cam_reader, args=(cong, camera), daemon=True).start()
        self.notify()

    def tat_cam(self, cong, log_message=True):
        if cong not in self.cameras:
            return
        cam = self.cameras[cong]
        self.cameras[cong] = None
        self.latest_frame[cong] = None
        self.latest_rgb[cong] = None
        if cam is not None:
            cam.release()
        if log_message:
            self.log("Tat camera vao" if cong == "vao" else "Tat camera ra")
        self.notify()

    def chup(self, cong="vao"):
        if cong not in self.cameras:
            return False
        if self.cameras[cong] is None:
            # Thu tu bat lai camera de tranh trang thai mat ket noi tam thoi.
            try:
                self.bat_cam(cong, str(self.camera_index[cong]))
            except Exception:
                self.log("Chua bat camera vao" if cong == "vao" else "Chua bat camera ra")
                return False
        if not self.ai_ready:
            self.log("AI chua san sang")
            return False
        if self.dang_nhan_dien:
            return False
        if not self._wait_for_frame(cong, timeout_sec=1.2):
            self.log("Chua co frame")
            return False
        frame_chup = self.latest_frame[cong].copy()
        self.dang_nhan_dien = True
        self.ai_cong_hien_tai = cong
        self.ai_started_at = time.monotonic()
        self.log("Dang nhan dien bien so cong vao" if cong == "vao" else "Dang nhan dien bien so cong ra")
        self.on_plate_result(cong, None, "processing")
        try:
            while not self.q_ai.empty():
                self.q_ai.get_nowait()
            self.q_ai.put_nowait((cong, frame_chup))
        except Exception:
            self.dang_nhan_dien = False
            self.ai_cong_hien_tai = None
            self.ai_started_at = 0.0
            self.on_plate_result(cong, None, None)
            self.log("Khong the day frame vao hang doi AI")
            self.notify()
            return False
        return True

    def _schedule_retry_ai(self, cong, schedule):
        if not schedule or self.retry_ai_dang_cho.get(cong):
            return
        sensor_key = "xe_vao" if cong == "vao" else "xe_ra"
        if not self.cam_bien.get(sensor_key, False) or self.barie.get(cong) != "dong":
            return
        self.retry_ai_dang_cho[cong] = True

        def retry(gate=cong):
            self.retry_ai_dang_cho[gate] = False
            sensor = "xe_vao" if gate == "vao" else "xe_ra"
            if self.cam_bien.get(sensor, False) and self.barie.get(gate) == "dong":
                self._yeu_cau_chup(gate, schedule=schedule)

        schedule(self.retry_ai_after_ms, retry)

    def _yeu_cau_chup(self, cong, schedule=None):
        if not self.chup(cong):
            self._schedule_retry_ai(cong, schedule)

    def _wait_for_frame(self, cong, timeout_sec=1.0):
        end = time.monotonic() + max(0.0, timeout_sec)
        while self.latest_frame.get(cong) is None and time.monotonic() < end:
            time.sleep(0.03)
        return self.latest_frame.get(cong) is not None

    def auto_close(self, cong, schedule=None):
        if self.barie[cong] != "mo":
            return
        sensor_key = "xe_vao" if cong == "vao" else "xe_ra"
        now = time.monotonic()
        if self.cam_bien.get(sensor_key, False):
            self.cho_dong[cong] = True
            self.cam_bien_da_gap_vat_can[cong] = True
            self.cam_bien_quang_tu[cong] = None
            if schedule:
                schedule(500, lambda gate=cong: self.auto_close(gate, schedule=schedule))
            return
        if not self.cam_bien_da_gap_vat_can.get(cong, False):
            self.cho_dong[cong] = False
            self.cam_bien_quang_tu[cong] = None
        elif schedule:
            moc_quang = self.cam_bien_quang_tu.get(cong)
            if moc_quang is None:
                self.cam_bien_quang_tu[cong] = now
                schedule(self.cho_dong_sau_khi_quang_ms, lambda gate=cong: self.auto_close(gate, schedule=schedule))
                return
            elapsed_ms = (now - moc_quang) * 1000
            if elapsed_ms < self.cho_dong_sau_khi_quang_ms:
                delay_ms = max(100, int(self.cho_dong_sau_khi_quang_ms - elapsed_ms))
                schedule(delay_ms, lambda gate=cong: self.auto_close(gate, schedule=schedule))
                return
        self.cho_dong[cong] = False
        self.cam_bien_quang_tu[cong] = None
        self.cam_bien_da_gap_vat_can[cong] = False
        self.barie[cong] = "dong"
        self.arduino.gui_lenh("VAO_DONG" if cong == "vao" else "RA_DONG")
        if cong == "ra" and self.bien_so_cho_ra:
            bs = self.bien_so_cho_ra
            self.bien_so_cho_ra = None
            if self.db.xoa_xe(bs):
                self._invalidate_db_cache()
                self.log("Xe da ra khoi bai - da cap nhat so luong")
        self.notify()

    def poll(self, schedule=None):
        self._check_ai_timeout()
        try:
            while True:
                self._xu_ly_cam_bien(self.q_sensor.get_nowait(), schedule=schedule)
        except queue.Empty:
            pass
        self._emit_state_change()

    def _reset_ai(self, image=None, cong=None):
        """Reset trang thai AI ve idle (dung chung cho timeout, error, done)."""
        cong = cong or self.ai_cong_hien_tai or "vao"
        self.dang_nhan_dien = False
        self.ai_cong_hien_tai = None
        self.ai_started_at = 0.0
        self.on_plate_result(cong, None, image)

    def _check_ai_timeout(self):
        if not self.dang_nhan_dien or self.ai_started_at <= 0:
            return
        if time.monotonic() - self.ai_started_at < self.ai_timeout_sec:
            return
        self._reset_ai()
        self.log("Nhan dien qua lau (>8s), da huy lan chup. Thu lai.")
        self.notify()

    def danh_sach_cong_com(self):
        """Tra ve danh sach cong COM hien co."""
        return self.arduino.danh_sach_cong()

    def ket_noi_arduino(self, ten_cong):
        """Ket noi Arduino vao cong COM duoc chon. Chay trong background thread."""
        def worker():
            self.q_msg.put(f"Dang ket noi {ten_cong}...")
            try:
                self.arduino.ngat()
                self.ard_connected = False
                self.arduino.ket_noi(ten_cong)
                if self.arduino.kiem_tra_handshake(thoi_gian_cho=3.0):
                    self.ard_connected = True
                    self.q_msg.put(f"Arduino ket noi thanh cong: {ten_cong}")
                    if self.arduino.firmware:
                        self.q_msg.put(f"Arduino firmware: {self.arduino.firmware}")
                    threading.Thread(target=self._sensor_worker, daemon=True).start()
                else:
                    self.arduino.ngat()
                    self.q_msg.put(f"{ten_cong} khong phan hoi. Kiem tra day cap va cong COM.")
            except Exception as e:
                self.arduino.ngat()
                self.q_msg.put(f"Loi ket noi {ten_cong}: {e}")
            self.notify()

        threading.Thread(target=worker, daemon=True).start()

    def ngat_arduino(self):
        """Ngat ket noi Arduino."""
        self.arduino.ngat()
        self.ard_connected = False
        self.log("Da ngat Arduino")
        self.notify()

    def _sensor_worker(self):
        import time
        while self.dang_chay and self.ard_connected:
            try:
                data = self.arduino.doc_cam_bien()
                if data:
                    self.q_sensor.put(data)
            except Exception:
                pass
            time.sleep(0.1)

    def _xu_ly_cam_bien(self, data, schedule=None):
        old_vao = self.cam_bien.get("xe_vao", False)
        old_ra = self.cam_bien.get("xe_ra", False)
        self.cam_bien.update(data)
        vao = self.cam_bien.get("xe_vao", False)
        ra = self.cam_bien.get("xe_ra", False)
        for cong, sensor_key, old_value, new_value in (
            ("vao", "xe_vao", old_vao, vao),
            ("ra", "xe_ra", old_ra, ra),
        ):
            if new_value:
                if self.barie.get(cong) == "mo":
                    self.cam_bien_da_gap_vat_can[cong] = True
                self.cam_bien_quang_tu[cong] = None
            elif old_value and not new_value:
                self.cam_bien_quang_tu[cong] = time.monotonic()
        for cong, sensor_key in (("vao", "xe_vao"), ("ra", "xe_ra")):
            if self.cho_dong.get(cong) and not self.cam_bien.get(sensor_key, False):
                self.auto_close(cong, schedule=schedule)
        if self.che_do != "tu_dong":
            return
        now_ms = time.monotonic() * 1000
        for cong, sensor_key, old_val, new_val in (
            ("vao", "xe_vao", old_vao, vao),
            ("ra", "xe_ra", old_ra, ra),
        ):
            # Chi chup khi: canh len (0->1) + barie dang dong + debounce da qua
            if new_val and not old_val and self.barie[cong] == "dong":
                last_edge = self.cam_bien_edge_ts.get(cong, 0.0)
                if now_ms - last_edge >= self.cam_bien_debounce_ms:
                    self.cam_bien_edge_ts[cong] = now_ms
                    self._yeu_cau_chup(cong, schedule=schedule)
            # Tu dong dong khi xe roi khoi cam bien
            if old_val and not new_val and self.barie[cong] == "mo":
                self.auto_close(cong, schedule=schedule)

    def _cam_reader(self, cong, cam):
        import time
        min_notify_interval = 1.0 / max(1.0, self.camera_target_fps)
        while cam and self.dang_chay and self.cameras.get(cong) is cam:
            try:
                ret, frame = cam.read()
                if ret and frame is not None:
                    self.latest_frame[cong] = frame
                    now = time.monotonic()
                    if now - self._last_preview_notify[cong] >= min_notify_interval:
                        target_w, target_h = self.cam_size[cong]
                        h, w = frame.shape[:2]
                        ratio = min(target_w / w, target_h / h)
                        new_w = max(1, int(w * ratio))
                        new_h = max(1, int(h * ratio))
                        preview = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
                        self.latest_rgb[cong] = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
                        self._last_preview_notify[cong] = now
                        self.notify()
            except Exception:
                break
            time.sleep(0.001)

    def _cho_xe_vao(self, bs, log_msg, schedule=None):
        """Logic chung cho xe vao bai (tu dong va thu cong)."""
        if self.db.them_xe(bs):
            self._invalidate_db_cache()
            self.barie["vao"] = "mo"
            self.cho_dong["vao"] = False
            self.cam_bien_quang_tu["vao"] = None
            self.cam_bien_da_gap_vat_can["vao"] = self.cam_bien.get("xe_vao", False)
            self.arduino.gui_lenh("VAO_MO")
            self.log(log_msg)
            if schedule:
                schedule(5000, lambda: self.auto_close("vao", schedule=schedule))

    def _handle_ai_result(self, cong, bs, anh_bs, schedule=None):
        self.dang_nhan_dien = False
        self.ai_cong_hien_tai = None
        self.ai_started_at = 0.0
        bs = chuan_hoa_bien_so(bs if isinstance(bs, str) else (str(bs) if bs is not None else ""))

        if not bs:
            self.bien_so_cuoi = ""
            self.on_plate_result(cong, None, anh_bs)
            self.log("Khong doc duoc bien so")
            self._retry_or_give_up(cong, schedule)
            self.notify()
            return
        self.bien_so_cuoi = bs
        plate_text = dinh_dang_hien_thi(bs)
        self.on_plate_result(cong, bs, anh_bs)
        self.log(f"Bien so cong {'vao' if cong == 'vao' else 'ra'}: {plate_text}")

        if cong == "ra":
            if not self.db.co_xe(bs):
                self.log("Xe khong co trong bai - khong mo cong ra")
                self._retry_or_give_up(cong, schedule, reason="Bien so khong khop, thu lai")
                self.notify()
                return
            if self.che_do != "tu_dong" and not self.on_messagebox("Duyet", f"Cho xe {plate_text} ra?"):
                self.log(f"Tu choi cho ra: {plate_text}")
                self.retry_ai_count[cong] = 0  # nguoi dung tu choi = reset retry
                self.notify()
                return
            # Thanh cong - reset retry va mo barrier
            self.retry_ai_count[cong] = 0
            self.bien_so_cho_ra = bs
            if self.barie["ra"] == "dong":
                self.barie["ra"] = "mo"
                self.cho_dong["ra"] = False
                self.cam_bien_quang_tu["ra"] = None
                self.cam_bien_da_gap_vat_can["ra"] = self.cam_bien.get("xe_ra", False)
                self.arduino.gui_lenh("RA_MO")
                self.log(f"Cho ra: {plate_text}")
                if schedule:
                    schedule(5000, lambda: self.auto_close("ra", schedule=schedule))
            self.notify()
            return

        for check, msg, can_retry in [
            (lambda: not self.db.la_hop_le(bs), "Xe khong hop le", True),
            (lambda: self.db.co_xe(bs), "Xe da co trong bai", False),
            (lambda: self.db.so_xe() >= self.db.lay_suc_chua(), "Bai xe da day", False),
        ]:
            if check():
                self.log(msg)
                if can_retry:
                    self._retry_or_give_up(cong, schedule, reason="Bien so khong hop le, thu lai")
                else:
                    self.retry_ai_count[cong] = 0
                self.notify()
                return

        # Thanh cong - reset retry
        self.retry_ai_count[cong] = 0
        if self.che_do == "tu_dong":
            self._cho_xe_vao(bs, f"Cho vao: {plate_text}", schedule)
        elif self.on_messagebox("Duyet", f"Cho xe {plate_text} vao?"):
            self._cho_xe_vao(bs, f"Duyet cho vao: {plate_text}", schedule)
        else:
            self.log(f"Tu choi: {plate_text}")
        self.notify()

    def _retry_or_give_up(self, cong, schedule, reason=None):
        """Thu lai nhan dien neu chua vuot qua so lan toi da, nguoc lai dung."""
        count = self.retry_ai_count.get(cong, 0) + 1
        self.retry_ai_count[cong] = count
        if count <= self.retry_ai_max:
            if reason:
                self.log(f"{reason} (lan {count}/{self.retry_ai_max})")
            self._schedule_retry_ai(cong, schedule)
        else:
            self.retry_ai_count[cong] = 0
            self.log(f"Da thu {self.retry_ai_max} lan - khong nhan dien duoc. Vui long thu cong.")

    def _ai_worker(self):
        try:
            self.ai = NhanDienBienSo()
            self.ai_ready = True
            self.q_msg.put(f"AI: {self.ai.trang_thai}")
        except Exception as exc:
            self.ai_ready = False
            self.q_msg.put(f"Loi khoi tao AI: {exc}")
            return

        while self.dang_chay:
            try:
                cong, frame = self.q_ai.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                t0 = time.monotonic()
                bs, anh_bs = self.ai.nhan_dien(frame)
                self.q_msg.put(f"AI xu ly xong sau {time.monotonic() - t0:.2f}s")
                self.q_msg.put(("ai_result", cong, bs, anh_bs))
            except Exception as exc:
                self.q_msg.put(("ai_error", cong, str(exc)))

    def poll_messages(self, schedule=None):
        try:
            while True:
                msg = self.q_msg.get_nowait()
                try:
                    if isinstance(msg, tuple) and msg and msg[0] == "ai_result":
                        self._handle_ai_result(msg[1], msg[2], msg[3], schedule=schedule)
                    elif isinstance(msg, tuple) and msg and msg[0] == "ai_error":
                        self.log(f"Loi AI: {msg[2]}")
                        self._reset_ai(cong=msg[1]); self.notify()
                    else:
                        self.log(msg)
                except Exception as exc:
                    self.log(f"Loi xu ly ket qua AI: {exc}")
                    self._reset_ai(); self.notify()
        except queue.Empty:
            pass
        self._emit_state_change()
