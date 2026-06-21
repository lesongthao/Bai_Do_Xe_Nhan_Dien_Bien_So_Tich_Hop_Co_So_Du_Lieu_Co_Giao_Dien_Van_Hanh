#include <Servo.h>

/*
  Dieu khien barie bai xe (LM393) - ban Viet hoa
  Lenh nhan qua Serial:
    VAO_MO
    VAO_DONG
    RA_MO
    RA_DONG
    TRANG_THAI
    PING
    SERVO_TEST

  Du lieu gui ve:
    CAM_BIEN:xe_vao=1,xe_ra=0
*/

// Chan ket noi phan cung
const int CHAN_SERVO_VAO = 9;
const int CHAN_SERVO_RA = 10;
const int CHAN_CAM_BIEN_XE_VAO = 2;
const int CHAN_CAM_BIEN_XE_RA = 3;

const char* PHIEN_BAN_FW = "FW_BARIE_SMOOTH_20MS";

// Goc quay barie
const int GOC_MO_VAO = 90;
const int GOC_DONG_VAO = 0;
const int GOC_MO_RA = 90;
const int GOC_DONG_RA = 0;

// Toc do servo: moi buoc 1 do, tre 20ms -> quay 90 do mat khoang 1.8 giay.
// Tang len 15-20 neu muon cham hon; giam xuong 8-10 neu muon nhanh hon.
const int SERVO_BUOC_DO = 1;
const int SERVO_TRE_BUOC_MS = 20;

// Cau hinh cam bien LM393 (DO)
const bool CAM_BIEN_TAC_DONG_MUC_THAP = true;
const unsigned long CHU_KY_GUI_TRANG_THAI_MS = 300;

Servo servoVao;
Servo servoRa;

// Goc hien tai va goc dich cua moi servo (state machine)
int gocHienTaiVao = GOC_DONG_VAO;
int gocHienTaiRa = GOC_DONG_RA;
int gocDichVao = GOC_DONG_VAO;
int gocDichRa = GOC_DONG_RA;
unsigned long mocBuocVao = 0;
unsigned long mocBuocRa = 0;

bool xeVao = false;
bool xeRa = false;

bool xeVaoTruoc = false;
bool xeRaTruoc = false;

unsigned long mocGuiGanNhat = 0;
String boDemLenh = "";

bool docCamBien(int chan) {
  int giaTri = digitalRead(chan);
  if (CAM_BIEN_TAC_DONG_MUC_THAP) return giaTri == LOW;
  return giaTri == HIGH;
}

void capNhatCamBien() {
  xeVao = docCamBien(CHAN_CAM_BIEN_XE_VAO);
  xeRa = docCamBien(CHAN_CAM_BIEN_XE_RA);
}

void guiThongTin(const char* noiDung) {
  Serial.println(noiDung);
}

void guiThongTin(String noiDung) {
  Serial.println(noiDung);
}

void guiTrangThaiCamBien() {
  Serial.print("CAM_BIEN:xe_vao=");
  Serial.print(xeVao ? 1 : 0);
  Serial.print(",xe_ra=");
  Serial.println(xeRa ? 1 : 0);
}

// Non-blocking: quay servo 1 buoc (1 do) moi lan goi, chi khi du 20ms.
// Goi lien tuc trong loop() de servo quay muot ma khong block.
void capNhatMotServo(Servo &servo, int &gocHienTai, int gocDich, unsigned long &mocBuoc) {
  if (gocHienTai == gocDich) return;

  unsigned long now = millis();
  if (now - mocBuoc < (unsigned long)SERVO_TRE_BUOC_MS) return;
  mocBuoc = now;

  if (gocHienTai < gocDich) {
    gocHienTai = min(gocHienTai + SERVO_BUOC_DO, gocDich);
  } else {
    gocHienTai = max(gocHienTai - SERVO_BUOC_DO, gocDich);
  }
  servo.write(gocHienTai);
}

void capNhatServo() {
  capNhatMotServo(servoVao, gocHienTaiVao, gocDichVao, mocBuocVao);
  capNhatMotServo(servoRa, gocHienTaiRa, gocDichRa, mocBuocRa);
}

void datBarieVao(bool mo) {
  gocDichVao = mo ? GOC_MO_VAO : GOC_DONG_VAO;
}

void datBarieRa(bool mo) {
  gocDichRa = mo ? GOC_MO_RA : GOC_DONG_RA;
}

void xuLyLenh(String lenh) {
  lenh.trim();
  if (lenh == "VAO_MO") { datBarieVao(true); guiThongTin("OK:VAO_MO"); return; }
  if (lenh == "VAO_DONG") { datBarieVao(false); guiThongTin("OK:VAO_DONG"); return; }
  if (lenh == "RA_MO") { datBarieRa(true); guiThongTin("OK:RA_MO"); return; }
  if (lenh == "RA_DONG") { datBarieRa(false); guiThongTin("OK:RA_DONG"); return; }
  if (lenh == "TRANG_THAI") { guiTrangThaiCamBien(); return; }
  if (lenh == "PING") { guiThongTin("PONG:FW_BARIE_SMOOTH_20MS"); return; }
  if (lenh == "SERVO_TEST") {
    datBarieVao(true);
    datBarieRa(true);
    guiThongTin("SERVO_TEST_MO");
    return;
  }

  Serial.print("LOI:LENH_KHONG_HOP_LE:");
  Serial.println(lenh);
}


void docLenhSerial() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (boDemLenh.length() > 0) {
        xuLyLenh(boDemLenh);
        boDemLenh = "";
      }
    } else {
      boDemLenh += c;
      if (boDemLenh.length() > 120) {
        boDemLenh = "";
        guiThongTin("RESET_BO_DEM");
      }
    }
  }
}

void setup() {
  pinMode(CHAN_CAM_BIEN_XE_VAO, INPUT_PULLUP);
  pinMode(CHAN_CAM_BIEN_XE_RA, INPUT_PULLUP);


  servoVao.attach(CHAN_SERVO_VAO);
  servoRa.attach(CHAN_SERVO_RA);

  gocHienTaiVao = GOC_DONG_VAO;
  gocHienTaiRa = GOC_DONG_RA;
  gocDichVao = GOC_DONG_VAO;
  gocDichRa = GOC_DONG_RA;
  servoVao.write(gocHienTaiVao);
  servoRa.write(gocHienTaiRa);

  Serial.begin(9600);
  delay(400);

  capNhatCamBien();
  xeVaoTruoc = xeVao;
  xeRaTruoc = xeRa;

  guiThongTin("KHOI_DONG_OK");
  guiThongTin(PHIEN_BAN_FW);
  guiTrangThaiCamBien();
}

void loop() {
  docLenhSerial();
  capNhatCamBien();
  capNhatServo();

  bool thayDoi = (xeVao != xeVaoTruoc) || (xeRa != xeRaTruoc);
  unsigned long hienTai = millis();

  if (thayDoi || (hienTai - mocGuiGanNhat >= CHU_KY_GUI_TRANG_THAI_MS)) {
    guiTrangThaiCamBien();
    mocGuiGanNhat = hienTai;
    xeVaoTruoc = xeVao;
    xeRaTruoc = xeRa;
  }

  delay(5);
}
