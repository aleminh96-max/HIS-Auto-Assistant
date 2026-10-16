from dataclasses import replace
import sys
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QLabel,QTabWidget,
    QTextEdit,QPushButton,QComboBox,QTableWidget,QTableWidgetItem,QCheckBox)
from .simulator import SimulatorAdapter
from .domain import DEPARTMENT


class SimulatorWindow(QMainWindow):
    def __init__(self, adapter=None):
        super().__init__()
        self.adapter = adapter or SimulatorAdapter()
        self.setWindowTitle("HIS Simulator — DỮ LIỆU GIẢ — không phải eHospital")
        self.resize(1000,650)
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        self.context_label = QLabel()
        layout.addWidget(self.context_label)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self.pages = {}
        for title in ("Bệnh án / Chẩn đoán", "Tổng kết", "F5 — Dịch vụ", "F7 — Tờ điều trị",
                      "Lĩnh dược", "Ký số / Báo cáo / In"):
            text = QTextEdit()
            text.setReadOnly(True)
            self.tabs.addTab(text,title)
            self.pages[title] = text
        self.meds = QTableWidget(0,15)
        self.meds.setHorizontalHeaderLabels(["Mặt hàng", "Sáng", "TG. Sáng", "Trưa", "TG. Trưa", "Chiều", "TG. Chiều",
            "Tối", "TG. Tối", "Khuya", "TG. Khuya", "Số ngày", "SL", "Cách dùng", "Không tính tiền"])
        self.tabs.addTab(self.meds,"Bảng thuốc (cuộn ngang)")
        layout.addWidget(QLabel("Gây lỗi mô phỏng để kiểm tra dừng an toàn:"))
        self.fault = QComboBox()
        self.fault.addItems(["Bình thường", "Đổi bệnh nhân", "Đổi đợt điều trị", "Sai khoa", "HIS treo", "Không có quyền ký", "Kết quả ký không rõ", "Lỗi lưu tờ 2"])
        self.fault.currentIndexChanged.connect(self.inject_fault)
        layout.addWidget(self.fault)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(500)
        self.refresh()

    def inject_fault(self, index):
        from .domain import PatientContext
        p = PatientContext("DEMO-0001","DEMO-DOT-01")
        if index == 1: p = replace(p,record_id="DEMO-0002")
        if index == 2: p = replace(p,episode_id="DEMO-DOT-02")
        if index == 3: p = replace(p,department="Khoa khác")
        if index == 4: p = replace(p,responsive=False)
        if index == 5: p = replace(p,permissions=("write","print"))
        self.adapter.patient = p
        self.adapter.unknown_signature = index == 6
        self.adapter.fail_step = "sheet2" if index == 7 else None
        self.refresh()

    def refresh(self):
        p = self.adapter.context()
        self.context_label.setText(f"DỮ LIỆU GIẢ | {p.record_id} | {p.episode_id}\n{p.department}")
        calls = self.adapter.calls
        self.pages["Bệnh án / Chẩn đoán"].setPlainText("Bản ghi mô phỏng đã xác minh: " + str(len(self.adapter.saved)) + "\n" + "\n".join(calls))
        self.pages["F7 — Tờ điều trị"].setPlainText("\n".join(s for s in calls if s.startswith("sheet")))
        self.pages["F5 — Dịch vụ"].setPlainText("Chỉ định mẫu không tự áp dụng.\n" + ("Đã lưu danh sách được duyệt" if "services" in calls else "Chưa lưu"))
        self.pages["Ký số / Báo cáo / In"].setPlainText(f"Chữ ký GIẢ: {len(self.adapter.signatures)}\nLệnh in GIẢ: {len(self.adapter.print_jobs)}\nKhông có PDF/Crystal Reports thật.")


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    window = SimulatorWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
