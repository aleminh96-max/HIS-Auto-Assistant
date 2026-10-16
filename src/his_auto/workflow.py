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
    def __init__(self, adapter, store, timeout=10):
        self.adapter, self.store, self.timeout = adapter, store, timeout
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
            steps = ("diagnosis", "services", "sheet1", "sheet2", "sheet3")
            step = steps[self.index]
            key = self.adapter.operation_key(self.dossier, step)
            previous = self.store.operation(key)
            if previous and not self.adapter.verify(step, self.dossier):
                raise SafetyError("Trạng thái HIS không khớp nhật ký. Kiểm tra thủ công trước khi tiếp tục.")
            if not previous:
                # Persist BEFORE calling the adapter: a crash cannot cause blind retry.
                self.store.mark(key, "PENDING")
                started = time.monotonic()
                self.adapter.execute(step, self.dossier)
                if time.monotonic() - started > self.timeout:
                    raise SafetyError("Quá thời gian chờ. Không tự thực hiện lại.")
                self.check_context()
                if not self.adapter.verify(step, self.dossier):
                    raise SafetyError("Chưa xác minh lưu thành công. Không tự thực hiện lại.")
            self.store.mark(key, "COMPLETED")
            self.store.audit(step, "COMPLETED")
            self.index += 1
            if self.index == len(steps):
                self.state = State.COMPLETED
        except Exception as exc:
            self.state = State.FAILED
            self.error = str(exc)
            self.store.audit("workflow", "FAILED")
