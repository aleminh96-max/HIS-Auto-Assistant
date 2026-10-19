"""Deterministic backend using fictitious data only; no hospital connection."""
from dataclasses import replace
import hashlib
import json
from .domain import PatientContext, SafetyError, digest


class SimulatorAdapter:
    def __init__(self, store=None):
        self.store = store
        self.patient = PatientContext("DEMO-0001", "DEMO-DOT-01")
        self.saved = {}
        self.signatures = {}
        self.print_jobs = {}
        self.calls = []
        self.fail_step = None
        self.unknown_signature = False
        self.signature_result = "SIGNED"
        self.fail_print = False
        if store:
            snapshot = store.setting("simulation_snapshot") or {}
            self.saved = snapshot.get("saved", {})
            self.signatures = snapshot.get("signatures", {})
            self.print_jobs = snapshot.get("print_jobs", {})
            self.calls = snapshot.get("calls", [])

    def persist(self):
        if self.store:
            # Store hashes and synthetic job IDs only, never dossier contents.
            self.store.setting("simulation_snapshot", {"saved": self.saved,"signatures":self.signatures,
                "print_jobs":self.print_jobs,"calls":self.calls})

    def context(self):
        return self.patient

    def operation_key(self, dossier, step):
        # Sheet identity independent of content to detect conflicting reruns.
        identity = repr(dossier.context.identity) + "|" + step
        if step.startswith("sheet"):
            identity += "|" + dossier.sheets[int(step[-1])-1].at.isoformat()
        return hashlib.sha256(identity.encode()).hexdigest()

    def required_permission(self, step):
        if step == "sign_orders":
            return "sign"
        if step.startswith("print_"):
            return "print"
        return "write"

    def skip_reason(self, step, dossier):
        if step in ("services", "sign_orders", "print_orders") and not dossier.services:
            return "Bản nháp không có chỉ định cận lâm sàng."
        if step == "print_external" and not dossier.sheets[1].medications:
            return "Bản nháp không có toa mua ngoài."
        if step in ("print_disclosure", "print_requisition") and not any(
                sheet.medications for sheet in dossier.sheets):
            return "Bản nháp không có thuốc cần công khai hoặc lĩnh."
        return ""

    def _document(self, step, dossier):
        from .documents import Document
        payloads = {
            "orders": {"services": dossier.services},
            "external_prescription": {"sheet": dossier.sheets[1]},
            "followup": {"sheets": dossier.sheets},
            "disclosure": {"medications": tuple(m for s in dossier.sheets for m in s.medications)},
            "requisition": {"sources": dossier.requisition_sources},
        }
        keys = {
            "sign_orders": ("orders", "Chỉ định cận lâm sàng mô phỏng"),
            "print_orders": ("orders", "Chỉ định cận lâm sàng mô phỏng"),
            "print_external": ("external_prescription", "Toa mua ngoài mô phỏng"),
            "print_followup": ("followup", "Phiếu theo dõi điều trị mô phỏng"),
            "print_disclosure": ("disclosure", "Phiếu công khai thuốc mô phỏng"),
            "print_requisition": ("requisition", "Phiếu lĩnh dược mô phỏng"),
        }
        key, title = keys[step]
        at = dossier.sheets[0].at.isoformat()
        return Document(dossier.context, f"{key}:{at}", title,
                        json.dumps(payloads[key], ensure_ascii=False, sort_keys=True, default=str))

    def _payload(self, step, dossier):
        if step == "patient_check":
            return hashlib.sha256(repr((dossier.context.identity, "write" in self.context().permissions)).encode()).hexdigest()
        if step == "diagnosis":
            t = dossier.sheets[0].clinical
            return hashlib.sha256(repr((t.diagnosis, t.icd, dossier.discharge)).encode()).hexdigest()
        if step == "services":
            return hashlib.sha256(repr(dossier.services).encode()).hexdigest()
        if step.startswith("sheet"):
            return digest(dossier.sheets[int(step[-1])-1])
        raise SafetyError(f"Thao tác simulator không được hỗ trợ: {step}")

    def execute(self, step, dossier):
        if self.fail_step == step:
            raise SafetyError("Lỗi mô phỏng trước lưu.")
        if self.skip_reason(step, dossier):
            raise SafetyError("Không thể thực hiện bước không áp dụng.")
        if step == "sign_orders":
            from .documents import SignatureManager
            manager = SignatureManager(self, self.store)
            manager.approve(self._document(step, dossier))
            manager.sign(self._document(step, dossier))
            return
        if step.startswith("print_"):
            from .documents import PrintConfig, PrintManager
            document = self._document(step, dossier)
            manager = PrintManager(self, self.store)
            manager.print(document, PrintConfig("Máy in mô phỏng", "A5", 1),
                          ["Máy in mô phỏng"], approved=True,
                          require_signature=(step == "print_orders"))
            return
        key = self.operation_key(dossier, step)
        if key in self.saved:
            raise SafetyError("Bản ghi đã tồn tại. Không tạo trùng.")
        self.calls.append(step)
        self.saved[key] = self._payload(step, dossier)
        self.persist()

    def verify(self, step, dossier):
        if step == "sign_orders":
            return self.signature_matches(self._document(step, dossier))
        if step.startswith("print_"):
            document = self._document(step, dossier)
            return any(fingerprint == document.fingerprint for fingerprint in self.print_jobs.values())
        if self.skip_reason(step, dossier):
            return False
        return self.saved.get(self.operation_key(dossier, step)) == self._payload(step, dossier)

    def sign(self, document):
        self.calls.append("sign")
        if self.unknown_signature:
            return "UNKNOWN"
        if self.signature_result != "SIGNED":
            return self.signature_result
        self.signatures[document.key] = document.fingerprint
        self.persist()
        return "SIGNED"

    def signature_matches(self, document):
        return self.signatures.get(document.key) == document.fingerprint

    def print_document(self, document, config):
        self.calls.append("print")
        if self.fail_print:
            raise SafetyError("Lỗi hàng đợi mô phỏng; không rõ lệnh đã nhận, không tự in lại.")
        job = f"SIM-{len(self.print_jobs)+1}"
        self.print_jobs[job] = document.fingerprint
        self.persist()
        return job
