"""Deterministic backend using fictitious data only; no hospital connection."""
from dataclasses import replace
import hashlib
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

    def _payload(self, step, dossier):
        if step == "diagnosis":
            t = dossier.sheets[0].clinical
            return hashlib.sha256(repr((t.diagnosis, t.icd, dossier.discharge)).encode()).hexdigest()
        if step == "services":
            return hashlib.sha256(repr(dossier.services).encode()).hexdigest()
        return digest(dossier.sheets[int(step[-1])-1])

    def execute(self, step, dossier):
        if self.fail_step == step:
            raise SafetyError("Lỗi mô phỏng trước lưu.")
        key = self.operation_key(dossier, step)
        if key in self.saved:
            raise SafetyError("Bản ghi đã tồn tại. Không tạo trùng.")
        self.calls.append(step)
        self.saved[key] = self._payload(step, dossier)
        self.persist()

    def verify(self, step, dossier):
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
