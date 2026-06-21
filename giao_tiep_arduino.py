"""
Module ket noi va dieu khien Arduino qua cong Serial.
Gui lenh mo/dong barie, doc trang thai cam bien.
"""

import threading

try:
    import serial
    from serial.tools import list_ports
except Exception:
    serial = None
    list_ports = None


class KetNoiArduino:
    """Quan ly giao tiep Serial voi Arduino."""

    def __init__(self):
        self._cong = None
        self._khoa = threading.RLock()
        self.firmware = ""

    # --- Ket noi ---

    def danh_sach_cong(self):
        """Liet ke cac cong COM co san tren may tinh."""
        if list_ports is None:
            return []
        return [p.device for p in list_ports.comports()]

    def ket_noi(self, ten_cong, toc_do=9600):
        """Mo ket noi Serial den Arduino."""
        if serial is None:
            raise RuntimeError("Chua cai thu vien pyserial")
        with self._khoa:
            self.ngat()
            self.firmware = ""
            self._cong = serial.Serial(port=ten_cong, baudrate=toc_do, timeout=1)

    def kiem_tra_handshake(self, thoi_gian_cho=3.0):
        """Kiem tra cong Serial co phai Arduino cua he thong khong.

        Cach hoat dong:
        - Khi mo Serial, Arduino reset va gui KHOI_DONG_OK sau ~0.5s
        - Doc du lieu trong thoi_gian_cho giay
        - Neu thay KHOI_DONG_OK hoac PONG -> dung la Arduino
        - Neu khong thay -> khong phai Arduino

        Tra ve: True neu dung la Arduino, False neu khong phai.
        """
        import time
        with self._khoa:
            s = self._cong if self._cong and getattr(self._cong, "is_open", False) else None
        if not s:
            return False

        deadline = time.time() + thoi_gian_cho
        da_dung = False
        # Giai doan 1: Doc KHOI_DONG_OK tu khi Arduino reset
        while time.time() < deadline:
            try:
                dong = s.readline().decode("utf-8", errors="ignore").strip()
                self._cap_nhat_firmware(dong)
                if "KHOI_DONG_OK" in dong.upper() or "PONG" in dong.upper():
                    da_dung = True
                    if self.firmware:
                        return True
            except Exception:
                return False
        if da_dung:
            return True

        # Giai doan 2: Thu gui PING neu chua nhan duoc KHOI_DONG_OK
        try:
            s.reset_input_buffer()
            s.write(b"PING\n")
            s.flush()
        except Exception:
            return False

        deadline2 = time.time() + 2.0
        while time.time() < deadline2:
            try:
                dong = s.readline().decode("utf-8", errors="ignore").strip()
                self._cap_nhat_firmware(dong)
                if "PONG" in dong.upper():
                    return True
            except Exception:
                return False

        return False

    def _cap_nhat_firmware(self, dong):
        dong = (dong or "").strip()
        upper = dong.upper()
        if "FW_" not in upper:
            return
        if ":" in dong:
            self.firmware = dong.rsplit(":", 1)[-1].strip()
        else:
            self.firmware = dong

    def ngat(self):
        """Dong ket noi Serial."""
        with self._khoa:
            if self._cong:
                try:
                    self._cong.close()
                except Exception:
                    pass
                self._cong = None

    def dang_noi(self):
        """Kiem tra Arduino co dang ket noi khong."""
        with self._khoa:
            return self._cong is not None and getattr(self._cong, "is_open", False)

    # --- Gui lenh ---

    def gui_lenh(self, lenh):
        """Gui lenh den Arduino. VD: VAO_MO, VAO_DONG, RA_MO, RA_DONG."""
        with self._khoa:
            if not self._cong or not getattr(self._cong, "is_open", False):
                return
            self._cong.write((lenh.strip() + "\n").encode("utf-8"))
            self._cong.flush()

    # --- Doc cam bien ---

    def doc_cam_bien(self):
        """Doc trang thai cam bien tu Arduino.

        Arduino gui: CAM_BIEN:xe_vao=1,xe_ra=0
        Tra ve: {"xe_vao": True/False, "xe_ra": True/False}
        """
        # Chi giu lock NGAN de lay serial ref, KHONG giu lock trong readline!
        with self._khoa:
            s = self._cong if self._cong and getattr(self._cong, "is_open", False) else None
        if not s:
            return {}
        try:
            dong = s.readline().decode("utf-8", errors="ignore").strip()
        except Exception:
            return {}

        if not dong.upper().startswith("CAM_BIEN:"):
            return {}

        ket_qua = {}
        phan_data = dong.split(":", 1)[1]
        for cap in phan_data.split(","):
            if "=" not in cap:
                continue
            ten, gt = cap.split("=", 1)
            ten = ten.strip().lower()
            if ten in ("xe_vao", "xe_ra"):
                ket_qua[ten] = gt.strip() in ("1", "true", "on")
        return ket_qua
