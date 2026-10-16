from dataclasses import dataclass
import hashlib
from .domain import PatientContext, SafetyError, digest


@dataclass(frozen=True)
class Document:
    context: PatientContext
    document_id: str
    kind: str
    content: str

    @property
    def key(self):
        return hashlib.sha256(repr((self.context.identity, self.document_id)).encode()).hexdigest()

    @property
    def fingerprint(self):
        return digest(self)


class SignatureManager:
    def __init__(self, adapter, store):
        self.adapter, self.store = adapter, store
        self.approved = None

    def validate(self, document, permission):
        current = self.adapter.context()
        current.validate()
        if current.identity != document.context.identity or permission not in current.permissions:
            raise SafetyError("Sai ngữ cảnh tài liệu hoặc không có quyền.")

    def approve(self, document):
        self.validate(document, "sign")
        self.approved = document.fingerprint

    def sign(self, document):
        self.validate(document, "sign")
        if self.approved != document.fingerprint:
            raise SafetyError("Chưa duyệt đúng phiên bản tài liệu.")
        key = "sign:" + document.key
        if self.store.operation(key):
            raise SafetyError("Đã gửi ký hoặc kết quả chưa rõ. Không tự ký lại.")
        self.store.mark(key, "PENDING")
        self.approved = None
        result = self.adapter.sign(document)
        self.validate(document, "sign")
        self.store.mark(key, result)
        self.store.audit("signature", result)
        if result != "SIGNED" or not self.adapter.signature_matches(document):
            raise SafetyError("Ký chưa thành công hoặc không rõ trạng thái; kiểm tra thủ công.")
        return result


@dataclass(frozen=True)
class PrintConfig:
    printer: str
    paper: str = "A5"
    copies: int = 1
    pages: str = "All"


class PrintManager:
    def __init__(self, adapter, store):
        self.adapter, self.store = adapter, store

    @staticmethod
    def windows_printers():
        try:
            import win32print
            return [p[2] for p in win32print.EnumPrinters(6)]
        except (ImportError, OSError):
            return []

    def print(self, document, config, available, approved=False, require_signature=True):
        SignatureManager(self.adapter, self.store).validate(document, "print")
        if not approved:
            raise SafetyError("Cần duyệt tài liệu và cấu hình in.")
        if config.printer not in available:
            raise SafetyError("Máy in không tồn tại hoặc đã đổi tên.")
        if type(config.copies) is not int or not 1 <= config.copies <= 20 or config.paper not in ("A4", "A5") or not config.pages.strip():
            raise SafetyError("Cấu hình in không hợp lệ.")
        if require_signature and not self.adapter.signature_matches(document):
            raise SafetyError("Tài liệu chưa được ký đúng phiên bản.")
        key = "print:" + document.key
        if self.store.operation(key):
            raise SafetyError("Đã gửi lệnh in hoặc kết quả chưa rõ. Không gửi lặp.")
        self.store.mark(key, "PENDING")
        job = self.adapter.print_document(document, config)
        if not job:
            raise SafetyError("Chưa xác minh hàng đợi in.")
        self.store.mark(key, "QUEUED")
        self.store.audit("print", "QUEUED")
        return job
