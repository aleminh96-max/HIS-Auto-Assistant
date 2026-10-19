"""Conservative, read-only eHospital screen classification based on static UI labels.

SCREENSHOT_REVIEWED, NOT LIVE VERIFIED. Do not use a match here as proof of
patient/encounter/department identity, permission, or authorization to write.
Never log or persist raw captions or any patient text.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


@dataclass(frozen=True)
class ScreenHint:
    key: str
    titles: tuple[str, ...]
    static_anchors: tuple[str, ...]
    reference_only: bool = False


SCREEN_HINTS = (
    ScreenHint(
        "inpatient_record",
        ("BA Nội trú - Ngoại Trú",),
        ("Hành chính, quản lý người bệnh", "Chẩn đoán", "Tổng kết Bệnh án",
         "Thông Tin Bệnh Án", "Thông Tin Khám Bệnh"),
    ),
    ScreenHint(
        "admission_exam_reference",
        ("Phiếu Khám Bệnh Vào Viện",),
        ("Thông tin chung", "Khám bệnh", "Lý do vào viện"),
        reference_only=True,
    ),
    ScreenHint(
        "service_registration",
        ("Đăng Ký Dịch Vụ",),
        ("Nhóm dịch vụ", "Mã dịch vụ", "Nơi yêu cầu", "Chọn In", "Xác nhận ký"),
    ),
    ScreenHint(
        "treatment_sheet",
        ("Phiếu theo dõi điều trị",),
        ("S (Hỏi bệnh)", "O.1 (Khám bệnh)", "O.3 (Kết quả xét nghiệm, CLS)",
         "A (Đánh giá - chẩn đoán)", "P (Kế hoạch điều trị)",
         "Mua ngoài", "Cấp thuốc", "In phiếu công khai thuốc",
         "In phiếu theo dõi điều trị"),
    ),
    ScreenHint(
        "pharmacy_requisition",
        ("Phiếu Lĩnh Dược",),
        ("Nơi lập phiếu", "Nơi sẽ giao", "Tổng Hợp Y Lệnh",
         "Loại phiếu lĩnh", "Nguồn dược"),
    ),
)


def _norm(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())


def title_module(raw_title: str) -> str | None:
    """Return only an allowlisted module, never raw title or arbitrary text."""
    if not isinstance(raw_title, str):
        return None
    match = re.search(r"\[([^\[\]]+)\]\s*$", raw_title)
    if not match:
        return None
    module = _norm(match.group(1))
    for spec in SCREEN_HINTS:
        if any(module == _norm(title) for title in spec.titles):
            return spec.key
    return None


def classify_static_screen(
    process_name: str,
    window_title: str,
    visible_static_labels: tuple[str, ...] | list[str],
    minimum_anchors: int = 2,
) -> str | None:
    """Return a cautious page hint, **never** an approval or a write permission.

    The caller must independently verify patient, encounter, department and
    authorization before performing any workflow side effect.
    """
    if _norm(process_name) != "ehospital.exe" or minimum_anchors < 2:
        return None
    module = title_module(window_title)
    if not module:
        return None
    spec = next(item for item in SCREEN_HINTS if item.key == module)
    available = {_norm(label) for label in visible_static_labels if isinstance(label, str)}
    evidence = {_norm(label) for label in spec.static_anchors} & available
    if len(evidence) < minimum_anchors:
        return None
    return module


def is_reference_only(module: str | None) -> bool:
    return any(spec.key == module and spec.reference_only for spec in SCREEN_HINTS)
