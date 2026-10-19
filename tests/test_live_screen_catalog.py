"""Pure read-only screen classification tests use no patient identifiers."""
from his_auto.live_screen_catalog import (
    SCREEN_HINTS, classify_static_screen, is_reference_only, title_module,
)


def test_five_known_modules_have_unique_keys():
    assert {x.key for x in SCREEN_HINTS} == {
        "inpatient_record", "admission_exam_reference", "service_registration",
        "treatment_sheet", "pharmacy_requisition",
    }


def test_recognize_ba_only_with_screen_anchors():
    title = "HIS: Quản Lý Tổng Thể Bệnh Viện [BA Nội trú - Ngoại Trú]"
    assert title_module(title) == "inpatient_record"
    assert classify_static_screen(
        "eHospital.exe", title,
        ["Chẩn đoán", "Tổng kết Bệnh án", "Hành chính, quản lý người bệnh"],
    ) == "inpatient_record"
    assert classify_static_screen("eHospital.exe", title, ["Chẩn đoán"]) is None


def test_do_not_accept_other_process_or_unknown_window():
    labels = ["Nhóm dịch vụ", "Mã dịch vụ", "Xác nhận ký"]
    title = "HIS: Quản Lý Tổng Thể Bệnh Viện [Đăng Ký Dịch Vụ]"
    assert classify_static_screen("unknown.exe", title, labels) is None
    assert classify_static_screen("eHospital.exe", "Ứng dụng lạ", labels) is None
    assert classify_static_screen("eHospital.exe", title, ["Chẩn đoán", "Lưu"]) is None


def test_five_module_examples():
    cases = [
        ("Phiếu Khám Bệnh Vào Viện", ["Thông tin chung", "Lý do vào viện"], "admission_exam_reference"),
        ("Đăng Ký Dịch Vụ", ["Nhóm dịch vụ", "Mã dịch vụ"], "service_registration"),
        ("Phiếu theo dõi điều trị", ["Mua ngoài", "Cấp thuốc"], "treatment_sheet"),
        ("Phiếu Lĩnh Dược", ["Nơi lập phiếu", "Tổng Hợp Y Lệnh"], "pharmacy_requisition"),
    ]
    for module, anchors, expected in cases:
        title = "HIS: Quản Lý Tổng Thể Bệnh Viện [" + module + "]"
        assert classify_static_screen("eHospital.exe", title, anchors) == expected


def test_admission_exam_is_read_only_reference():
    assert is_reference_only("admission_exam_reference")
    assert not is_reference_only("inpatient_record")
    assert not is_reference_only(None)


def test_unverified_anchors_never_classify_screen():
    assert classify_static_screen(
        "eHospital.exe",
        "HIS [Phiếu theo dõi điều trị]",
        ["Thông tin nhạy cảm", "Dữ liệu bệnh nhân"],
    ) is None
    assert title_module("BA Nội trú - Ngoại Trú") is None
