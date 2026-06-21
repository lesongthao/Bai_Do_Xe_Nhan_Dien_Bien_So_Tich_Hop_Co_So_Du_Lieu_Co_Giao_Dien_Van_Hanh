"""
Module quan ly co so du lieu bai xe bang SQLite.
Luu tru: bien so hop le (whitelist), xe dang trong bai, cai dat.
"""

import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime

from nhan_dien_bien_so import (
    chuan_hoa_bien_so,
)


class CSDLBaiXe:
    """Quan ly du lieu bai xe bang SQLite."""

    def __init__(self, duong_dan="co_so_du_lieu_bai_xe.db"):
        self.duong_dan = duong_dan
        self._khoa = threading.Lock()
        self._tao_bang()

    @contextmanager
    def _kn(self):
        kn = sqlite3.connect(self.duong_dan, check_same_thread=False)
        kn.row_factory = sqlite3.Row
        kn.execute("PRAGMA journal_mode=WAL")
        kn.execute("PRAGMA temp_store=MEMORY")
        try:
            yield kn
        finally:
            kn.close()

    def _chuan_hoa_bien_so(self, bien_so):
        return chuan_hoa_bien_so(bien_so)

    def _kiem_tra_bien_so(self, bien_so):
        bien_so = self._chuan_hoa_bien_so(bien_so)
        if not bien_so:
            raise ValueError("Bien so rong sau chuan hoa")
        return bien_so

    def _tao_bang(self):
        with self._khoa, self._kn() as kn:
            kn.executescript("""
                CREATE TABLE IF NOT EXISTS cai_dat (
                    khoa TEXT PRIMARY KEY, gia_tri TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS bien_so_hop_le (
                    bien_so TEXT PRIMARY KEY, chu_xe TEXT, tao_luc TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS xe_trong_bai (
                    bien_so TEXT PRIMARY KEY, vao_luc TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS lich_su_ra_vao (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bien_so TEXT NOT NULL,
                    su_kien TEXT NOT NULL,
                    thoi_gian TEXT NOT NULL,
                    ghi_chu TEXT
                );
            """)
            kn.execute("INSERT OR IGNORE INTO cai_dat VALUES ('suc_chua', '3')")
            self._chuan_hoa_du_lieu_cu(kn)
            kn.commit()

    def _chuan_hoa_du_lieu_cu(self, kn):
        """Sua du lieu cu neu bien so tung duoc luu kem dau/phay/sao."""
        for bang in ("bien_so_hop_le", "xe_trong_bai"):
            rows = kn.execute(f"SELECT * FROM {bang}").fetchall()
            for row in rows:
                cu = row["bien_so"]
                moi = self._chuan_hoa_bien_so(cu)
                if not moi:
                    kn.execute(f"DELETE FROM {bang} WHERE bien_so=?", (cu,))
                    continue
                if moi == cu:
                    continue
                if bang == "bien_so_hop_le":
                    kn.execute(
                        """
                        INSERT OR IGNORE INTO bien_so_hop_le (bien_so, chu_xe, tao_luc)
                        VALUES (?, ?, ?)
                        """,
                        (moi, row["chu_xe"], row["tao_luc"]),
                    )
                    kn.execute("DELETE FROM bien_so_hop_le WHERE bien_so=?", (cu,))
                else:
                    kn.execute(
                        "INSERT OR IGNORE INTO xe_trong_bai (bien_so, vao_luc) VALUES (?, ?)",
                        (moi, row["vao_luc"]),
                    )
                    kn.execute("DELETE FROM xe_trong_bai WHERE bien_so=?", (cu,))

    # --- Cai dat ---

    def lay_suc_chua(self):
        with self._khoa, self._kn() as kn:
            r = kn.execute("SELECT gia_tri FROM cai_dat WHERE khoa='suc_chua'").fetchone()
            return int(r["gia_tri"]) if r else 3

    # --- Bien so hop le (whitelist) ---

    def ds_bien_so(self):
        with self._khoa, self._kn() as kn:
            return [dict(r) for r in kn.execute(
                "SELECT bien_so, chu_xe FROM bien_so_hop_le ORDER BY tao_luc DESC"
            ).fetchall()]

    def them_bien_so(self, bien_so, chu_xe=None):
        bien_so = self._kiem_tra_bien_so(bien_so)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._khoa, self._kn() as kn:
            kn.execute("INSERT OR REPLACE INTO bien_so_hop_le VALUES (?,?,?)",
                       (bien_so, chu_xe, now))
            kn.commit()

    def xoa_bien_so(self, bien_so):
        bien_so = self._chuan_hoa_bien_so(bien_so)
        if not bien_so:
            return
        with self._khoa, self._kn() as kn:
            kn.execute("DELETE FROM bien_so_hop_le WHERE bien_so=?", (bien_so,))
            kn.commit()

    def la_hop_le(self, bien_so):
        bien_so = self._chuan_hoa_bien_so(bien_so)
        if not bien_so:
            return False
        with self._khoa, self._kn() as kn:
            return kn.execute("SELECT 1 FROM bien_so_hop_le WHERE bien_so=?",
                              (bien_so,)).fetchone() is not None

    # --- Xe trong bai ---

    def them_xe(self, bien_so):
        bien_so = self._kiem_tra_bien_so(bien_so)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._khoa, self._kn() as kn:
            try:
                kn.execute("INSERT INTO xe_trong_bai VALUES (?,?)", (bien_so, now))
                kn.execute(
                    "INSERT INTO lich_su_ra_vao (bien_so, su_kien, thoi_gian, ghi_chu) VALUES (?,?,?,?)",
                    (bien_so, "VAO", now, "Tu dong/duyet vao bai"),
                )
                kn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def xoa_xe(self, bien_so):
        bien_so = self._chuan_hoa_bien_so(bien_so)
        if not bien_so:
            return False
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._khoa, self._kn() as kn:
            c = kn.execute("DELETE FROM xe_trong_bai WHERE bien_so=?", (bien_so,))
            if c.rowcount > 0:
                kn.execute(
                    "INSERT INTO lich_su_ra_vao (bien_so, su_kien, thoi_gian, ghi_chu) VALUES (?,?,?,?)",
                    (bien_so, "RA", now, "Nhan dien tai cong ra"),
                )
            kn.commit()
            return c.rowcount > 0

    def so_xe(self):
        with self._khoa, self._kn() as kn:
            return kn.execute("SELECT COUNT(*) as sl FROM xe_trong_bai").fetchone()["sl"]

    def co_xe(self, bien_so):
        bien_so = self._chuan_hoa_bien_so(bien_so)
        if not bien_so:
            return False
        with self._khoa, self._kn() as kn:
            return kn.execute("SELECT 1 FROM xe_trong_bai WHERE bien_so=?",
                              (bien_so,)).fetchone() is not None

    def ds_xe(self):
        with self._khoa, self._kn() as kn:
            return [dict(r) for r in kn.execute(
                "SELECT bien_so, vao_luc FROM xe_trong_bai ORDER BY vao_luc ASC"
            ).fetchall()]

    def ds_lich_su(self, gioi_han=50):
        with self._khoa, self._kn() as kn:
            return [dict(r) for r in kn.execute(
                """
                SELECT bien_so, su_kien, thoi_gian, ghi_chu
                FROM lich_su_ra_vao
                ORDER BY id DESC
                LIMIT ?
                """,
                (gioi_han,),
            ).fetchall()]
