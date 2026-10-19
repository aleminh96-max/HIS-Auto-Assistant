from enum import StrEnum
import time
from .domain import SafetyError, MAIN_SCREEN


class State(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING_FOR_REVIEW = "WAITING_FOR_REVIEW"
    APPROVED = "APPROVED"
    WAITING_FOR_SIGNATURE_RESULT = "WAITING_FOR_SIGNATURE_RESULT"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"


class Workflow:
    """One verified side effect per tick. Unknown outcomes never auto-retry."""
    STEPS = (
        "patient_check", "diagnosis", "services", "sign_orders", "print_orders",
        "sheet1", "sheet2", "print_external", "sheet3", "print_followup",
        "print_disclosure", "print_requisition",
    )
    STEP_LABELS = (
        "Kiểm tra bệnh nhân và khoa",
        "Nhập chẩn đoán và tổng kết bệnh án",
        "Chuẩn bị, xác nhận chỉ định cận lâm sàng",
        "Ký số các chỉ định đã phê duyệt",
        "In phiếu chỉ định",
        "Tạo tờ điều trị thứ nhất — Toa cấp thuốc",
        "Tạo tờ điều trị thứ hai — Toa mua ngoài",
        "In toa mua ngoài",
        "Tạo tờ điều trị thứ ba — không thuốc, +30 phút",
        "In phiếu theo dõi điều trị",
        "In phiếu công khai thuốc",
        "Lập và in phiếu lĩnh dược",
    )

    def __init__(self, adapter, store, timeout=10):
        self.adapter, self.store, self.timeout = adapter, store, timeout
        if getattr(adapter, "store", None) is None:
            adapter.store = store
        self.state = State.NOT_STARTED
        self.index = 0
        self.dossier = None
        self.error = ""
        self.approved_hash = None

    def prepare(self, dossier):
        if self.state in (State.RUNNING, State.PAUSED):
            raise SafetyError("Dừng quy trình hiện tại trước khi chuẩn bị lại.")
        self.dossier = dossier
        self.index = 0
        self.error = ""
        self.approved_hash = None
        self.check_context()
        if self.adapter.context().screen != MAIN_SCREEN:
            raise SafetyError("Chỉ khởi chạy tại màn hình BA Nội trú - Ngoại Trú.")
        self.state = State.WAITING_FOR_REVIEW

    def check_context(self, permission="write"):
        current = self.adapter.context()
        current.validate()
        if current.identity != self.dossier.context.identity:
            raise SafetyError("Bệnh nhân, đợt điều trị hoặc khoa đã thay đổi.")
        if permission not in current.permissions:
            raise SafetyError(f"Tài khoản không có quyền: {permission}")

    def approve(self, fingerprint):
        if self.state != State.WAITING_FOR_REVIEW or fingerprint != self.dossier.fingerprint:
            raise SafetyError("Nội dung thay đổi; cần xem trước và duyệt lại.")
        self.check_context()
        self.approved_hash = fingerprint
        self.state = State.APPROVED

    def start(self):
        if self.state not in (State.APPROVED, State.PAUSED):
            raise SafetyError("Hồ sơ chưa được duyệt hoặc không thể tiếp tục.")
        self.check_context()
        if self.approved_hash != self.dossier.fingerprint:
            raise SafetyError("Nội dung đã thay đổi sau duyệt.")
        self.state = State.RUNNING

    def pause(self):
        if self.state == State.RUNNING:
            self.state = State.PAUSED

    def stop(self):
        self.state = State.STOPPED
        self.store.audit("workflow", "STOPPED")

    def tick(self):
        if self.state != State.RUNNING:
            return
        try:
            self.check_context()
            if self.approved_hash != self.dossier.fingerprint:
                raise SafetyError("Nội dung thay đổi sau duyệt.")
            step = self.STEPS[self.index]
            key = self.adapter.operation_key(self.dossier, step)
            previous = self.store.operation(key)
            skip_reason = self.adapter.skip_reason(step, self.dossier)
            if previous and previous.startswith("SKIPPED:"):
                if skip_reason != previous[len("SKIPPED:"):]:
                    raise SafetyError("Điều kiện bỏ qua đã thay đổi. Chuẩn bị và duyệt lại hồ sơ.")
            elif previous and not self.adapter.verify(step, self.dossier):
                raise SafetyError("Trạng thái HIS không khớp nhật ký. Kiểm tra thủ công trước khi tiếp tục.")
            if not previous:
                if skip_reason:
                    self.store.mark(key, "SKIPPED:" + skip_reason)
                    self.store.audit(step, "SKIPPED")
                else:
                    # Persist BEFORE calling the adapter: a crash cannot cause blind retry.
                    self.store.mark(key, "PENDING")
                    started = time.monotonic()
                    self.adapter.execute(step, self.dossier)
                    if time.monotonic() - started > self.timeout:
                        raise SafetyError("Quá thời gian chờ. Không tự thực hiện lại.")
                    self.check_context(self.adapter.required_permission(step))
                    if not self.adapter.verify(step, self.dossier):
                        raise SafetyError("Chưa xác minh lưu thành công. Không tự thực hiện lại.")
                    self.store.mark(key, "COMPLETED")
                    self.store.audit(step, "COMPLETED")
            elif previous.startswith("SKIPPED:"):
                self.store.audit(step, "SKIPPED")
            else:
                self.store.mark(key, "COMPLETED")
                self.store.audit(step, "COMPLETED")
            self.index += 1
            if self.index == len(self.STEPS):
                self.state = State.COMPLETED
        except Exception as exc:
            self.state = State.FAILED
            self.error = str(exc)
            self.store.audit("workflow", "FAILED")

    def recover(self):
        """Resume only if the failed operation is absent or now verifiably complete."""
        if self.state != State.FAILED or not self.dossier or self.index >= len(self.STEPS):
            raise SafetyError("Không có bước lỗi có thể khôi phục.")
        self.check_context()
        if self.approved_hash != self.dossier.fingerprint:
            raise SafetyError("Nội dung duyệt đã thay đổi. Chuẩn bị và duyệt lại.")
        key = self.adapter.operation_key(self.dossier, self.STEPS[self.index])
        previous = self.store.operation(key)
        if previous == "PENDING":
            if not self.adapter.verify(self.STEPS[self.index], self.dossier):
                raise SafetyError("Kết quả thao tác chưa rõ. Kiểm tra simulator thủ công; không tự chạy lại.")
            self.store.mark(key, "COMPLETED")
            self.store.audit(self.STEPS[self.index], "RECOVERED")
            self.index += 1
        elif previous and previous.startswith("SKIPPED:"):
            if self.adapter.skip_reason(self.STEPS[self.index], self.dossier) != previous[len("SKIPPED:"):]:
                raise SafetyError("Điều kiện bỏ qua đã thay đổi. Chuẩn bị và duyệt lại.")
            self.index += 1
        elif previous:
            if not self.adapter.verify(self.STEPS[self.index], self.dossier):
                raise SafetyError("Không xác minh được thao tác trước đó. Không tự thực hiện lại.")
            self.index += 1
        self.error = ""
        self.state = State.APPROVED
