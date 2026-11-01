from dataclasses import asdict, replace
from datetime import datetime
from pathlib import Path
import json
import os
import sys
from PySide6.QtCore import QDateTime, QTimer, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox, QCheckBox,
    QDateTimeEdit, QTabWidget, QMessageBox, QFileDialog, QScrollArea, QSpinBox,
    QTableWidget, QTableWidgetItem, QProgressBar, QTreeWidget, QTreeWidgetItem,
    QGroupBox)
from .domain import (ClinicalTemplate, Group, Vitals, Medication, SafetyError, prepare_dossier,
                     validate_requisition_sources)
from .storage import Store
from .workflow import Workflow, State
from .simulator import SimulatorAdapter
from .documents import Document, SignatureManager, PrintManager, PrintConfig


def dossier_text(dossier):
    return json.dumps(asdict(dossier), ensure_ascii=False, indent=2, default=str)


class AssistantWindow(QMainWindow):
    def __init__(self, store=None):
        super().__init__()
        self.setWindowTitle("HIS Auto Assistant 0.1 — BẢN MÔ PHỎNG")
        self.resize(1220, 820)
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "HISAutoAssistant"
        self.store = store or Store(base / "assistant.sqlite3")
        self.adapter = SimulatorAdapter(self.store)
        self.workflow = Workflow(self.adapter, self.store)
        self.signature = SignatureManager(self.adapter, self.store)
        self.printer = PrintManager(self.adapter, self.store)
        self.dossier = None
        self.document = None
        self.sim_window = None
        self.workflow_started_at = None
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        banner = QLabel("HIS AUTO ASSISTANT   •   DỮ LIỆU GIẢ / KHÔNG KẾT NỐI HIS THẬT")
        banner.setStyleSheet("background:#153f61;color:white;padding:16px;font-size:17px;font-weight:bold")
        layout.addWidget(banner)
        self.status = QLabel()
        layout.addWidget(self.status)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self.make_home()
        self.make_clinical()
        self.make_templates()
        self.make_preview()
        self.make_settings()
        self.make_orders()
        self.actions = getattr(self, "actions", {})
        QShortcut(QKeySequence("Esc"), self, activated=self.workflow.stop)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.advance)
        self.timer.start(350)
        self.setStyleSheet("QLineEdit,QTextEdit,QComboBox,QDateTimeEdit,QSpinBox{padding:5px;} QPushButton{padding:8px;} QTabBar::tab{padding:10px;}")
        self.refresh_templates()
        default = self.store.setting("default_template")
        if default:
            self.template_list.setCurrentText(default)
            self.load_template()
        self.update_status()

    def page(self, title):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        self.tabs.addTab(scroll, title)
        return layout

    def button(self, layout, text, fn):
        b = QPushButton(text)
        b.clicked.connect(lambda checked=False: self.run(fn))
        layout.addWidget(b)
        return b

    def make_home(self):
        box = self.page("Tổng quan")
        patient = QGroupBox("Bệnh nhân và ngữ cảnh HIS")
        patient_layout = QVBoxLayout(patient)
        self.patient_summary = QLabel()
        self.patient_summary.setWordWrap(True)
        patient_layout.addWidget(self.patient_summary)
        box.addWidget(patient)
        self.group = QComboBox()
        self.group.addItems(list(Group))
        self.group.setCurrentText(Group.LATENT)
        self.group.currentTextChanged.connect(self.group_changed)
        box.addWidget(self.group)
        self.injection = QComboBox()
        self.injection.addItems(["Chưa chọn mũi", "Mũi 1", "Mũi 2", "Mũi 3"])
        box.addWidget(self.injection)
        self.history_confirm = QCheckBox("Đã xác nhận lịch sử điều trị và lần tiêm (dữ liệu giả)")
        box.addWidget(self.history_confirm)
        self.button(box, "Kiểm tra kết nối / đúng bệnh nhân mô phỏng", self.check_demo)
        self.button(box, "Mở HIS Simulator", self.open_simulator)
        self.button(box, "Phát hiện eHospital đang mở (chỉ đọc)", self.detect_live)
        live = QPushButton("Tự động hóa eHospital thật — CHƯA NGHIỆM THU")
        live.setEnabled(False)
        box.addWidget(live)
        progress_box = QGroupBox("Tiến trình quy trình")
        progress_layout = QVBoxLayout(progress_box)
        self.progress_label = QLabel("Chưa chuẩn bị hồ sơ mô phỏng")
        progress_layout.addWidget(self.progress_label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 12)
        self.progress.setValue(0)
        self.progress.setFormat("%p% — %v/12 mục đã xử lý hoặc bỏ qua có lý do")
        progress_layout.addWidget(self.progress)
        self.progress_detail = QLabel("Thời gian: 00:00 | Thời gian còn lại: chưa đủ dữ liệu")
        progress_layout.addWidget(self.progress_detail)
        box.addWidget(progress_box)
        preview_box = QGroupBox("Xem trước hồ sơ trước khi duyệt")
        preview_layout = QVBoxLayout(preview_box)
        self.inline_preview = QTextEdit()
        self.inline_preview.setReadOnly(True)
        self.inline_preview.setPlaceholderText("Chuẩn bị hồ sơ để xem bản xem trước tại đây.")
        self.inline_preview.setMaximumHeight(130)
        preview_layout.addWidget(self.inline_preview)
        box.addWidget(preview_box)
        self.timeline = QTreeWidget()
        self.timeline.setColumnCount(3)
        self.timeline.setHeaderLabels(["Công việc", "Trạng thái", "Chi tiết xác minh"])
        self.timeline.setRootIsDecorated(False)
        self.timeline.setAlternatingRowColors(True)
        self.timeline.setMinimumHeight(260)
        box.addWidget(self.timeline)
        self._timeline_items = []
        controls = QHBoxLayout()
        self.actions = {}
        for label, fn in (("1. Chuẩn bị và xem trước", self.prepare),
                          ("2. Duyệt nội dung", self.approve),
                          ("3. BẮT ĐẦU MÔ PHỎNG", self.start),
                          ("Tạm dừng", self.workflow.pause),
                          ("Tiếp tục", self.start),
                          ("Khôi phục sau lỗi đã kiểm tra", self.recover_workflow),
                          ("DỪNG KHẨN CẤP", self.workflow.stop)):
            button = QPushButton(label)
            button.clicked.connect(lambda checked=False, f=fn: self.run(f))
            controls.addWidget(button)
            self.actions[label] = button
        self.actions["3. BẮT ĐẦU MÔ PHỎNG"].setStyleSheet("background:#147d64;color:white;font-weight:bold;padding:14px")
        self.actions["DỪNG KHẨN CẤP"].setStyleSheet("background:#b52c38;color:white;font-weight:bold")
        box.addLayout(controls)
        log_box = QGroupBox("Nhật ký workflow đã ghi nhận")
        log_layout = QVBoxLayout(log_box)
        self.live_log = QTextEdit()
        self.live_log.setReadOnly(True)
        self.live_log.setMaximumHeight(130)
        log_layout.addWidget(self.live_log)
        box.addWidget(log_box)
        box.addStretch()

    def make_clinical(self):
        box = self.page("Nhập dữ liệu")
        form = QFormLayout()
        box.addLayout(form)
        self.fields = {}
        labels = {"name":"Tên mẫu", "diagnosis":"Chẩn đoán", "icd":"ICD bác sĩ chọn",
                  "subjective":"S — Hỏi bệnh", "objective":"O.1 — Khám bệnh", "labs":"O.3 — Cận lâm sàng",
                  "assessment":"A — Đánh giá", "plan":"P — Kế hoạch", "notes":"Ghi chú"}
        for name, label in labels.items():
            editor = QLineEdit() if name in ("name", "diagnosis", "icd") else QTextEdit()
            if isinstance(editor, QTextEdit):
                editor.setMaximumHeight(70)
            self.fields[name] = editor
            form.addRow(label, editor)
        self.fields["name"].setText("Mẫu cá nhân")
        self.fields["icd"].setText("A53.0")
        self.at = QDateTimeEdit(QDateTime.currentDateTime())
        self.at.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.measured = QDateTimeEdit(QDateTime.currentDateTime())
        self.measured.setDisplayFormat("dd/MM/yyyy HH:mm")
        form.addRow("Thời gian tờ 1 / tờ 2", self.at)
        form.addRow("Thời điểm đo gốc", self.measured)
        self.vital_fields = {}
        for name, label in (("pulse","Mạch (lần/phút)"), ("systolic","HA tâm thu (mmHg)"),
                            ("diastolic","HA tâm trương (mmHg)"), ("temperature","Nhiệt độ (°C)"),
                            ("respiration","Nhịp thở (lần/phút)"), ("spo2","SpO₂ (%)"),
                            ("weight","Cân nặng (kg)"), ("height","Chiều cao (cm)")):
            e = QLineEdit()
            e.setPlaceholderText("Nhập số đo đã xác nhận")
            self.vital_fields[name] = e
            form.addRow(label, e)
        self.third = QCheckBox("Đã kiểm tra nội dung tờ 3 và việc tham chiếu lần đo gốc (không tạo số đo mới)")
        self.abnormal = QCheckBox("Đã kiểm tra và xác nhận số đo nằm ngoài khoảng rà soát")
        box.addWidget(self.third)
        box.addWidget(self.abnormal)
        box.addWidget(QLabel("Thuốc, vật tư và dịch vụ tùy chọn nằm trong thẻ Soạn toa / lĩnh dược. Không tự áp dụng mẫu."))
        self.button(box, "Nạp dữ liệu GIẢ để chạy thử", self.demo_data)

    def make_templates(self):
        box = self.page("Quản lý mẫu")
        self.template_list = QComboBox()
        box.addWidget(self.template_list)
        for text, fn in (("Lưu mẫu từ ô nhập", self.save_template), ("Nạp mẫu đã chọn", self.load_template),
                         ("Nhân bản mẫu", self.duplicate_template), ("Đặt làm mặc định", self.default_template),
                         ("Xem lịch sử phiên bản", self.template_history), ("Xóa mẫu…", self.delete_template),
                         ("Xuất mẫu JSON…", self.export_templates), ("Nhập mẫu JSON…", self.import_templates),
                         ("Sao lưu dữ liệu…", self.backup)):
            self.button(box, text, fn)
        box.addStretch()

    def make_preview(self):
        box = self.page("Xem trước / ký / in")
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        box.addWidget(self.preview)
        self.button(box, "Duyệt hồ sơ đang xem", self.approve)
        self.button(box, "Duyệt và ký số tài liệu đang xem (MÔ PHỎNG)", self.sign)
        self.button(box, "Duyệt và in tài liệu đã ký (MÔ PHỎNG)", self.print_demo)

    def make_settings(self):
        box = self.page("Cấu hình / nhật ký")
        form = QFormLayout()
        box.addLayout(form)
        self.printer_name = QComboBox()
        self.printer_name.addItems(["Máy in mô phỏng"] + PrintManager.windows_printers())
        self.printer_name.setCurrentText(self.store.setting("printer") or "Máy in mô phỏng")
        form.addRow("Máy in (không gửi in thật)", self.printer_name)
        self.paper = QComboBox()
        self.paper.addItems(["A5", "A4"])
        form.addRow("Khổ giấy", self.paper)
        self.copies = QSpinBox()
        self.copies.setRange(1,20)
        form.addRow("Số bản", self.copies)
        self.button(box, "Lưu cấu hình máy in", lambda: self.store.setting("printer", self.printer_name.currentText()))
        self.floating = QCheckBox("Cửa sổ nổi trên cùng")
        self.floating.toggled.connect(self.float_window)
        box.addWidget(self.floating)
        self.button(box, "Xem nhật ký (không chứa nội dung bệnh án)", self.show_audit)
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        box.addWidget(self.logs)
        screen = QApplication.primaryScreen()
        box.addWidget(QLabel(f"Màn hình hiện tại: {screen.size().width()} × {screen.size().height()} | DPI: {screen.logicalDotsPerInch():.0f}\nHiệu chỉnh HIS thật: CHƯA KIỂM CHỨNG; chưa bật nhấp tọa độ."))

    def run(self, fn):
        try:
            fn()
        except Exception as exc:
            QMessageBox.warning(self, "Cần kiểm tra", str(exc))
        self.update_status()

    def make_orders(self):
        box = self.page("Soạn toa / lĩnh dược")
        box.addWidget(QLabel("DỮ LIỆU KIỂM THỬ. Tên và mã TEST chỉ dùng trong simulator, không phải danh mục eHospital.\nChỉnh tổng liều theo dữ liệu giả đã duyệt; không suy ra tổng liều từ số lượng lọ."))
        self.order_table = QTableWidget(0,9)
        self.order_table.setHorizontalHeaderLabels(["Mã TEST", "Tên / quy cách", "SL", "Cách dùng", "Giờ sử dụng (ISO)", "Miễn phí (0/1)", "Hàm lượng / quy cách", "Tổng liều đã duyệt", "Kho nhận"])
        self.order_table.setMinimumHeight(250)
        self.order_table.setColumnWidth(1,350)
        box.addWidget(self.order_table)
        self.button(box,"Nạp danh mục mẫu khảo sát (chưa duyệt)",self.load_survey)
        self.button(box,"Xóa dòng đang chọn",self.remove_order)
        self.med_review = QCheckBox("Đã duyệt đúng mặt hàng, hàm lượng, tổng liều, cách dùng, thời gian, dị ứng và yếu tố an toàn (TEST)")
        box.addWidget(self.med_review)
        box.addWidget(QLabel("Dịch vụ đã duyệt (mỗi dòng một tên; để trống nếu không chỉ định):"))
        self.services = QTextEdit()
        self.services.setMaximumHeight(85)
        box.addWidget(self.services)
        self.button(box,"Nạp dịch vụ mẫu TEST",lambda: self.services.setPlainText("[TEST] Công chích STD\n[TEST] Test lẫy da (Prick test)"))
        box.addWidget(QLabel("Nếu có thuốc, nhập đủ ba nguồn JSON theo cùng mã và số lượng TEST. Tổng phải khớp các toa đã duyệt. Để trống cả ba nếu không có thuốc."))
        self.reconcile_inputs = []
        for label in ("Y lệnh", "Tổng hợp", "Phiếu lĩnh"):
            e = QLineEdit()
            e.setPlaceholderText(label + ': {"TEST-BENZ": 2}')
            box.addWidget(e)
            self.reconcile_inputs.append(e)
        self.button(box,"Kiểm tra ba nguồn số lượng",self.check_requisition)

    def load_survey(self):
        from .drafts import survey_drafts
        self.order_table.setRowCount(0)
        for m in survey_drafts(self.at.dateTime().toPython().astimezone()):
            row = self.order_table.rowCount()
            self.order_table.insertRow(row)
            for col,value in enumerate((m.catalog_id,m.name,m.quantity,m.route,m.use_at.isoformat(),int(m.free),m.strength,m.total_dose,"Kho miễn phí" if m.free else "Nhà thuốc")):
                self.order_table.setItem(row,col,QTableWidgetItem(str(value)))
        self.med_review.setChecked(False)

    def remove_order(self):
        row = self.order_table.currentRow()
        if row >= 0: self.order_table.removeRow(row)

    def medication_drafts(self):
        from .drafts import SURVEY_ITEMS, validate_catalog
        rows = []
        catalog = {item[0]:"[TEST] " + item[1] for item in SURVEY_ITEMS}
        for row in range(self.order_table.rowCount()):
            cells = [self.order_table.item(row,c).text().strip() if self.order_table.item(row,c) else "" for c in range(9)]
            code,name,quantity,route,at,free,strength,dose,warehouse = cells
            if free not in ("0","1") or warehouse != ("Kho miễn phí" if free == "1" else "Nhà thuốc"):
                raise SafetyError("Kiểm tra loại toa và nơi nhận thuốc.")
            rows.append(Medication(code,name,int(quantity),route,datetime.fromisoformat(at),free=="1",strength,dose))
        validate_catalog(rows,catalog)
        return tuple(m for m in rows if m.free),tuple(m for m in rows if not m.free)

    def check_requisition(self):
        free, external = self.medication_drafts()
        sources = self.requisition_source_data()
        normalized = validate_requisition_sources(tuple(free) + tuple(external), sources)
        message = "Ba nguồn khớp với toa TEST đã duyệt." if normalized else "Không có thuốc; bước lĩnh dược sẽ được bỏ qua có lý do."
        QMessageBox.information(self,"Đối chiếu TEST",message + " Chưa gửi lệnh tới HIS hoặc máy in thật.")

    def requisition_source_data(self):
        raw = [editor.text().strip() for editor in self.reconcile_inputs]
        if not any(raw):
            return ()
        if not all(raw):
            raise SafetyError("Nhập đủ cả ba nguồn số lượng lĩnh hoặc xóa cả ba.")
        try:
            sources = tuple(json.loads(value) for value in raw)
        except json.JSONDecodeError:
            raise SafetyError("Số lượng lĩnh phải là JSON hợp lệ, ví dụ {\"TEST-MED\": 2}.") from None
        if any(not isinstance(source, dict) for source in sources):
            raise SafetyError("Mỗi nguồn số lượng phải là một đối tượng JSON theo mã TEST.")
        return sources

    def group_changed(self, value):
        if not hasattr(self, "fields"):
            return
        self.fields["icd"].setText("A53.0" if value == Group.LATENT else "")
        self.injection.setCurrentIndex(0)
        self.history_confirm.setChecked(False)

    def current_template(self):
        values = {name: e.text() if isinstance(e,QLineEdit) else e.toPlainText() for name,e in self.fields.items()}
        return ClinicalTemplate(group=self.group.currentText(), **values)

    def fill_template(self, t):
        self.group.setCurrentText(t.group)
        for name,e in self.fields.items():
            e.setText(str(getattr(t,name))) if isinstance(e,QLineEdit) else e.setPlainText(str(getattr(t,name)))

    def current_dossier(self):
        at = self.at.dateTime().toPython().astimezone()
        measured = self.measured.dateTime().toPython().astimezone()
        vitals = Vitals(measured, **{n:float(e.text().replace(",",".")) for n,e in self.vital_fields.items()})
        free,external = self.medication_drafts()
        requisition_sources = self.requisition_source_data()
        return prepare_dossier(self.adapter.context(), self.current_template(), vitals, at,free=free,external=external,
            services=tuple(line.strip() for line in self.services.toPlainText().splitlines() if line.strip()),
            medication_reviewed=self.med_review.isChecked(),
            requisition_sources=requisition_sources,
            injection=self.injection.currentIndex() or None, history_confirmed=self.history_confirm.isChecked(),
            third_reviewed=self.third.isChecked(), abnormal_reviewed=self.abnormal.isChecked())

    def prepare(self):
        self.dossier = self.current_dossier()
        self.workflow.prepare(self.dossier)
        self.document = Document(self.dossier.context, "DEMO-" + self.dossier.sheets[0].at.isoformat(), "Ba tờ điều trị mô phỏng", dossier_text(self.dossier))
        preview_text = "DỮ LIỆU GIẢ — KHÔNG PHẢI Y LỆNH\n" + self.document.content
        self.preview.setPlainText(preview_text)
        self.inline_preview.setPlainText(preview_text)

    def ensure_unchanged(self):
        if not self.dossier or self.current_dossier().fingerprint != self.dossier.fingerprint:
            raise SafetyError("Dữ liệu đã thay đổi. Chuẩn bị và duyệt lại hồ sơ.")

    def approve(self):
        self.ensure_unchanged()
        self.workflow.approve(self.dossier.fingerprint)

    def start(self):
        self.ensure_unchanged()
        if self.workflow.state != State.PAUSED:
            self.workflow_started_at = datetime.now().astimezone()
        self.workflow.start()

    def recover_workflow(self):
        self.ensure_unchanged()
        self.workflow.recover()

    def advance(self):
        if self.workflow.state == State.RUNNING:
            try:
                self.ensure_unchanged()
                self.workflow.tick()
            except Exception as exc:
                self.workflow.state = State.FAILED
                self.workflow.error = str(exc)
        self.update_status()
        if self.sim_window:
            self.sim_window.refresh()

    def update_status(self):
        self.status.setText(f"CHẾ ĐỘ MÔ PHỎNG — không kết nối HIS thật | {self.workflow.state} | {self.workflow.error}")
        if hasattr(self, "timeline"):
            self.refresh_dashboard()
        if hasattr(self,"actions"):
            self.actions["3. BẮT ĐẦU MÔ PHỎNG"].setEnabled(self.workflow.state == State.APPROVED)
            self.actions["Tiếp tục"].setEnabled(self.workflow.state == State.PAUSED)
            self.actions["Khôi phục sau lỗi đã kiểm tra"].setEnabled(self.workflow.state == State.FAILED)
            self.actions["Tạm dừng"].setEnabled(self.workflow.state == State.RUNNING)

    def refresh_dashboard(self):
        context = self.adapter.context()
        prepared = self.workflow.state != State.NOT_STARTED
        context_valid = False
        if prepared and self.dossier:
            try:
                context.validate()
                context_valid = (context.identity == self.dossier.context.identity and
                                 "write" in context.permissions)
            except SafetyError:
                context_valid = False
        self.patient_summary.setText(
            f"Kết nối: HIS Simulator (dữ liệu giả) | Khoa: {context.department} — "
            f"{'đúng' if context.department == 'Khoa Điều trị Nội trú ban ngày' else 'không đúng'}\n"
            f"Bệnh nhân: {context.record_id} | Đợt điều trị: {context.episode_id}\n"
            f"Nhóm: {self.group.currentText()} | ICD: {self.fields['icd'].text() if hasattr(self, 'fields') else '—'} | "
            f"Lần tiêm: {self.injection.currentText()}"
        )
        specs = list(zip(self.workflow.STEP_LABELS, self.workflow.STEPS))
        verified_count = 0
        rows = []
        for number, (title, step) in enumerate(specs, 1):
            state, detail = ("CHƯA CHUẨN BỊ", "" if context_valid else "Chỉ chạy trên HIS Simulator giả")
            if prepared and self.dossier:
                if not context_valid:
                    state, detail = "NGỮ CẢNH KHÔNG KHỚP", "Không thực hiện thao tác"
                else:
                    key = self.adapter.operation_key(self.dossier, step)
                    persisted = self.store.operation(key)
                if not context_valid:
                    pass
                elif persisted and persisted.startswith("SKIPPED:"):
                    state, detail = "BỎ QUA CÓ LÝ DO", persisted[len("SKIPPED:"):]
                    verified_count += 1
                elif persisted == "COMPLETED" and self.adapter.verify(step, self.dossier):
                    state, detail = "ĐÃ XÁC MINH", "Trạng thái đã lưu khớp dữ liệu simulator"
                    verified_count += 1
                elif persisted == "PENDING":
                    state, detail = "CẦN KIỂM TRA", "Thao tác có thể đã chạy; không tự gửi lại"
                elif self.workflow.state == State.FAILED and self.workflow.index == number - 1:
                    state, detail = "LỖI / CẦN KIỂM TRA", self.workflow.error
                elif self.workflow.state == State.RUNNING and self.workflow.index == number - 1:
                    state, detail = "ĐANG THỰC HIỆN", "Đang xử lý simulator"
                elif self.workflow.state == State.PAUSED and self.workflow.index == number - 1:
                    state, detail = "TẠM DỪNG", "Có thể tiếp tục"
                elif not context_valid:
                    state, detail = "NGỮ CẢNH KHÔNG KHỚP", "Không thực hiện thao tác"
                else:
                    state, detail = "CHỜ THỰC HIỆN", ""
            rows.append((number, title, state, detail))
        if not self._timeline_items:
            for _ in rows:
                item = QTreeWidgetItem(["", "", ""])
                self.timeline.addTopLevelItem(item)
                self._timeline_items.append(item)
        for item, (number, title, state, detail) in zip(self._timeline_items, rows):
            item.setText(0, f"{number}. {title}")
            item.setText(1, state)
            item.setText(2, detail)
        self.timeline.resizeColumnToContents(0)
        self.timeline.resizeColumnToContents(1)
        self.progress.setValue(verified_count)
        self.progress_label.setText(f"Đã xử lý / bỏ qua có lý do {verified_count}/12 mục — {self.workflow.state}")
        if self.workflow.state == State.RUNNING and self.workflow.index < len(specs):
            active = f"Đang thực hiện: {specs[self.workflow.index][0]}"
        elif self.workflow.state == State.FAILED:
            active = f"Đã dừng do lỗi: {self.workflow.error}"
        elif self.workflow.state == State.COMPLETED:
            active = "Đã xử lý và xác minh đủ 12 bước mô phỏng."
        else:
            active = f"Trạng thái hiện tại: {self.workflow.state}"
        elapsed = "00:00"
        if self.workflow_started_at:
            seconds = max(0, int((datetime.now().astimezone() - self.workflow_started_at).total_seconds()))
            elapsed = f"{seconds // 60:02d}:{seconds % 60:02d}"
        self.progress_detail.setText(f"{active} | Thời gian: {elapsed} | Còn lại: chưa đủ dữ liệu dự báo")
        events = self.store.db.execute("SELECT at,event,status FROM audit ORDER BY id DESC LIMIT 30").fetchall()
        log_text = "\n".join(" | ".join(map(str, row)) for row in reversed(events)) or "Chưa có sự kiện workflow được ghi nhận."
        if self.live_log.toPlainText() != log_text:
            self.live_log.setPlainText(log_text)

    def sign(self):
        self.ensure_unchanged()
        if self.workflow.state != State.COMPLETED:
            raise SafetyError("Hoàn thành và xác minh lưu mô phỏng trước khi ký.")
        self.signature.approve(self.document)
        self.signature.sign(self.document)
        QMessageBox.information(self,"Ký mô phỏng","Đã ký một lần. Không có chữ ký thật.")

    def print_demo(self):
        self.ensure_unchanged()
        config = PrintConfig(self.printer_name.currentText(),self.paper.currentText(),self.copies.value())
        job = self.printer.print(self.document,config,["Máy in mô phỏng"] + PrintManager.windows_printers(),approved=True)
        QMessageBox.information(self,"In mô phỏng",f"Đã xếp hàng {job}. Không gửi tới máy in thật.")

    def refresh_templates(self):
        self.template_list.clear()
        self.template_list.addItems([t.name for t in self.store.templates()])

    def save_template(self):
        self.store.save_template(self.current_template())
        self.refresh_templates()

    def load_template(self):
        matches = [t for t in self.store.templates() if t.name == self.template_list.currentText()]
        if matches:
            self.fill_template(matches[0])

    def duplicate_template(self):
        self.load_template()
        self.fields["name"].setText(self.fields["name"].text()+" (bản sao)")
        self.save_template()

    def default_template(self):
        if self.template_list.currentText():
            self.store.setting("default_template", self.template_list.currentText())

    def template_history(self):
        versions = self.store.history(self.template_list.currentText())
        self.preview.setPlainText(json.dumps([asdict(t) for t in versions],ensure_ascii=False,indent=2))
        self.tabs.setCurrentIndex(3)

    def delete_template(self):
        name = self.template_list.currentText()
        if name and QMessageBox.question(self,"Xóa mẫu",f"Xóa toàn bộ phiên bản của mẫu '{name}'?") == QMessageBox.Yes:
            self.store.delete_template(name,confirmed=True)
            self.refresh_templates()

    def export_templates(self):
        path,_ = QFileDialog.getSaveFileName(self,"Xuất mẫu","mau-benh-an.json","JSON (*.json)")
        if path: self.store.export_templates(path)

    def import_templates(self):
        path,_ = QFileDialog.getOpenFileName(self,"Nhập mẫu","","JSON (*.json)")
        if path:
            self.store.import_templates(path)
            self.refresh_templates()

    def backup(self):
        path,_ = QFileDialog.getSaveFileName(self,"Sao lưu","his-backup.sqlite3","SQLite (*.sqlite3)")
        if path: self.store.backup(path)

    def show_audit(self):
        self.logs.setPlainText("\n".join(" | ".join(row) for row in self.store.db.execute("SELECT at,event,status FROM audit ORDER BY id DESC LIMIT 100")))

    def float_window(self, enabled):
        self.setWindowFlag(Qt.WindowStaysOnTopHint,enabled)
        self.show()

    def check_demo(self):
        self.adapter.context().validate()
        QMessageBox.information(self,"Ngữ cảnh mô phỏng",repr(self.adapter.context()))

    def detect_live(self):
        from .recognition import LiveAdapter
        report = LiveAdapter().inspect()
        lines = [
            f"Tiến trình eHospital: {report['processes_detected']}",
            f"Cửa sổ được nhận diện: {report['windows_detected']}",
        ]
        for index, window in enumerate(report["windows"], 1):
            size = window.get("window_size", {})
            hint = window.get("screen_hint") or "chưa đủ mốc tĩnh để phân loại"
            count = sum(window.get("controls_by_type", {}).values())
            lines.append(f"Cửa sổ {index}: {size.get('width', 0)}×{size.get('height', 0)}, {count} điều khiển, {hint}")
        lines.append("Chỉ đọc metadata UI. Chưa xác minh bệnh nhân, đợt, khoa hoặc quyền HIS; mọi thao tác ghi, ký và in vẫn khóa.")
        message = "\n".join(lines)
        if report["processes_detected"] != 1:
            QMessageBox.warning(self, "eHospital chưa xác định duy nhất", message)
        else:
            QMessageBox.information(self, "Khảo sát eHospital chỉ đọc", message)

    def open_simulator(self):
        from .simulator_ui import SimulatorWindow
        if not self.sim_window:
            self.sim_window = SimulatorWindow(self.adapter)
        self.sim_window.show()

    def demo_data(self):
        self.fill_template(ClinicalTemplate("DEMO — Tiềm ẩn",diagnosis="DEMO: Giang mai tiềm ẩn; Mũi 1",
            subjective="DỮ LIỆU GIẢ — nội dung hỏi bệnh do người dùng thử nhập",
            objective="DỮ LIỆU GIẢ — không sử dụng cho người bệnh thật",
            labs="DEMO — chưa nhập kết quả",assessment="DEMO — chờ đánh giá",plan="DEMO — chờ bác sĩ xác nhận"))
        self.injection.setCurrentIndex(1)
        for name,value in {"pulse":80,"systolic":120,"diastolic":80,"temperature":37,"respiration":18,"spo2":98,"weight":60,"height":165}.items():
            self.vital_fields[name].setText(str(value))
        now = QDateTime.currentDateTime()
        self.measured.setDateTime(now)
        self.at.setDateTime(now)
        # Review checkboxes deliberately remain unchecked.
        self.history_confirm.setChecked(False)
        self.third.setChecked(False)

    def closeEvent(self, event):
        self.workflow.stop()
        if self.sim_window: self.sim_window.close()
        super().closeEvent(event)


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    window = AssistantWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
