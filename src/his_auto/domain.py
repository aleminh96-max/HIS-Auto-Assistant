from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum
import hashlib
import json
import math

DEPARTMENT = "Khoa Điều trị Nội trú ban ngày"
MAIN_SCREEN = "BA Nội trú - Ngoại Trú"


class SafetyError(ValueError):
    pass


class Group(StrEnum):
    EARLY = "Giang mai sớm"
    LATENT = "Giang mai tiềm ẩn, không rõ sớm hoặc muộn"


@dataclass(frozen=True)
class PatientContext:
    record_id: str
    episode_id: str
    department: str = DEPARTMENT
    process: str = "HISSimulator.exe"
    screen: str = MAIN_SCREEN
    permissions: tuple[str, ...] = ("write", "sign", "print")
    responsive: bool = True

    def validate(self, simulation=True):
        expected = "HISSimulator.exe" if simulation else "eHospital.exe"
        if self.process != expected:
            raise SafetyError("Sai tiến trình HIS.")
        if not self.responsive or self.screen not in (MAIN_SCREEN, "F5", "F7", "Lĩnh dược", "Ký số", "Báo cáo", "In"):
            raise SafetyError("Mất cửa sổ, sai màn hình hoặc HIS không phản hồi.")
        if self.department != DEPARTMENT:
            raise SafetyError("Sai khoa được phép.")
        if not self.record_id.strip() or not self.episode_id.strip():
            raise SafetyError("Chưa xác định mã bệnh án / đợt điều trị.")

    @property
    def identity(self):
        return self.record_id, self.episode_id, self.department, self.process


@dataclass(frozen=True)
class ClinicalTemplate:
    name: str
    group: str = Group.LATENT
    diagnosis: str = ""
    icd: str = "A53.0"
    subjective: str = ""
    objective: str = ""
    labs: str = ""
    assessment: str = ""
    plan: str = ""
    notes: str = ""
    version: int = 1

    def validate(self):
        if not self.name.strip() or self.group not in tuple(Group):
            raise SafetyError("Tên mẫu hoặc nhóm bệnh không hợp lệ.")
        if self.group == Group.LATENT and self.icd != "A53.0":
            raise SafetyError("Nhóm tiềm ẩn trong V1 dùng ICD A53.0.")
        if not self.icd.strip():
            raise SafetyError("Bác sĩ phải chọn ICD cho nhóm giang mai sớm.")


@dataclass(frozen=True)
class Vitals:
    measured_at: datetime
    pulse: float
    systolic: float
    diastolic: float
    temperature: float
    respiration: float
    spo2: float
    weight: float
    height: float

    def validate(self):
        if self.measured_at.tzinfo is None:
            raise SafetyError("Thời điểm đo phải có múi giờ.")
        for name, value in asdict(self).items():
            if name != "measured_at" and (not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0):
                raise SafetyError(f"Số đo không hợp lệ: {name}")
        if self.spo2 > 100 or self.systolic <= self.diastolic:
            raise SafetyError("Kiểm tra SpO₂ và huyết áp.")

    def warnings(self):
        # Data review thresholds only; never diagnostic or treatment decisions.
        bounds = {"pulse": (40, 150), "systolic": (80, 200), "diastolic": (40, 120),
                  "temperature": (35, 40), "respiration": (8, 35), "spo2": (90, 100),
                  "weight": (20, 250), "height": (80, 230)}
        return [name for name, (lo, hi) in bounds.items() if not lo <= getattr(self, name) <= hi]


@dataclass(frozen=True)
class Medication:
    catalog_id: str
    name: str
    quantity: int
    route: str
    use_at: datetime
    free: bool = False
    strength: str = ""
    total_dose: str = ""

    def validate(self):
        if not self.catalog_id or not self.name or type(self.quantity) is not int or self.quantity <= 0:
            raise SafetyError("Thiếu tên, mã danh mục hoặc sai số lượng.")
        if not self.route.strip() or self.use_at.tzinfo is None:
            raise SafetyError("Thiếu cách dùng / thời điểm sử dụng.")


@dataclass(frozen=True)
class TreatmentSheet:
    number: int
    at: datetime
    kind: str
    clinical: ClinicalTemplate
    vitals: Vitals
    medications: tuple[Medication, ...] = ()


@dataclass(frozen=True)
class Dossier:
    context: PatientContext
    sheets: tuple[TreatmentSheet, ...]
    services: tuple[str, ...] = ()
    injection: int | None = None
    discharge: str = ""
    requisition_sources: tuple[tuple[tuple[str, str], ...], ...] = ()

    @property
    def fingerprint(self):
        return digest(self)


def digest(value):
    return hashlib.sha256(json.dumps(asdict(value), ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()


def validate_requisition_sources(medications, requisition_sources):
    totals = {}
    for medication in medications:
        totals[medication.catalog_id] = totals.get(medication.catalog_id, 0) + medication.quantity
    if not totals:
        if requisition_sources:
            raise SafetyError("Không có thuốc trong hồ sơ; không thể tạo phiếu lĩnh dược.")
        return ()
    if len(requisition_sources) != 3:
        raise SafetyError("Nhập đủ số lượng theo y lệnh, tổng hợp và phiếu lĩnh trước khi chạy workflow.")
    try:
        sources = tuple({str(code): Decimal(str(quantity)) for code, quantity in source.items()}
                        for source in requisition_sources)
    except (AttributeError, TypeError, ValueError, ArithmeticError):
        raise SafetyError("Ba nguồn số lượng lĩnh phải là các mã TEST và số lượng hợp lệ.") from None
    reconcile_quantities(*sources)
    expected = {code: Decimal(quantity) for code, quantity in totals.items()}
    if sources[0] != expected:
        raise SafetyError("Số lượng đối chiếu không khớp toa đã duyệt.")
    return tuple(tuple(sorted((code, str(quantity)) for code, quantity in source.items()))
                 for source in sources)


def prepare_dossier(context, clinical, vitals, at, free=(), external=(), services=(), injection=None,
                    history_confirmed=False, third_reviewed=False, abnormal_reviewed=False, discharge="",
                    medication_reviewed=False, requisition_sources=()):
    context.validate()
    clinical.validate()
    vitals.validate()
    if at.tzinfo is None:
        raise SafetyError("Thời gian tờ điều trị phải có múi giờ.")
    if vitals.measured_at > at:
        raise SafetyError("Thời điểm đo không thể sau tờ đầu.")
    if vitals.warnings() and not abnormal_reviewed:
        raise SafetyError("Số đo bất thường cần bác sĩ kiểm tra.")
    if not third_reviewed:
        raise SafetyError("Cần xác nhận nội dung và lần đo gốc phù hợp với tờ 3.")
    if clinical.group == Group.LATENT and (injection not in (1, 2, 3) or not history_confirmed):
        raise SafetyError("Xác nhận lịch sử điều trị và chọn mũi 1–3.")
    if clinical.group == Group.EARLY and injection is not None:
        raise SafetyError("Nhóm sớm không tự xác định lần tiêm.")
    if (free or external) and not medication_reviewed:
        raise SafetyError("Bác sĩ phải duyệt tên, hàm lượng, tổng liều, đường dùng, thời gian, dị ứng và yếu tố an toàn.")
    for items, expected_free in ((free, True), (external, False)):
        ids = []
        for item in items:
            item.validate()
            if not item.strength.strip() or not item.total_dose.strip() or "CHƯA DUYỆT" in item.total_dose:
                raise SafetyError("Chưa xác nhận hàm lượng / quy cách và tổng liều.")
            if item.free != expected_free:
                raise SafetyError("Không trộn toa miễn phí và toa mua ngoài.")
            ids.append(item.catalog_id)
        if len(ids) != len(set(ids)):
            raise SafetyError("Trùng mặt hàng trong toa.")
    if len(services) != len(set(services)):
        raise SafetyError("Trùng dịch vụ.")
    normalized_sources = validate_requisition_sources(tuple(free) + tuple(external), requisition_sources)
    sheets = (TreatmentSheet(1, at, "Cấp thuốc", clinical, vitals, tuple(free)),
              TreatmentSheet(2, at, "Mua ngoài", clinical, vitals, tuple(external)),
              TreatmentSheet(3, at + timedelta(minutes=30), "Không thuốc", clinical, vitals))
    return Dossier(context, sheets, tuple(services), injection, discharge, normalized_sources)


def reconcile_quantities(approved, aggregated, requested):
    if not approved or approved != aggregated or approved != requested:
        raise SafetyError("Sai lệch y lệnh / tổng hợp / phiếu lĩnh. Cần kiểm tra, không tự sửa.")
    try:
        invalid = any(not Decimal(str(q)).is_finite() or Decimal(str(q)) <= 0
                      for source in (approved, aggregated, requested) for q in source.values())
    except (ArithmeticError, ValueError):
        raise SafetyError("Số lượng lĩnh không hợp lệ.") from None
    if invalid:
        raise SafetyError("Số lượng lĩnh không hợp lệ.")
    return True
